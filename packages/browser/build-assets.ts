// SPDX-License-Identifier: MIT OR Apache-2.0
/** Host-only reproducible packaging. The provider itself contains no Bun/Node API. */
import {mkdir,cp,readFile,readdir,writeFile} from 'node:fs/promises';
import {join,resolve,isAbsolute} from 'node:path';
const root=resolve(import.meta.dir,'../..');
const hash=(bytes:Uint8Array|string)=>new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
const inputs=['packages/browser/key-receipt-storage.ts','packages/browser/store.ts','packages/browser/catalog.ts','packages/browser/actions.ts','packages/browser/materialize.ts','packages/browser/objects.ts','packages/browser/bulk.ts','packages/browser/batch.ts','packages/browser/feed.ts','packages/browser/build-assets.ts','packages/browser/package.json','bun.lock',
  'packages/postgresql/src/acceptance-json.ts','packages/postgresql/src/original-byte-custody.ts',
  'packages/umf-bun/src/catalog-declarations.ts',
  ...['layout.sql','scalars.sql','lineage.sql','containers.sql','plan.sql'].map(x=>'packages/python/src/truss/_catalog_runtime/'+x),
  'packages/python/src/truss/_umf_core08/producer.js','packages/python/src/truss/_umf_core08/producer-manifest.json'];
