/** Host-only reproducible packaging. The provider itself contains no Bun/Node API. */
import {mkdir,cp,readFile,readdir,writeFile} from 'node:fs/promises';
import {join,resolve,isAbsolute} from 'node:path';
const root=resolve(import.meta.dir,'../..');
const hash=(bytes:Uint8Array|string)=>new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
const inputs=['packages/browser/store.ts','packages/browser/catalog.ts','packages/browser/actions.ts','packages/browser/materialize.ts','packages/browser/build-assets.ts','packages/browser/package.json','bun.lock',
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
  if(sourceHashes[ownerDirectory+'/notices/inventory.json']!=='fb153552de3f60335d542bbb9123d1f29be150bab2d1a373039eda251066796b')throw Error('Original action owner notice inventory required');
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
  if(hash(originalOwner)!=='9d26a51a6fe47b63dfd830d5759e342d633bc1f68df3aefc15ac05a6c2c4653b')throw Error('Pinned original UMF local action ESM required');
  await mkdir(join(directory,'owners'));await writeFile(join(directory,'owners/umf-actions.js'),originalOwner);
  await cp(join(root,ownerDirectory,'notices'),join(directory,'licenses/umf-local-actions'),{recursive:true});
  const weftDirectory='packages/browser/owners/weft-local';
  const weftProducer=JSON.parse(await readFile(join(root,weftDirectory,'producer.json'),'utf8'));
  if(weftProducer.assets['weft_wasm.js'].sha256!=='2711256b057a90fa8a898f1d616b871a083f993177b6bbffcd6cbd17fcaa6119'||weftProducer.revision!=='4f5b73df8b751b4291b84af3b59169c1a1b63ed0'||weftProducer.assets['weft_wasm_bg.wasm'].sha256!=='e73e77d5dfbf2118a0452838f70c17ab17658caf7bca5841abc6f31a6e91f8e5')throw Error('Original local Weft producer required');
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
    umfActionsProducer:{revision:'40f011402bf8f0c9512225975b62a034f1da325c',producer:'sha256:633f8ad623cc150fd3f6e2c5fe5324a0a128393036aa34d9929bfadf1142c6e4',bundleSha256:assets['owners/umf-actions.js']!.sha256},
    weftProducer:{revision:weftProducer.revision,features:weftProducer.features,wasmSha256:assets['owners/weft/weft_wasm_bg.wasm']!.sha256},
    scope:{lifecycle:true,coreCatalog:true,actionRegistration:true,selectionReadGrant:true,materialization:true,manifestSealing:true,sealRecovery:true,actionExecution:false,effects:false},
    sourceHashes,assets:Object.fromEntries(Object.entries(assets).sort(([a],[b])=>a<b?-1:a>b?1:0))};
  const encoded=JSON.stringify(manifest,null,2)+'\n';await writeFile(join(directory,'manifest.json'),encoded);
  return {directory,manifestSha256:hash(encoded),providerSha256:assets['store.js']!.sha256};
}
if(import.meta.main){if(!Bun.argv[2])throw Error('Fresh absolute output directory required');console.log(JSON.stringify(await buildBrowserAssets(Bun.argv[2]),null,2));}
