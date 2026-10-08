/** Host package build; portable package must be built first. */
import {resolve} from 'node:path';
import {mkdir,readFile,writeFile,rm} from 'node:fs/promises';
const root=resolve(import.meta.dir,'..');const pkg=resolve(root,'packages/pg-runtime');const dist=resolve(pkg,'dist');
await rm(dist,{recursive:true,force:true});await mkdir(dist,{recursive:true});
const result=Bun.spawnSync([process.execPath,resolve(root,'node_modules/typescript/bin/tsc'),'--strict','--declaration','--emitDeclarationOnly','--target','ES2022','--module','ESNext','--moduleResolution','Bundler','--outDir',dist,resolve(pkg,'src/index.ts')],{cwd:root});
if(result.exitCode)throw Error(new TextDecoder().decode(result.stdout)+new TextDecoder().decode(result.stderr));
const build=await Bun.build({entrypoints:[resolve(pkg,'src/index.ts')],outdir:dist,target:'bun',format:'esm',external:['pg']});
if(!build.success)throw Error('Host build failed');
const declaration=await readFile(resolve(dist,'index.d.ts'),'utf8');
if(declaration.includes('../')||declaration.includes('/Users/')||!declaration.includes('@documentdrivendx/truss-postgresql'))throw Error('Private public declaration path');
const hash=(text:string)=>new Bun.CryptoHasher('sha256').update(text).digest('hex');
await writeFile(resolve(dist,'build-evidence.json'),JSON.stringify({compiler:'typescript/7.0.2',loader:'bun/'+Bun.version,driver:'pg/8.16.3',jsSha256:hash(await readFile(resolve(dist,'index.js'),'utf8')),declarationsSha256:hash(declaration),qualification:'Built host package; exact canonical public Truss type imports. No release, Node/pooler, native bootstrap or complete executor support.'},null,2)+'\n');
console.log('Built host PostgreSQL package against canonical public Truss types.');
