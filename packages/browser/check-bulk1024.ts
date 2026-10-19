// SPDX-License-Identifier: MIT OR Apache-2.0
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
  const external:string[]=[],errors:string[]=[];
  await context.route('**/*',(route:any)=>{const r=route.request();if(!r.url().startsWith(origin)||r.method()!=='GET'){external.push(r.method()+' '+r.url());return route.abort();}return route.continue();});
  a.on('pageerror',(error:any)=>errors.push(error.message));
  await prepare(a);await prepare(b);
  const name='bulk-update-1024';
  const opened=await call(a,{command:'open',name});if(opened.outcome!=='available')throw Error(JSON.stringify(opened));
  if((await call(a,{command:'register'})).outcome!=='registered')throw Error('Catalog registration failed');
  const seeded=await call(a,{command:'seedBulk',count:1024,firstKey:'bar'});if(seeded.outcome!=='bulk_loaded'||seeded.ids.length!==1024)throw Error(JSON.stringify(seeded));
  if((await call(a,{command:'action'})).outcome!=='action_registered')throw Error('Action/read grant failed');
  const completed:any[]=[];
  async function update(sql:string,key:string,count:number,version:string,reopen=false){
    const started=performance.now();let phaseStarted=started;const phaseMs:Record<string,number>={};const batchMs:number[]=[];
    const selected=await call(a,{command:'materialize',sql,batchSize:100,maxItems:1024});
    if(selected.outcome!=='materialized'||selected.count!==count||selected.batches.length!==Math.ceil(count/100))throw Error(JSON.stringify(selected));
    phaseMs.materialize=performance.now()-phaseStarted;phaseStarted=performance.now();
    const sealed=await call(a,{command:'seal',request:{requestKey:key+'-seal',attempt:'1'}});if(sealed.outcome!=='sealed')throw Error(JSON.stringify(sealed));
    phaseMs.seal=performance.now()-phaseStarted;phaseStarted=performance.now();
    const submitted=await call(a,{command:'submit',input:{key,reference:sealed.reference,control:{requestKey:key+'-submit',attempt:'1'}}});if(submitted.status!=='submitted')throw Error(JSON.stringify(submitted));
    phaseMs.submit=performance.now()-phaseStarted;
    const job=submitted.state.job;let changed=0;
    for(let i=0;i<selected.batches.length;i++){
      const claimed=await call(a,{command:'claim',input:{job,control:{requestKey:key+'-claim-'+i,attempt:'1'}}});
      if(claimed.status!=='claimed'||claimed.batch!==i)throw Error(JSON.stringify(claimed));
      const executionStarted=performance.now();
      const input={job,batch:claimed.batch,fence:claimed.fence},result=await call(a,{command:'executeBatch',input});
      if(result.status!=='committed'||result.items.length!==selected.batches[i].count||result.items.some((item:any)=>item.result.version!==version||item.result.noOp))throw Error(JSON.stringify(result));
      batchMs.push(performance.now()-executionStarted);changed+=result.items.length;
      if(i===0){
        if(JSON.stringify(await call(a,{command:'recoverBatch',input}))!==JSON.stringify(result))throw Error('First batch recovery changed');
        if(reopen){
          await call(a,{command:'close'});if((await call(a,{command:'open',name})).outcome!=='available')throw Error('Reopen failed');
          if((await call(a,{command:'action'})).outcome!=='action_registered')throw Error('Fresh action/read grant failed');
          if(JSON.stringify(await call(a,{command:'recoverBatch',input}))!==JSON.stringify(result))throw Error('Reopened batch recovery changed');
        }
      }
    }
    const reviewed=await call(a,{command:'reviewJob',job});
    if(changed!==count||reviewed.state?.status!=='completed'||reviewed.state.committedBatches!==selected.batches.length)throw Error(JSON.stringify(reviewed));
    completed.push({sql,count,batches:selected.batches.length,elapsedMs:performance.now()-started,phaseMs,committedBatchMs:batchMs,firstBatchRecoveryEqual:true,reopenedRecovery:reopen,planSha256:selected.plan.sha256,manifestSha256:selected.manifest.sha256});
  }
  await update("UPDATE products SET name='Bulk' WHERE name='Sample'",'all-1024',1024,'2',true);
  await update("UPDATE products SET name='Foo' WHERE id='bar'",'one-product',1,'3');
  await call(a,{command:'close'});if((await call(a,{command:'open',name})).outcome!=='available')throw Error('Final reopen failed');
  const objects:any[]=[];let afterId:string|null=null;
  do{const page=await call(a,{command:'pageObjects',limit:512,afterId});if(!Array.isArray(page.objects))throw Error(JSON.stringify(page));objects.push(...page.objects);afterId=page.nextAfterId;if(objects.length>1024)throw Error('Duplicate page');}while(afterId!==null);
  if(JSON.stringify(objects.map(o=>o.id))!==JSON.stringify(seeded.ids))throw Error('Public identity readback differs');
  for(let i=0;i<objects.length;i++){
    const fields=Object.fromEntries(objects[i].fields.map((f:any)=>[f.field,f.value]));
    if(fields['product-id']!==(i===0?'bar':'p'+String(i).padStart(4,'0'))||fields['product-name']!==(i===0?'Foo':'Bulk')||objects[i].version!==(i===0?'3':'2'))throw Error('Committed public values/versions differ');
  }
  await call(a,{command:'close'});if(errors.length||external.length)throw Error(JSON.stringify({errors,external}));
  const sealStorage=await call(a,{command:'sealStorage',info:opened.info});if(sealStorage.outcome!=='seal_storage'||sealStorage.seals.length!==2||sealStorage.seals[0].receipts+sealStorage.seals[1].receipts!==1025)throw Error(JSON.stringify(sealStorage));
  const report={sealStorage,passed:true,execution:'real Chromium worker/PGlite0.5.10/PostgreSQL18.6',actualLoadedRows:1024,actualChangedUpdates:1025,jobs:completed,allReopenedPublicValuesVerified:true,externalRequests:external,serviceWrites:0,performanceQualified:false,provider:packaged};
  const encoded=JSON.stringify(report,null,2)+'\n';if(Bun.argv[3])await Bun.write(Bun.argv[3],encoded);console.log(encoded);
}finally{await browser.close();server.stop(true);await rm(temporary,{recursive:true,force:true});}
