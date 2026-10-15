/** Host-only reproducible packaging. The provider itself contains no Bun/Node API. */
import {mkdir,cp,readFile,readdir,writeFile} from 'node:fs/promises';
import {join,resolve,isAbsolute} from 'node:path';
const root=resolve(import.meta.dir,'../..');
const hash=(bytes:Uint8Array|string)=>new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
const inputs=['packages/browser/store.ts','packages/browser/catalog.ts','packages/browser/build-assets.ts','packages/browser/package.json','bun.lock',
  'packages/postgresql/src/acceptance-json.ts','packages/postgresql/src/original-byte-custody.ts',
  'packages/umf-bun/src/catalog-declarations.ts',
  ...['layout.sql','lineage.sql','containers.sql','plan.sql'].map(x=>'packages/python/src/truss/_catalog_runtime/'+x),
  'packages/python/src/truss/_umf_core08/producer.js','packages/python/src/truss/_umf_core08/producer-manifest.json'];
export async function buildBrowserAssets(directory:string){
  if(Bun.version!=='1.4.2'||!isAbsolute(directory))throw Error('Bun1.4.2 and a fresh absolute output directory required');
  const sourceHashes:Record<string,string>={};
  for(const file of inputs)sourceHashes[file]=hash(await readFile(join(root,file)));
  if(sourceHashes['packages/python/src/truss/_umf_core08/producer.js']!=='88899e3c1221ca3998e80a878d37d5344d68062afa82eb15d6cffc49dd3752f3')throw Error('Original UMF core0.8 producer required');
  const dependency=join(root,'packages/browser/node_modules/@electric-sql/pglite');
  if(JSON.parse(await readFile(join(dependency,'package.json'),'utf8')).version!=='0.5.10')throw Error('Pinned PGlite required');
  const build=await Bun.build({root,entrypoints:[join(root,'packages/browser/store.ts')],target:'browser',format:'esm',minify:{whitespace:true},
    plugins:[{name:'original-pglite',setup(b){b.onResolve({filter:/^@electric-sql\/pglite$/},()=>({path:'./pglite/index.js',external:true}));}}]});
  if(!build.success||build.outputs.length!==1)throw Error(String(build.logs));
  await mkdir(directory); // Existing output is never overwritten.
  await writeFile(join(directory,'store.js'),await build.outputs[0]!.text());
  await cp(join(dependency,'dist'),join(directory,'pglite'),{recursive:true});
  await mkdir(join(directory,'licenses'),{recursive:true});
  await cp(join(dependency,'LICENSE'),join(directory,'licenses/pglite-LICENSE'));
  await cp(join(root,'packages/python/src/truss/_umf_core08/licenses'),join(directory,'licenses/umf'),{recursive:true});
  await cp(join(root,'packages/python/src/truss/_catalog_runtime/layout.sql'),join(directory,'layout.sql'));
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
  for(const file of inputs){
    if(hash(await readFile(join(root,file)))!==sourceHashes[file])throw Error('Build input changed: '+file);
  }
  if(assets['layout.sql']!.sha256!==sourceHashes['packages/python/src/truss/_catalog_runtime/layout.sql'])throw Error('Emitted layout differs from captured input');
  const manifest={interfaceVersion:'truss-browser-assets/0.1',bun:Bun.version,pglite:'0.5.10',
    umfCoreProducer:{revision:'7c0f0c98beee2cc1a5a407992b5c53cc2616da8e',bundleSha256:sourceHashes['packages/python/src/truss/_umf_core08/producer.js']},
    scope:{lifecycle:true,coreCatalog:true,selectionReadGrant:false,actionExecution:false,effects:false},
    sourceHashes,assets:Object.fromEntries(Object.entries(assets).sort(([a],[b])=>a<b?-1:a>b?1:0))};
  const encoded=JSON.stringify(manifest,null,2)+'\n';await writeFile(join(directory,'manifest.json'),encoded);
  return {directory,manifestSha256:hash(encoded),providerSha256:assets['store.js']!.sha256};
}
if(import.meta.main){if(!Bun.argv[2])throw Error('Fresh absolute output directory required');console.log(JSON.stringify(await buildBrowserAssets(Bun.argv[2]),null,2));}
