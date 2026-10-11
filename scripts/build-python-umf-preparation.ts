/** Rebuild packaged Python ingress from committed UMF and original Truss sources. */
import {mkdir,readFile,writeFile,copyFile} from 'node:fs/promises';
import {resolve} from 'node:path';
const repository=process.argv[2];if(!repository)throw Error('UMF repository required');
const base=resolve('packages/python/src/truss/_umf');
const hash=(b:Uint8Array)=>new Bun.CryptoHasher('sha256').update(b).digest('hex');
const bridgeOnly=process.argv[3]==='--bridge-only';
if(bridgeOnly){
 const previous=await readFile(base+'/manifest.json');
 const release=await readFile('packages/python/src/truss/_umf_release.py','utf8');
 const pin=/MANIFEST_SHA256 = "([0-9a-f]{64})"/.exec(release)?.[1];
 if(!pin||hash(previous)!==pin)throw Error('Original packaged release manifest required');
 for(const [path,digest] of Object.entries(JSON.parse(previous.toString()).files))
  if(hash(await readFile(base+'/'+path))!==digest)throw Error('Original packaged owner/runtime asset drift');
}
if(!bridgeOnly){
const built=Bun.spawnSync(['bun','scripts/build-umf-runtime.ts',repository,'record']);
if(built.exitCode!==0)throw Error('Original UMF build failed');
const owner=Buffer.from(built.stdout).toString().trim();
await mkdir(base+'/owner',{recursive:true});await mkdir(base+'/runtime/node_modules/ajv/dist',{recursive:true});
await mkdir(base+'/packages/umf-bun/src',{recursive:true});await mkdir(base+'/docs/helix/02-design/contracts',{recursive:true});
for(const name of ['producer.js','producer-manifest.json'])await copyFile(owner+'/'+name,base+'/owner/'+name);
await copyFile('docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json',base+'/docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json');
await writeFile(base+'/runtime/package.json',JSON.stringify({name:'truss-preparation-runtime',private:true,type:'commonjs'})+'\n');
const ajv=await Bun.build({entrypoints:[resolve(repository,'node_modules/ajv/dist/2020.js')],target:'bun',format:'cjs',outdir:base+'/runtime/node_modules/ajv/dist',naming:'2020.js'});
if(!ajv.success)throw Error('Original Ajv bundle failed');
}
const bridge=await Bun.build({entrypoints:['packages/umf-bun/src/python-preparation.ts'],target:'bun',format:'esm',outdir:base+'/packages/umf-bun/src',naming:'bridge.js'});
if(!bridge.success)throw Error('Python preparation bridge build failed');
const notices:string[]=[];
await mkdir(base+'/licenses',{recursive:true});
for(const name of ['ajv','yaml','fast-uri','fast-deep-equal','json-schema-traverse','require-from-string']){
 const source=resolve(repository,'node_modules',name,name==='require-from-string'?'license':'LICENSE');
 const target='licenses/'+name+'.txt';if(!bridgeOnly)await copyFile(source,base+'/'+target);notices.push(target);
}
const paths=[...notices,'owner/producer.js','owner/producer-manifest.json','runtime/package.json','runtime/node_modules/ajv/dist/2020.js','packages/umf-bun/src/bridge.js','docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json'];

const manifest={interfaceVersion:'truss-python-umf-preparation/0.1.0',runtime:'Bun',runtimeVersion:Bun.version,files:Object.fromEntries(await Promise.all(paths.map(async p=>[p,hash(await readFile(base+'/'+p))]))),owner:JSON.parse(await readFile(base+'/owner/producer-manifest.json','utf8')),
 sources:Object.fromEntries(await Promise.all(['scripts/build-python-umf-preparation.ts','scripts/build-umf-runtime.ts','packages/umf-bun/src/python-preparation.ts','packages/umf-bun/src/catalog-input.ts','packages/umf-bun/src/catalog-declarations.ts','packages/umf-bun/src/catalog-transition-correspondence.ts','packages/umf-bun/src/catalog-validation-evidence.ts','packages/umf-bun/src/catalog-extension-artifacts.ts','packages/umf-bun/src/catalog-extension-inventory.ts','packages/umf-bun/src/catalog-ingress-report-basis.ts','packages/umf-bun/src/index.ts','packages/umf-bun/src/acceptance-input.ts','packages/postgresql/src/acceptance-json.ts'].map(async p=>[p,hash(await readFile(p))])))};
await writeFile(base+'/manifest.json',JSON.stringify(manifest,null,2)+'\n');
await writeFile('packages/python/src/truss/_umf_release.py','"""Generated exact packaged preparation release pins; no acceptance authority."""\nMANIFEST_SHA256 = '+JSON.stringify(hash(await readFile(base+'/manifest.json')))+'\n');
console.log(JSON.stringify({base,manifestSha256:hash(await readFile(base+'/manifest.json')),ownerBundleSha256:manifest.owner.bundleSha256}));
