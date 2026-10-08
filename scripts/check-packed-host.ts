/** Separate consumer receives packed artifacts only; no source links or database I/O. */
import {mkdtemp,mkdir,readFile,writeFile,cp,readdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve,join} from 'node:path';
const root=resolve(import.meta.dir,'..');const temporary=await mkdtemp(join(tmpdir(),'truss-host-packed-'));
const run=(args:string[],cwd:string)=>{const r=Bun.spawnSync(args,{cwd});if(r.exitCode)throw Error(new TextDecoder().decode(r.stdout)+new TextDecoder().decode(r.stderr));return new TextDecoder().decode(r.stdout);};
const names=['postgresql','pg-runtime'];const archives:Record<string,string>={};
const hash=(data:string|Uint8Array)=>new Bun.CryptoHasher('sha256').update(data).digest('hex');
const evidence:Record<string,unknown>={loader:'bun/'+Bun.version,sourceManifestHashes:{},archiveHashes:{}};
for(const name of names){
 const source=resolve(root,'packages',name),staging=resolve(temporary,'staging',name,'package');await mkdir(staging,{recursive:true});
 const original=await readFile(resolve(source,'package.json'),'utf8');const manifest=JSON.parse(original);
 if(name==='pg-runtime')manifest.dependencies['@documentdrivendx/truss-postgresql']='0.0.0-experimental.1';
 await writeFile(resolve(staging,'package.json'),JSON.stringify(manifest,null,2)+'\n');await cp(resolve(source,'dist'),resolve(staging,'dist'),{recursive:true});
 const archive=resolve(temporary,name+'.tgz');run(['/usr/bin/tar','-czf',archive,'-C',resolve(staging,'..'),'package'],root);
 archives[manifest.name]='file:'+archive;
 (evidence.sourceManifestHashes as any)[name]=hash(original);(evidence.archiveHashes as any)[name]=hash(await readFile(archive));
}
const consumer=resolve(temporary,'consumer');await mkdir(consumer);
await writeFile(resolve(consumer,'package.json'),JSON.stringify({private:true,type:'module',dependencies:archives,overrides:{'@documentdrivendx/truss-postgresql':archives['@documentdrivendx/truss-postgresql']},devDependencies:{typescript:'7.0.2'}},null,2)+'\n');
run([process.execPath,'install','--ignore-scripts'],consumer);
const code=`import {createPgConnectionSource} from '@documentdrivendx/truss-pg-runtime';
import {createEngineExecutor} from '@documentdrivendx/truss-postgresql';
import type {NativeConnectionSource,TransactionHandle} from '@documentdrivendx/truss-postgresql';
const host=createPgConnectionSource({host:'127.0.0.1',port:1,user:'unused',database:'unused',max:1});
const source:NativeConnectionSource=host.source;
const executor=createEngineExecutor(source);
// Exact public handle relation compiles without a brand-repair assertion.
const typed=(handle:TransactionHandle)=>executor.execute(handle,{sql:'SELECT 1',parameters:[]});
if(typeof typed!=='function'||host.quarantinedCount()!==0)throw Error('Public construction failed');
await host.close();
console.log('Packed host construction closes without acquiring a connection.');
`;
await writeFile(resolve(consumer,'consumer.ts'),code);
const compiler=resolve(consumer,'node_modules/typescript/bin/tsc');
const flags=[process.execPath,compiler,'--strict','--noEmit','--target','ES2022','--module','ESNext','--moduleResolution','Bundler','--lib','ES2022,DOM'];
run([...flags,'consumer.ts'],consumer);const output=run([process.execPath,'consumer.ts'],consumer);
const libraryRoot=resolve(consumer,'node_modules/@documentdrivendx/truss-postgresql/dist/contracts');
let brands=0;for(const file of await readdir(libraryRoot))brands+=(await readFile(resolve(libraryRoot,file),'utf8')).match(/declare const transactionBrand: unique symbol/g)?.length??0;
if(brands!==1)throw Error('Canonical transaction brand split');
evidence.cleanConsumerTypecheck=true;evidence.cleanConsumerRuntime=true;evidence.transactionBrandDeclarations=brands;evidence.output=output;
evidence.consumerLockSha256=hash(await readFile(resolve(consumer,'bun.lock')));
evidence.manifestTransformation='Only staged host workspace:* dependency becomes exact portable package version; both original manifests unchanged. Root consumer selects the two actual local archives.';
evidence.qualification='Clean external packed ESM host/portable consumer under Bun 1.4.2; no repository source paths, no connection acquisition, no native I/O. No release, Node/pooler, adoption/cancellation or full bootstrap qualification.';
await writeFile(resolve(root,'docs/helix/04-build/evidence/inert-assembly/packed-host-check.json'),JSON.stringify(evidence,null,2)+'\n');
await writeFile(resolve(root,'docs/helix/04-build/evidence/inert-assembly/packed-host-consumer.ts'),code);
console.log('Packed host/portable consumer typecheck/runtime passed; one canonical brand.');
