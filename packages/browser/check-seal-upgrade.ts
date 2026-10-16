/** Real Chromium worker/IndexedDB test. Supply a package.json resolving playwright. */
import {createRequire} from 'node:module';
import {join} from 'node:path';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {buildBrowserAssets} from './build-assets';
const {chromium}=createRequire(Bun.argv[2]??import.meta.path)('playwright');
const temporary=await mkdtemp(join(tmpdir(),'truss-browser-check-'));
const packaged=await buildBrowserAssets(join(temporary,'bundle'));
const built=await Bun.build({entrypoints:[new URL('./test-worker.ts',import.meta.url).pathname],target:'browser',
  plugins:[{name:'owned-provider',setup(build){build.onResolve({filter:/^\.\/store$/},()=>({path:'./store.js',external:true}));build.onResolve({filter:/^@electric-sql\/pglite$/},()=>({path:'./pglite/index.js',external:true}));build.onResolve({filter:/^@truss\/umf-local-actions$/},()=>({path:'./owners/umf-actions.js',external:true}));build.onResolve({filter:/^@truss\/weft-local$/},()=>({path:'./owners/weft/weft_wasm.js',external:true}));}}]});
if(!built.success)throw Error(String(built.logs));
// Optional fourth argument relocates the exact retained old bundle; hashes stay fixed.
const oldDirectory=Bun.argv[4]??'/private/tmp/truss-browser-canonical-weft-site-bundle-20261016';
const digest=(bytes:Uint8Array|string)=>new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
const oldManifestUtf8=await Bun.file(join(oldDirectory,'manifest.json')).text(),oldManifest=JSON.parse(oldManifestUtf8);
const oldProvider={directory:oldDirectory,manifestSha256:digest(oldManifestUtf8),storeSha256:digest(await Bun.file(join(oldDirectory,'store.js')).bytes()),assetsVerified:0};
if(oldProvider.manifestSha256!=='d932ee3943770bcf123f614fd059633c7591a5ef66077c65bb4c80935c28e0ba'||oldProvider.storeSha256!=='7e4da46f14dfbb19b1268286dbf4c0124ac00e90c6c2dc601d49f5a808a80a31')throw Error('Exact original full-receipt provider required');
for(const [name,meta] of Object.entries(oldManifest.assets) as [string,{sha256:string;bytes:number}][]){const bytes=await Bun.file(join(oldDirectory,name)).bytes();if(bytes.length!==meta.bytes||digest(bytes)!==meta.sha256)throw Error('Original old-provider asset differs: '+name);oldProvider.assetsVerified++;}
let activeBundle=oldDirectory;
const server=Bun.serve({hostname:'127.0.0.1',port:0,async fetch(request){
  const requested=new URL(request.url).pathname;
  if(!requested.startsWith('/example/truss/'))return new Response('Missing prefix',{status:404});
  const path=requested.slice('/example/truss'.length);
  if(path==='/')return new Response('<!doctype html><title>Truss lifecycle</title>',{headers:{'content-type':'text/html'}});
  if(path==='/worker.js')return new Response(await built.outputs[0]!.text(),{headers:{'content-type':'text/javascript'}});
  if(path==='/model.json')return new Response(Bun.file(new URL('./fixtures/local-products-model.json',import.meta.url)));
  if(!path.includes('..')){const file=Bun.file(join(activeBundle,path.slice(1)));if(await file.exists())return new Response(file);}
  return new Response('Missing',{status:404});
}});
const browser=await chromium.launch({headless:true});
try{
 const context=await browser.newContext(),page=await context.newPage();
 const origin=`http://127.0.0.1:${server.port}/example/truss/`,external:string[]=[];
 await context.route('**/*',(route:any)=>{if(!route.request().url().startsWith(origin)||route.request().method()!=='GET'){external.push(route.request().url());return route.abort();}return route.continue();});
 await page.goto(origin);
 async function worker(){await page.evaluate(()=>{(window as any).worker=new Worker(new URL('worker.js',location.href),{type:'module'});});}
 async function call(data:any){return page.evaluate((data:any)=>new Promise<any>((resolve,reject)=>{const w=(window as any).worker;w.onmessage=(event:any)=>resolve(event.data);w.onerror=reject;w.postMessage(data);}),data);}
 function equal(a:any,b:any,label:string){if(JSON.stringify(a)!==JSON.stringify(b))throw Error(label+': '+JSON.stringify({a,b}));}
 const name='actual-full-to-compact-upgrade';await worker();
 const opened=await call({command:'open',name});if(opened.outcome!=='available')throw Error(JSON.stringify(opened));
 if((await call({command:'register'})).outcome!=='registered')throw Error('Old registration failed');
 if((await call({command:'seedBulk',count:4,firstKey:'bar'})).outcome!=='bulk_loaded')throw Error('Old sample load failed');
 if((await call({command:'action'})).outcome!=='action_registered')throw Error('Old action failed');
 const selected=await call({command:'materialize',sql:"UPDATE products SET name='Upgraded' WHERE name='Sample'",batchSize:2,maxItems:4});
 if(selected.outcome!=='materialized'||selected.count!==4)throw Error(JSON.stringify(selected));
 const oldSeal=await call({command:'seal',request:{requestKey:'old-full-seal',attempt:'1'}});if(oldSeal.outcome!=='sealed')throw Error(JSON.stringify(oldSeal));
 const submitInput={key:'old-route',reference:oldSeal.reference,control:{requestKey:'old-submit',attempt:'1'}};
 const submitted=await call({command:'submit',input:submitInput});if(submitted.status!=='submitted')throw Error(JSON.stringify(submitted));
 const job=submitted.state.job,claimInput={job,control:{requestKey:'old-claim',attempt:'1'}},claimed=await call({command:'claim',input:claimInput});
 if(claimed.status!=='claimed')throw Error(JSON.stringify(claimed));
 const execution={job,batch:0,fence:claimed.fence},committed=await call({command:'executeBatch',input:execution});if(committed.status!=='committed')throw Error(JSON.stringify(committed));
 await call({command:'close'});await page.evaluate(()=>(window as any).worker.terminate());
 activeBundle=packaged.directory;await worker();
 const reopened=await call({command:'open',name});if(reopened.outcome!=='available')throw Error(JSON.stringify(reopened));
 if((await call({command:'action'})).outcome!=='action_registered')throw Error('New action failed');
 equal(await call({command:'recoverSeal',reference:oldSeal.reference}),oldSeal,'Original old seal outcome');
 equal(await call({command:'recoverSubmit',input:submitInput}),submitted,'Original old submit outcome');
 equal(await call({command:'recoverClaim',input:claimInput}),claimed,'Original old claim outcome');
 equal(await call({command:'recoverBatch',input:execution}),committed,'Original old batch outcome');
 await call({command:'close'});
 const transport=await call({command:'compactSealFixture',info:reopened.info,originalRequest:'old-full-seal',requestKey:'compact-equivalent-fixture'});
 if(transport.outcome!=='compact_transport_fixture')throw Error(JSON.stringify(transport));
 if((await call({command:'open',name})).outcome!=='available')throw Error('Fixture reopen failed');await call({command:'action'});
 const crossOld=await call({command:'submit',input:{key:'old-route',reference:transport.reference,control:{requestKey:'compact-to-old',attempt:'1'}}});
 if(crossOld.status!=='submitted')throw Error(JSON.stringify(crossOld));if(crossOld.state.job.namespace!==job.namespace||crossOld.state.job.id!==job.id)throw Error('Compact seal must reuse actual old job');
 const newJob=await call({command:'submit',input:{key:'new-route',reference:transport.reference,control:{requestKey:'new-route-submit',attempt:'1'}}});if(newJob.status!=='submitted')throw Error(JSON.stringify(newJob));
 const crossNew=await call({command:'submit',input:{key:'new-route',reference:oldSeal.reference,control:{requestKey:'old-to-compact',attempt:'1'}}});
 if(crossNew.status!=='submitted')throw Error(JSON.stringify(crossNew));if(crossNew.state.job.namespace!==newJob.state.job.namespace||crossNew.state.job.id!==newJob.state.job.id)throw Error('Old seal must reuse compact-intent job');
 const lastClaim=await call({command:'claim',input:{job,control:{requestKey:'after-upgrade-claim',attempt:'1'}}});if(lastClaim.status!=='claimed'||lastClaim.batch!==1)throw Error(JSON.stringify(lastClaim));
 const last=await call({command:'executeBatch',input:{job,batch:1,fence:lastClaim.fence}});if(last.status!=='committed'||last.items.length!==2)throw Error(JSON.stringify(last));
 const point=await call({command:'materialize',sql:"UPDATE products SET name='Foo' WHERE id='bar'",batchSize:2,maxItems:4});if(point.outcome!=='materialized'||point.count!==1)throw Error(JSON.stringify(point));
 const actualCompact=await call({command:'seal',request:{requestKey:'actual-new-compact',attempt:'1'}});if(actualCompact.outcome!=='sealed')throw Error(JSON.stringify(actualCompact));
 const pointJob=await call({command:'submit',input:{key:'actual-compact',reference:actualCompact.reference,control:{requestKey:'point-submit',attempt:'1'}}});if(pointJob.status!=='submitted')throw Error(JSON.stringify(pointJob));
 const pointClaim=await call({command:'claim',input:{job:pointJob.state.job,control:{requestKey:'point-claim',attempt:'1'}}});if(pointClaim.status!=='claimed')throw Error(JSON.stringify(pointClaim));
 const pointDone=await call({command:'executeBatch',input:{job:pointJob.state.job,batch:0,fence:pointClaim.fence}});if(pointDone.status!=='committed')throw Error(JSON.stringify(pointDone));
 await call({command:'close'});if((await call({command:'open',name})).outcome!=='available')throw Error('Final reopen failed');
 const rows=await call({command:'pageObjects',limit:512,afterId:null});if(rows.objects?.length!==4)throw Error(JSON.stringify(rows));
 for(const row of rows.objects){const fields=Object.fromEntries(row.fields.map((f:any)=>[f.field,f.value]));if(fields['product-name']!==(fields['product-id']==='bar'?'Foo':'Upgraded')||row.version!==(fields['product-id']==='bar'?'3':'2'))throw Error('Upgrade public readback mismatch');}
 await call({command:'close'});if(external.length)throw Error(JSON.stringify(external));
 const report={passed:true,actualOldProvider:oldProvider,newProvider:packaged,oldSealRecoveryByteEqual:true,oldSubmitClaimBatchRecoveryByteEqual:true,oldFrozenRemainingBatchExecuted:true,newCompactPointExecuted:true,reopenedPublicValuesVerified:true,crossFormatIntentBothDirections:true,crossFormatScope:'Test-only compact transport fixture derived from actual old-provider sealed bytes; not fresh authority issuance',externalRequests:external};
 const encoded=JSON.stringify(report,null,2)+'\n';if(Bun.argv[3])await Bun.write(Bun.argv[3],encoded);console.log(encoded);
}finally{await browser.close();server.stop(true);await rm(temporary,{recursive:true,force:true});}
