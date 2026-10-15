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
  plugins:[{name:'owned-provider',setup(build){build.onResolve({filter:/^\.\/store$/},()=>({path:'./store.js',external:true}));}}]});
if(!built.success)throw Error(String(built.logs));
const server=Bun.serve({hostname:'127.0.0.1',port:0,async fetch(request){
  const requested=new URL(request.url).pathname;
  if(!requested.startsWith('/example/truss/'))return new Response('Missing prefix',{status:404});
  const path=requested.slice('/example/truss'.length);
  if(path==='/')return new Response('<!doctype html><title>Truss lifecycle</title>',{headers:{'content-type':'text/html'}});
  if(path==='/worker.js')return new Response(await built.outputs[0]!.text(),{headers:{'content-type':'text/javascript'}});
  if(path==='/model.json')return new Response(Bun.file(new URL('./fixtures/local-products-model.json',import.meta.url)));
  if(!path.includes('..')){const file=Bun.file(join(packaged.directory,path.slice(1)));if(await file.exists())return new Response(file);}
  return new Response('Missing',{status:404});
}});
const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext();
  const a=await context.newPage(),b=await context.newPage();
  const origin=`http://127.0.0.1:${server.port}/example/truss/`;
  async function prepare(page:any){await page.goto(origin);await page.evaluate(()=>{
    (window as any).worker=new Worker(new URL('worker.js',location.href),{type:'module'});
    (window as any).call=(data:any)=>new Promise((resolve,reject)=>{
      const worker=(window as any).worker;worker.onmessage=(event:any)=>resolve(event.data);worker.onerror=reject;worker.postMessage(data);
    });
  });}
  const call=(page:any,data:any)=>page.evaluate((data:any)=>(window as any).call(data),data);
  await prepare(a);await prepare(b);
  const first=await call(a,{command:'open',name:'lifecycle-basic'});
  if(first.outcome!=='available')throw Error(JSON.stringify(first));
  const registered=await call(a,{command:'register'});
  if(registered.outcome!=='registered'||registered.catalog.catalogRevision!=='1'
    ||registered.catalog.types.length!==1||registered.catalog.properties.length!==2||registered.catalog.keys.length!==1)
    throw Error(JSON.stringify(registered));
  if(registered.catalog.changes.length!==3||registered.catalog.changes.some((change:any)=>change.before!==null))throw Error('Original catalog change records required');
  const original=await Bun.file(new URL('./fixtures/local-products-model.json',import.meta.url)).text();
  if(registered.catalog.document.sourceUtf8!==original||registered.catalog.document.sourceSha256!=='b8ce3cfe76eeda7c1531b2bbf8aba121c9d9614800ff1f3301f853c048516f27')throw Error('Original document custody mismatch');
  const unchanged=await call(a,{command:'register'});
  if(unchanged.outcome!=='unchanged')throw Error(JSON.stringify(unchanged));
  const action=await call(a,{command:'action'});
  if(action.outcome!=='action_registered'||action.preparationSha256!=='6f5e69462c327da970f07ca1f6253dbacc4db0badf1335b7d91e3f38eb67ad40'||!action.opaque)throw Error(JSON.stringify(action));
  const expectedGrant={profile:{id:'umf.actions.local-store-read',version:'1'},target:{element:'products',key:'pk',module:'sales'},fields:[{module:'sales',element:'product-id'},{module:'sales',element:'product-name'}],view:'complete-canonical-target-population',disposition:'original'};
  if(JSON.stringify(action.declaration)!==JSON.stringify(expectedGrant))throw Error(JSON.stringify(action.declaration));
  const forgedAction=await call(a,{command:'forgedAction'});if(forgedAction.outcome!=='refused')throw Error(JSON.stringify(forgedAction));
  const oldAction=await call(a,{command:'reopenAction',name:'lifecycle-basic'});
  if(oldAction.outcome!=='previous_action_refused'||JSON.stringify(oldAction.info)!==JSON.stringify(first.info))throw Error(JSON.stringify(oldAction));
  const reissuedAction=await call(a,{command:'action'});if(reissuedAction.outcome!=='action_registered'||reissuedAction.preparationSha256!==action.preparationSha256)throw Error(JSON.stringify(reissuedAction));
  const forged=await call(a,{command:'forged'});
  if(forged.outcome!=='refused')throw Error(JSON.stringify(forged));
  const second=await call(b,{command:'open',name:'lifecycle-basic'});
  if(second.outcome!=='unavailable'||second.reason!=='store_in_use')throw Error(JSON.stringify(second));
  const closed=await call(a,{command:'close'});
  if(closed.outcome!=='closed')throw Error(JSON.stringify(closed));
  const takeover=await call(b,{command:'open',name:'lifecycle-basic'});
  if(takeover.outcome!=='available'||JSON.stringify(first.info)!==JSON.stringify(takeover.info))throw Error(JSON.stringify(takeover));
  await call(b,{command:'close'});
  await prepare(a);
  const reopened=await call(a,{command:'open',name:'lifecycle-basic'});
  if(reopened.outcome!=='available'||JSON.stringify(first.info)!==JSON.stringify(reopened.info))throw Error(JSON.stringify(reopened));
  const catalog=await call(a,{command:'catalog'});
  if(catalog.outcome!=='catalog'||JSON.stringify(catalog.catalog)!==JSON.stringify(registered.catalog))throw Error('Catalog changed across IndexedDB reopen');
  await call(a,{command:'close'});
  const receipt={scope:'Chromium worker lifecycle, original core catalog and local action/read-grant issuance with IndexedDB reopen',assetPrefix:'/example/truss/',chromium:browser.version(),bundle:{manifestSha256:packaged.manifestSha256,providerSha256:packaged.providerSha256},first,forged,second,takeover,reopened,
    action:{registered:action,forged:forgedAction,previousOpen:oldAction.outcome,reissued:reissuedAction.outcome},
    catalog:{registration:registered.outcome,retry:unchanged.outcome,revision:catalog.catalog.catalogRevision,sourceSha256:catalog.catalog.document.sourceSha256,types:catalog.catalog.types,properties:catalog.catalog.properties,keys:catalog.catalog.keys,changeCount:catalog.catalog.changes.length},
    actionExecution:false,selectionReadGrant:true,crashRecovery:false};
  const encoded=JSON.stringify(receipt,null,2)+'\n';if(Bun.argv[3])await Bun.write(Bun.argv[3],encoded);console.log(encoded);
}finally{await browser.close();server.stop(true);await rm(temporary,{recursive:true,force:true});}
