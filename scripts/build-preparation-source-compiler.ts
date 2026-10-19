// SPDX-License-Identifier: MIT OR Apache-2.0
/** Package the original committed host-only source compiler, without rewriting it. */
import {mkdtemp,writeFile,readFile,symlink,mkdir,copyFile,readdir} from 'node:fs/promises';
const repository=process.argv[2];if(!repository?.startsWith('/'))throw Error('Absolute UMF Git repository required');
const revision='98ee88f193f5d70ccf21bd78ef6c37fffddc5eab';
const entry='tools/security/protection-preparation-sources.ts';
const output=await mkdtemp('/private/tmp/truss-preparation-source-compiler-');
const archive=Bun.spawnSync(['git','archive',revision],{cwd:repository});
if(archive.exitCode)throw Error('Committed source compiler archive required');
await writeFile(output+'/source.tar',archive.stdout);
if(Bun.spawnSync(['tar','-xf',output+'/source.tar','-C',output]).exitCode)throw Error('Source extraction failed');
await symlink(repository+'/node_modules',output+'/node_modules');
const root='packages/python/src/truss/_preparation_sources';await mkdir(root+'/licenses',{recursive:true});
const built=await Bun.build({entrypoints:[output+'/'+entry],outdir:root,target:'bun',format:'esm',naming:'producer.js'});
if(!built.success)throw Error('Original source compiler build failed: '+built.logs.join('\n'));
for(const name of await readdir('packages/python/src/truss/_umf/licenses'))
 await copyFile('packages/python/src/truss/_umf/licenses/'+name,root+'/licenses/'+name);
const hash=(b:Uint8Array)=>new Bun.CryptoHasher('sha256').update(b).digest('hex');
const files=['producer.js',...(await readdir(root+'/licenses')).map(name=>'licenses/'+name)];
const manifest={revision,entry,runtime:'Bun',runtimeVersion:Bun.version,
 archiveSha256:hash(archive.stdout),entrySha256:hash(await readFile(output+'/'+entry)),
 files:Object.fromEntries(await Promise.all(files.map(async p=>[p,hash(await readFile(root+'/'+p))]))),
 scope:'Original host-only UMF source obligations; no authority, native provenance or SQL execution'};
await writeFile(root+'/manifest.json',JSON.stringify(manifest,null,2)+'\n');
await writeFile('packages/python/src/truss/_preparation_sources_release.py',
 '"""Generated original private source compiler pin; no authority."""\nMANIFEST_SHA256 = '+JSON.stringify(hash(await readFile(root+'/manifest.json')))+'\n');
console.log(JSON.stringify({revision,bundleSha256:manifest.files['producer.js'],manifestSha256:hash(await readFile(root+'/manifest.json'))}));
