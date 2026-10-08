/** Host-only compiler/packaging; libraries contain no driver or tooling import. */
import {resolve, dirname, basename} from 'node:path';
import {mkdir, readFile, writeFile, rm} from 'node:fs/promises';
const root = resolve(import.meta.dir, '..');
const arg = process.argv.indexOf('--tsc');
const compiler = arg >= 0 ? process.argv[arg + 1] : Bun.resolveSync('typescript/bin/tsc', root);
if (!compiler) throw Error('Explicit installed TypeScript compiler required');
const version = Bun.spawnSync([process.execPath, compiler, '--version'], {cwd: root});
if (version.exitCode !== 0 || new TextDecoder().decode(version.stdout).trim() !== 'Version 7.0.2') throw Error('Expected TypeScript 7.0.2');
const pkg = resolve(root, 'packages/postgresql');
const dist = resolve(pkg, 'dist');
await rm(dist, {recursive: true, force: true});
await mkdir(resolve(dist, 'contracts'), {recursive: true});
const declarations = Bun.spawnSync([process.execPath, compiler, '--strict', '--declaration', '--emitDeclarationOnly',
  '--target', 'ES2022', '--module', 'ESNext', '--moduleResolution', 'Bundler', '--lib', 'ES2022,DOM',
  '--outDir', dist, resolve(pkg, 'src/index.ts')], {cwd: root});
if (declarations.exitCode !== 0) throw Error(new TextDecoder().decode(declarations.stdout) + new TextDecoder().decode(declarations.stderr));
const runtime = await Bun.build({entrypoints: [resolve(pkg, 'src/index.ts')], outdir: dist, target: 'browser', format: 'esm'});
if (!runtime.success) throw Error(runtime.logs.join('\n'));
const publicDeclarations = await readFile(resolve(dist, 'index.d.ts'), 'utf8');
const bindingRoot = resolve(root, 'docs/helix/02-design/contracts/bindings');
const pending = [...publicDeclarations.matchAll(/(?:from\s*|import\()(['"])([^'"]+)\1/g)].map(match => resolve(pkg, 'src', match[2] + '.d.ts'));
const copied = new Map<string, string>();
while (pending.length) {
  const path = pending.pop()!;
  if (dirname(path) !== bindingRoot) throw Error('Public declaration outside owning binding closure: ' + path);
  if (copied.has(path)) continue;
  const text = await readFile(path, 'utf8');
  copied.set(path, text);
  for (const match of text.matchAll(/(?:from\s*|import\()(['"])([^'"]+)\1/g)) {
    if (!match[2].startsWith('./')) throw Error('Unselected declaration dependency: ' + match[2]);
    pending.push(resolve(dirname(path), match[2] + '.d.ts'));
  }
  await writeFile(resolve(dist, 'contracts', basename(path)), text);
}
const rewritten = publicDeclarations.replaceAll('../../../docs/helix/02-design/contracts/bindings/', './contracts/');
if (rewritten.includes('../') || rewritten.includes('/Users/') || rewritten.includes('/private/')) throw Error('Private public declaration path');
await writeFile(resolve(dist, 'index.d.ts'), rewritten);
const js = await readFile(resolve(dist, 'index.js'), 'utf8');
if (/\b(?:import|require)\s*\(/.test(js) || /from\s*['"](?:node:|bun|.*adapter|.*tooling)/.test(js)
    || /\b(?:Bun|process|Date)\b/.test(js)) throw Error('Executable library has a host/runtime import or clock');
const hash = (text: string) => new Bun.CryptoHasher('sha256').update(text).digest('hex');
const profile = await readFile(resolve(pkg, 'inert-profile.json'), 'utf8');
await writeFile(resolve(dist, 'inert-profile.json'), profile);
const lib = await import(resolve(dist, 'index.js'));
if (lib.INERT_ASSEMBLY_PROFILE.sha256 !== hash(profile)) throw Error('Inert profile fingerprint mismatch');
await writeFile(resolve(dist, 'build-evidence.json'), JSON.stringify({interfaceVersion: 'truss-inert-package-build/0.1.0',
  compiler: 'typescript/7.0.2', loader: 'bun/' + Bun.version, nativeCapabilities: 'none',
  jsSha256: hash(js), declarationsSha256: hash(rewritten), bindingSourceSha256: Object.fromEntries([...copied].map(([path, text]) => [basename(path), hash(text)])),
  qualification: 'ESM runtime and complete canonical declaration closure only; no native installation, UMF interpretation, Node/browser or database support.'}, null, 2) + '\n');
console.log('Built inert PostgreSQL assembly and ' + copied.size + ' owning declaration files; no native capability.');