export async function buildBrowserAssets(directory:string){
  if(Bun.version!=='1.4.2'||!isAbsolute(directory))throw Error('Bun1.4.2 and a fresh absolute output directory required');
  const ownerDirectory='packages/browser/owners/umf-local-actions';
  const ownerInputs:string[]=[];
  async function ownerFiles(relative:string){for(const entry of await readdir(join(root,relative),{withFileTypes:true})){
    const file=relative+'/'+entry.name;if(entry.isDirectory())await ownerFiles(file);else if(entry.isFile())ownerInputs.push(file);else throw Error('Regular original owner files required');
  }}
  await ownerFiles('packages/browser/owners');ownerInputs.sort();const allInputs=[...inputs,...ownerInputs];
  const sourceHashes:Record<string,string>={};
  for(const file of allInputs)sourceHashes[file]=hash(await readFile(join(root,file)));
  if(sourceHashes[ownerDirectory+'/notices/inventory.json']!=='dd26874ed53f10d5f697474c5ca260d7fca06b2413fb097530384f8f86d2b7aa')throw Error('Original action owner notice inventory required');
  const notices=JSON.parse(await readFile(join(root,ownerDirectory,'notices/inventory.json'),'utf8'));
  for(const dependency of notices.packages)for(const notice of dependency.notices){
    if(sourceHashes[ownerDirectory+'/notices/'+notice.path]!==notice.sha256)throw Error('Original action owner notice bytes required');
  }
  if(sourceHashes['packages/python/src/truss/_umf_core08/producer.js']!=='88899e3c1221ca3998e80a878d37d5344d68062afa82eb15d6cffc49dd3752f3')throw Error('Original UMF core0.8 producer required');
  const dependency=join(root,'packages/browser/node_modules/@electric-sql/pglite');
  if(JSON.parse(await readFile(join(dependency,'package.json'),'utf8')).version!=='0.5.10')throw Error('Pinned PGlite required');
  const build=await Bun.build({root,entrypoints:[join(root,'packages/browser/store.ts')],target:'browser',format:'esm',minify:{whitespace:true},
    plugins:[{name:'original-pglite',setup(b){b.onResolve({filter:/^@electric-sql\/pglite$/},()=>({path:'./pglite/index.js',external:true}));b.onResolve({filter:/^@truss\/umf-local-actions$/},()=>({path:'./owners/umf-actions.js',external:true}));b.onResolve({filter:/^@truss\/weft-local$/},()=>({path:'./owners/weft/weft_wasm.js',external:true}));}}]});
  if(!build.success||build.outputs.length!==1)throw Error(String(build.logs));
  await mkdir(directory); // Existing output is never overwritten.
  await writeFile(join(directory,'store.js'),await build.outputs[0]!.text());
  await cp(join(dependency,'dist'),join(directory,'pglite'),{recursive:true});
  await mkdir(join(directory,'licenses'),{recursive:true});
  await cp(join(dependency,'LICENSE'),join(directory,'licenses/pglite-LICENSE'));
  await cp(join(root,'packages/python/src/truss/_umf_core08/licenses'),join(directory,'licenses/umf'),{recursive:true});
  await cp(join(root,'packages/python/src/truss/_catalog_runtime/layout.sql'),join(directory,'layout.sql'));
  const originalOwner=Bun.gunzipSync(await readFile(join(root,ownerDirectory,'umf.js.gz')));
  if(hash(originalOwner)!=='86fd188e12b2c796c41f10d4f26a9b8aaa12323d148722fa034d05ec062a43a3')throw Error('Pinned original UMF local action ESM required');
  await mkdir(join(directory,'owners'));await writeFile(join(directory,'owners/umf-actions.js'),originalOwner);
  await cp(join(root,ownerDirectory,'notices'),join(directory,'licenses/umf-local-actions'),{recursive:true});
  const weftDirectory='packages/browser/owners/weft-local';
  const weftProducer=JSON.parse(await readFile(join(root,weftDirectory,'producer.json'),'utf8'));
  if(weftProducer.assets['weft_wasm.js'].sha256!=='2711256b057a90fa8a898f1d616b871a083f993177b6bbffcd6cbd17fcaa6119'||weftProducer.revision!=='ab94595f176cc67ed213843285dda4d401033959'||weftProducer.assets['weft_wasm_bg.wasm'].sha256!=='4434aad3ba9ce064f37f21146943a74d18b26d20c9caa255bdd5e56f503b2fd2')throw Error('Original local Weft producer required');
  await mkdir(join(directory,'owners/weft'));
  for(const name of ['weft_wasm.js','weft_wasm_bg.wasm']){
    const bytes=Bun.gunzipSync(await readFile(join(root,weftDirectory,name+'.gz')));
    if(hash(bytes)!==weftProducer.assets[name].sha256)throw Error('Original local Weft asset required');
    await writeFile(join(directory,'owners/weft',name),bytes);
  }
  await mkdir(join(directory,'licenses/weft-local'));
  for(const name of ['ahash-LICENSE-MIT','ahash-LICENSE-APACHE','producer.json'])await cp(join(root,weftDirectory,name),join(directory,'licenses/weft-local',name));
  const assets:Record<string,{sha256:string;bytes:number}>={};
  async function inventory(relative=''){
    for(const entry of await readdir(join(directory,relative),{withFileTypes:true})){
      const path=relative?relative+'/'+entry.name:entry.name;
      if(entry.isDirectory())await inventory(path);
      else if(entry.isFile()){const bytes=await readFile(join(directory,path));assets[path]={sha256:hash(bytes),bytes:bytes.length};}
      else throw Error('Regular bundle files required');
    }
  }
  await inventory();
  for(const file of allInputs){
    if(hash(await readFile(join(root,file)))!==sourceHashes[file])throw Error('Build input changed: '+file);
  }
  if(assets['layout.sql']!.sha256!==sourceHashes['packages/python/src/truss/_catalog_runtime/layout.sql'])throw Error('Emitted layout differs from captured input');
  const manifest={interfaceVersion:'truss-browser-assets/0.1',bun:Bun.version,pglite:'0.5.10',
    umfCoreProducer:{revision:'7c0f0c98beee2cc1a5a407992b5c53cc2616da8e',bundleSha256:sourceHashes['packages/python/src/truss/_umf_core08/producer.js']},
    umfActionsProducer:{revision:'c1e316c42ebe2a3a87420a5edc7e1ae751137b5b',producer:'sha256:6b331c0b5118435a79eb19b3c66464b4ea1ed3e70134fc3b71e07913487a408b',bundleSha256:assets['owners/umf-actions.js']!.sha256},
    weftProducer:{revision:weftProducer.revision,features:weftProducer.features,wasmSha256:assets['owners/weft/weft_wasm_bg.wasm']!.sha256},
    scope:{lifecycle:true,coreCatalog:true,actionRegistration:true,selectionReadGrant:true,materialization:true,manifestSealing:true,sealRecovery:true,objectLoad:true,objectRead:true,objectReadPage:true,loadRecovery:true,submission:true,submissionRecovery:true,jobReview:true,claims:true,claimRecovery:true,actionExecution:true,batchRecovery:true,journalPages:true,effects:true},
    sourceHashes,assets:Object.fromEntries(Object.entries(assets).sort(([a],[b])=>a<b?-1:a>b?1:0))};
  const encoded=JSON.stringify(manifest,null,2)+'\n';await writeFile(join(directory,'manifest.json'),encoded);
  return {directory,manifestSha256:hash(encoded),providerSha256:assets['store.js']!.sha256};
}
if(import.meta.main){if(!Bun.argv[2])throw Error('Fresh absolute output directory required');console.log(JSON.stringify(await buildBrowserAssets(Bun.argv[2]),null,2));}
