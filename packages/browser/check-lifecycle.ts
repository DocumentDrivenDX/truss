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
  plugins:[{name:'owned-provider',setup(build){build.onResolve({filter:/^\.\/store$/},()=>({path:'./store.js',external:true}));build.onResolve({filter:/^@electric-sql\/pglite$/},()=>({path:'./pglite/index.js',external:true}));}}]});
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
  const seeded=await call(a,{command:'seedFixture',name:'lifecycle-basic'});if(seeded.outcome!=='public_objects_loaded')throw Error(JSON.stringify(seeded));
  const readyAction=await call(a,{command:'action'});if(readyAction.outcome!=='action_registered')throw Error(JSON.stringify(readyAction));
  const forgedGrant=await call(a,{command:'forgedGrant'});if(forgedGrant.outcome!=='refused')throw Error(JSON.stringify(forgedGrant));
  const materialized=await call(a,{command:'materialize'});
  if(materialized.outcome!=='materialized'||materialized.count!==3||materialized.batches.map((b:any)=>b.count).join(',')!=='2,1')throw Error(JSON.stringify(materialized));
  const body=JSON.parse(materialized.manifest.utf8);
  if(body.items.map((item:any)=>item.entity.components[0].string).join(',')!=='bar,baz,qux'||body.items.some((item:any)=>item.guard.version!=='1'))throw Error('Original selected Key/version mismatch');
  const sealRequest={requestKey:'basic-seal',attempt:'attempt-1'};
  const sealed=await call(a,{command:'seal',request:sealRequest});if(sealed.outcome!=='sealed')throw Error(JSON.stringify(sealed));
  const replay=await call(a,{command:'seal',request:sealRequest});if(JSON.stringify(replay)!==JSON.stringify(sealed))throw Error('Seal replay changed original outcome bytes');
  const conflict=await call(a,{command:'seal',request:{...sealRequest,attempt:'attempt-2'}});if(conflict.outcome!=='conflict'||conflict.code!=='request_key_conflict')throw Error(JSON.stringify(conflict));
  const submitInput={key:'products-bulk',reference:sealed.reference,control:{requestKey:'submit-1',attempt:'attempt-1'}};
  const submitted=await call(a,{command:'submit',input:submitInput});if(submitted.status!=='submitted'||submitted.state.status!=='queued')throw Error(JSON.stringify(submitted));
  const submitReplay=await call(a,{command:'submit',input:submitInput});if(JSON.stringify(submitReplay)!==JSON.stringify(submitted))throw Error('Original submission replay changed');
  const sameJob=await call(a,{command:'submit',input:{...submitInput,control:{requestKey:'submit-2',attempt:'attempt-2'}}});if(sameJob.status!=='submitted'||sameJob.state.job.id!==submitted.state.job.id||sameJob.state.job.namespace!==submitted.state.job.namespace||sameJob.state.status!=='queued'||sameJob.state.nextBatch!==0)throw Error('Same submit key created another job');
  const secondSeal=await call(a,{command:'seal',request:{requestKey:'second-genuine-seal',attempt:'seal-2'}});if(secondSeal.outcome!=='sealed')throw Error(JSON.stringify(secondSeal));
  const sameManifest=await call(a,{command:'submit',input:{...submitInput,reference:secondSeal.reference,control:{requestKey:'submit-3',attempt:'attempt-3'}}});if(sameManifest.status!=='submitted'||sameManifest.state.job.id!==submitted.state.job.id)throw Error('Genuine second seal changed submission intent');
  const refusalInput={...submitInput,reference:{...sealed.reference,requestKey:'absent-seal'},control:{requestKey:'submit-refused',attempt:'attempt-refused'}};
  const submitRefusal=await call(a,{command:'submit',input:refusalInput});if(submitRefusal.status!=='unsupported')throw Error(JSON.stringify(submitRefusal));
  const refusalRecovery=await call(a,{command:'recoverSubmit',input:refusalInput});if(JSON.stringify(refusalRecovery)!==JSON.stringify(submitRefusal))throw Error('Recorded refusal recovery repeated fresh seal admission');
  const controlConflict=await call(a,{command:'submit',input:{...submitInput,key:'changed-key'}});if(controlConflict.status!=='conflict')throw Error(JSON.stringify(controlConflict));
  const claimInput={job:submitted.state.job,control:{requestKey:'claim-1',attempt:'attempt-claim-1'}};
  const claimed=await call(a,{command:'claim',input:claimInput});if(claimed.status!=='claimed'||claimed.batch!==0||claimed.fence!=='1'||typeof claimed.leaseUntil!=='string')throw Error(JSON.stringify(claimed));
  const claimReplay=await call(a,{command:'claim',input:claimInput});if(JSON.stringify(claimReplay)!==JSON.stringify(claimed))throw Error('Original claim replay renewed or changed');
  const secondClaim=await call(a,{command:'claim',input:{...claimInput,control:{requestKey:'claim-2',attempt:'attempt-claim-2'}}});if(secondClaim.status!=='unsupported'||secondClaim.code!=='PAP_FENCE')throw Error(JSON.stringify(secondClaim));
  const executeInput={job:claimed.job,batch:claimed.batch,fence:claimed.fence};
  const executed=await call(a,{command:'executeBatch',input:executeInput});if(executed.status!=='committed'||executed.items.length!==2||executed.items.some((i:any)=>i.result.version!=='2'||i.result.noOp))throw Error(JSON.stringify(executed));
  const executeReplay=await call(a,{command:'executeBatch',input:executeInput});if(JSON.stringify(executeReplay)!==JSON.stringify(executed))throw Error('Batch replay changed original outcome');
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
  const recoveryAction=await call(a,{command:'action'});if(recoveryAction.outcome!=='action_registered')throw Error(JSON.stringify(recoveryAction));
  const recovered=await call(a,{command:'recoverSeal',reference:Object.fromEntries(Object.entries(sealed.reference).reverse())});if(JSON.stringify(recovered)!==JSON.stringify(sealed))throw Error('Recovered seal changed original outcome');
  const missing=await call(a,{command:'recoverSeal',reference:{...sealed.reference,requestKey:'missing-seal'}});if(missing.outcome!=='unresolved'||missing.code!=='not_found')throw Error(JSON.stringify(missing));
  const recoveredSubmit=await call(a,{command:'recoverSubmit',input:submitInput});if(JSON.stringify(recoveredSubmit)!==JSON.stringify(submitted))throw Error('Recovered submission changed');
  const reviewedJob=await call(a,{command:'reviewJob',job:submitted.state.job});if(reviewedJob.state?.status!=='queued'||reviewedJob.state?.job?.id!==submitted.state.job.id||JSON.stringify(reviewedJob.manifest)!==JSON.stringify(sealed.manifest))throw Error('Retained job source/state changed');
  const recoveredClaim=await call(a,{command:'recoverClaim',input:claimInput});if(JSON.stringify(recoveredClaim)!==JSON.stringify(claimed))throw Error('Recovered claim renewed or changed');
  const recoveredBatch=await call(a,{command:'recoverBatch',input:executeInput});if(JSON.stringify(recoveredBatch)!==JSON.stringify(executed))throw Error('Batch reopen recovery changed original outcome');
  const claimedSecond=await call(a,{command:'claim',input:{job:claimed.job,control:{requestKey:'claim-next',attempt:'attempt-next'}}});if(claimedSecond.status!=='claimed'||claimedSecond.batch!==1||claimedSecond.fence!=='2')throw Error(JSON.stringify(claimedSecond));
  const executedSecond=await call(a,{command:'executeBatch',input:{job:claimedSecond.job,batch:claimedSecond.batch,fence:claimedSecond.fence}});if(executedSecond.status!=='committed'||executedSecond.items.length!==1||executedSecond.items[0].result.version!=='2')throw Error(JSON.stringify(executedSecond));
  const finalState=await call(a,{command:'reviewJob',job:claimed.job});if(finalState.state?.status!=='completed'||finalState.state?.committedBatches!==2)throw Error(JSON.stringify(finalState));
  const finalObjects=await call(a,{command:'readObjects'});if(finalObjects.length!==4||finalObjects.filter((o:any)=>o.fields.some((f:any)=>f.field==='product-name'&&f.value==='Bulk')).length!==3)throw Error(JSON.stringify(finalObjects));
  async function newJob(sql:string,key:string,count=3){
    const work=await call(a,{command:'materialize',sql});if(work.outcome!=='materialized'||work.count!==count)throw Error(JSON.stringify(work));
    const seal=await call(a,{command:'seal',request:{requestKey:key+'-seal',attempt:'1'}});if(seal.outcome!=='sealed')throw Error(JSON.stringify(seal));
    const submitted=await call(a,{command:'submit',input:{key,reference:seal.reference,control:{requestKey:key+'-submit',attempt:'1'}}});if(submitted.status!=='submitted')throw Error(JSON.stringify(submitted));return submitted.state.job;
  }
  const cancelJob=await newJob("UPDATE products SET name='Cancelled' WHERE name='Bulk'",'cancelled');
  const cancelInput={job:cancelJob,control:{requestKey:'cancel-job',attempt:'1'}};
  const cancelled=await call(a,{command:'cancel',input:cancelInput});
  if(cancelled.status!=='cancelled'||cancelled.state.status!=='cancelled'||cancelled.state.committedBatches!==0)throw Error(JSON.stringify(cancelled));
  const cancelReplay=await call(a,{command:'cancel',input:cancelInput});if(JSON.stringify(cancelReplay)!==JSON.stringify(cancelled))throw Error('Cancel replay changed');
  const cancelClaim=await call(a,{command:'claim',input:{job:cancelJob,control:{requestKey:'cancelled-claim',attempt:'1'}}});if(cancelClaim.code!=='PAP_CANCELLED')throw Error(JSON.stringify(cancelClaim));
  const cancelExecution=await call(a,{command:'executeBatch',input:{job:cancelJob,batch:0,fence:'1'}});if(cancelExecution.code!=='PAP_CANCELLED')throw Error(JSON.stringify(cancelExecution));
  await call(a,{command:'close'});await prepare(a);const cancelReopen=await call(a,{command:'open',name:'lifecycle-basic'});if(cancelReopen.outcome!=='available')throw Error(JSON.stringify(cancelReopen));
  await call(a,{command:'action'});
  const cancelRecovered=await call(a,{command:'recoverCancel',input:cancelInput});if(JSON.stringify(cancelRecovered)!==JSON.stringify(cancelled))throw Error('Cancel recovery changed');
  const afterCancel=await call(a,{command:'readObjects'});if(JSON.stringify(afterCancel)!==JSON.stringify(finalObjects))throw Error('Cancelled job changed objects');
  const noOpJob=await newJob("UPDATE products SET name='Bulk' WHERE name='Bulk'",'noop'),noOpResults=[];
  for(let batch=0;batch<2;batch++){
    const claim=await call(a,{command:'claim',input:{job:noOpJob,control:{requestKey:'noop-claim-'+batch,attempt:'1'}}});if(claim.status!=='claimed')throw Error(JSON.stringify(claim));
    const result=await call(a,{command:'executeBatch',input:{job:noOpJob,batch,fence:claim.fence}});if(result.status!=='committed'||result.items.some((i:any)=>!i.result.noOp||i.result.version!=='2'||i.result.changes.length))throw Error(JSON.stringify(result));noOpResults.push(result);
  }
  const afterNoOp=await call(a,{command:'readObjects'});if(JSON.stringify(afterNoOp)!==JSON.stringify(finalObjects))throw Error('No-op changed objects');
  const failedJob=await newJob("UPDATE products SET name='Fail' WHERE name='Bulk'",'rollback');
  const failedClaim=await call(a,{command:'claim',input:{job:failedJob,control:{requestKey:'rollback-claim',attempt:'1'}}});if(failedClaim.status!=='claimed')throw Error(JSON.stringify(failedClaim));
  const secondId=finalObjects.find((o:any)=>o.fields.some((f:any)=>f.field==='product-id'&&f.value==='baz')).id;
  const fault=await call(a,{command:'batchFault',id:secondId});if(fault.outcome!=='fault_installed')throw Error(JSON.stringify(fault));
  const faultAction=await call(a,{command:'action'});if(faultAction.outcome!=='action_registered')throw Error(JSON.stringify(faultAction));
  const failedInput={job:failedJob,batch:0,fence:failedClaim.fence};
  const failed=await call(a,{command:'executeBatch',input:failedInput});if(failed.status!=='failed'||failed.code!=='BATCH_ROLLED_BACK')throw Error(JSON.stringify(failed));
  const afterFailure=await call(a,{command:'readObjects'});if(JSON.stringify(afterFailure)!==JSON.stringify(finalObjects))throw Error('Failed batch leaked first-item changes');
  const failedRecovery=await call(a,{command:'recoverBatch',input:failedInput});if(JSON.stringify(failedRecovery)!==JSON.stringify(failed))throw Error('Confirmed failed batch recovery changed');
  const failedState=await call(a,{command:'reviewJob',job:failedJob});if(failedState.state?.status!=='stopped'||failedState.state?.committedBatches!==0)throw Error(JSON.stringify(failedState));
  const removed=await call(a,{command:'batchFault',id:secondId,remove:true});if(removed.outcome!=='fault_removed')throw Error(JSON.stringify(removed));
  await call(a,{command:'action'});
  const staleJob=await newJob("UPDATE products SET name='WouldRollback' WHERE name='Bulk'",'stale');
  const interventionJob=await newJob("UPDATE products SET name='Changed' WHERE id='baz'",'intervention',1);
  const interventionClaim=await call(a,{command:'claim',input:{job:interventionJob,control:{requestKey:'intervention-claim',attempt:'1'}}});if(interventionClaim.status!=='claimed')throw Error(JSON.stringify(interventionClaim));
  const intervention=await call(a,{command:'executeBatch',input:{job:interventionJob,batch:0,fence:interventionClaim.fence}});if(intervention.status!=='committed'||intervention.items[0].result.version!=='3')throw Error(JSON.stringify(intervention));
  const staleClaim=await call(a,{command:'claim',input:{job:staleJob,control:{requestKey:'stale-claim',attempt:'1'}}});if(staleClaim.status!=='claimed')throw Error(JSON.stringify(staleClaim));
  const staleInput={job:staleJob,batch:0,fence:staleClaim.fence};
  const stale=await call(a,{command:'executeBatch',input:staleInput});if(stale.status!=='conflict'||stale.code!=='PAP_GUARD'||stale.item!==1)throw Error(JSON.stringify(stale));
  const afterStale=await call(a,{command:'readObjects'});
  const firstAfterStale=afterStale.find((o:any)=>o.fields.some((f:any)=>f.field==='product-id'&&f.value==='bar'));
  if(firstAfterStale.version!=='2'||!firstAfterStale.fields.some((f:any)=>f.field==='product-name'&&f.value==='Bulk')||afterStale.some((o:any)=>o.fields.some((f:any)=>f.value==='WouldRollback')))throw Error('Stale batch leaked first-item changes');
  const staleRecovery=await call(a,{command:'recoverBatch',input:staleInput});if(JSON.stringify(staleRecovery)!==JSON.stringify(stale))throw Error('Stale outcome recovery changed');
  let feedCursor:any=null;const feedPages:any[]=[],feedEvents:any[]=[];
  do{
    const page=await call(a,{command:'readFeed',input:{cursor:feedCursor,limit:3}});if(page.status!=='page')throw Error(JSON.stringify(page));feedPages.push(page);feedEvents.push(...page.events);feedCursor=page.cursor;if(!page.hasMore)break;
  }while(feedPages.length<4);
  if(feedEvents.length!==8||feedEvents.filter(e=>e.operation==='create').length!==4||feedEvents.filter(e=>e.operation==='property').length!==4||!feedEvents.some((e,i)=>i>0&&BigInt(e.sequence)>BigInt(feedEvents[i-1].sequence)+1n)||feedCursor.afterSeq!==feedEvents.at(-1).sequence)throw Error('Incomplete journal pages or rollback-gap cursor');
  if(feedEvents.some(e=>e.after.fields.some((f:any)=>f.value==='Fail'||f.value==='WouldRollback'))||feedEvents.at(-1).change?.after!=='Changed')throw Error('Failed business event leaked or logical decode failed');
  const foreignCursor=await call(a,{command:'readFeed',input:{cursor:{...feedCursor,storeId:'00000000-0000-4000-8000-000000000000'},limit:3}});if(foreignCursor.status!=='refused'||foreignCursor.code!=='CURSOR_SCOPE')throw Error(JSON.stringify(foreignCursor));
  const feedReopen=await call(a,{command:'reopenAction',name:'lifecycle-basic'});if(feedReopen.outcome!=='previous_action_refused')throw Error(JSON.stringify(feedReopen));
  await call(a,{command:'action'});
  const emptyFeed=await call(a,{command:'readFeed',input:{cursor:feedCursor,limit:3}});if(emptyFeed.status!=='page'||emptyFeed.events.length||emptyFeed.hasMore||JSON.stringify(emptyFeed.cursor)!==JSON.stringify(feedCursor))throw Error('Empty reopened feed advanced cursor');
  const recoveredLoad=await call(a,{command:'recoverLoad'});if(JSON.stringify(recoveredLoad)!==JSON.stringify(seeded.loaded))throw Error('Recovered load changed original outcome');
  await call(a,{command:'close'});
  const physical=await call(a,{command:'inspectStorage'});if(physical.objects!=='4'||physical.keys!=='4'||physical.reservations!=='4'||physical.journal!=='8'||physical.generation!=='1'||physical.exact!==true)throw Error(JSON.stringify(physical));
  const receipt={cancellation:{cancelled,cancelReplay,cancelClaim,cancelExecution,cancelRecovered},scope:'Actual worker catalog/action/read-grant, original Weft materialization and UMF manifest, keyed seal/replay/reopen recovery; public atomic load/replay/readback',assetPrefix:'/example/truss/',chromium:browser.version(),bundle:{manifestSha256:packaged.manifestSha256,providerSha256:packaged.providerSha256},first,forged,second,takeover,reopened,
    feed:{pages:feedPages,events:feedEvents.length,foreignCursor:foreignCursor.code,emptyAfterReopen:emptyFeed},
    staleGuard:{result:stale,recoveredByteEqual:true,firstItemUnchanged:true},
    noOp:{results:noOpResults,unchanged:true},
    atomicRollback:{result:failed,recoveredByteEqual:true,unchanged:true,state:failedState},
    execution:{first:executed,second:executedSecond,replayedByteEqual:true,recoveredByteEqual:true,finalState,finalObjects},
    claim:{result:claimed,replayedByteEqual:true,recoveredByteEqual:true,competingClaim:secondClaim},
    submit:{result:submitted,replayedByteEqual:true,recoveredByteEqual:true,sameJob:true,controlConflict:controlConflict.status,secondGenuineSealSameJob:true,refusalReplayedByteEqual:true},
    load:{...seeded,recoveredByteEqual:true,physical},
    materialization:{count:materialized.count,batches:materialized.batches,planSha256:materialized.plan.sha256,manifestSha256:materialized.manifest.sha256,keys:body.items.map((item:any)=>item.entity.components[0].string),forgedGrant:forgedGrant.outcome},
    seal:{reference:sealed.reference,receipt:sealed.receipt,replayedByteEqual:true,recoveredByteEqual:true,conflict:conflict.outcome,missing:missing.outcome},
    action:{registered:action,forged:forgedAction,previousOpen:oldAction.outcome,reissued:reissuedAction.outcome},
    catalog:{registration:registered.outcome,retry:unchanged.outcome,revision:catalog.catalog.catalogRevision,sourceSha256:catalog.catalog.document.sourceSha256,types:catalog.catalog.types,properties:catalog.catalog.properties,keys:catalog.catalog.keys,changeCount:catalog.catalog.changes.length},
    actionExecution:true,selectionReadGrant:true,crashRecovery:false};
  const encoded=JSON.stringify(receipt,null,2)+'\n';if(Bun.argv[3])await Bun.write(Bun.argv[3],encoded);console.log(encoded);
}finally{await browser.close();server.stop(true);await rm(temporary,{recursive:true,force:true});}
