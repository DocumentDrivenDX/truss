import {applyFrozenBatch,BatchRefusal,type ItemResult} from './batch';
import type {PGlite} from '@electric-sql/pglite';
import type {LocalAction,SelectionReadGrant} from './actions';
import {SealAdmissionRefusal,SealCustodyUnavailable,captureSeal,captureSealReference,type SealReference,type SealRequest,type Artifact,createSealer} from './materialize';
import type {StoreInfo} from './store';
export interface JobRef {namespace:string;id:string}
export type JobReview={state:JobState;manifest:Artifact}|{status:'unsupported';code:'JOB_UNAVAILABLE'};
class JobRefusal extends Error {}
export interface SubmitInput {key:string;reference:SealReference;control:SealRequest}
export interface JobState {status:'queued'|'running'|'reconciling'|'stopped'|'completed';job:JobRef;manifestSha256:string;nextBatch:number;committedBatches:number;unresolvedBatch:number|null;stop:{batch:number;code:string}|null}
export type SubmitResult={status:'submitted';state:JobState}
 |{status:'conflict';code:'TOKEN_REUSE'}
 |{status:'unsupported';code:string}
 |{status:'control-unknown';operation:'submit';control:SealRequest}
 |{status:'control-failure';operation:'submit';control:SealRequest;code:'CONTROL_NONCOMMIT';settlement:'current_attempt_rolled_back'}
 |{status:'unresolved';code:'not_found';operation:'submit';control:SealRequest};
export interface ClaimInput {job:JobRef;control:SealRequest}
export type ClaimResult={status:'claimed';job:JobRef;batch:number;fence:string;leaseUntil:string}
 |{status:'idle';job:JobRef}
 |{status:'unsupported';code:string}
 |{status:'conflict';code:'TOKEN_REUSE'}
 |{status:'control-unknown';operation:'claim';control:SealRequest}
 |{status:'control-failure';operation:'claim';control:SealRequest;code:'CONTROL_NONCOMMIT';settlement:'current_attempt_rolled_back'}
 |{status:'unresolved';code:'not_found';operation:'claim';control:SealRequest};
export function captureClaim(input:ClaimInput):ClaimInput{
 if(!input||Object.keys(input).sort().join(',')!=='control,job')throw Error('Exact claim input required');
 const {job,control}=input;return Object.freeze({job:captureJob(job),control:captureSeal(control)});
}
export interface ExecuteInput {job:JobRef;batch:number;fence:string}
export type BatchOutcome={status:'committed';job:JobRef;batch:number;manifestSha256:string;items:ItemResult[];receipt:Artifact}
 |{status:'conflict'|'rejected';job:JobRef;batch:number;code:string;item:number}
 |{status:'failed';job:JobRef;batch:number;code:string}
 |{status:'indeterminate';job:JobRef;batch:number}
 |{status:'unsupported';code:string};
export function captureExecute(input:ExecuteInput):ExecuteInput{
 if(!input||Object.keys(input).sort().join(',')!=='batch,fence,job')throw Error('Exact execution input required');
 const {job,batch,fence}=input;if(!Number.isInteger(batch)||batch<0||batch>9999||typeof fence!=='string'||!/^[1-9][0-9]{0,63}$/.test(fence))throw Error('Original batch and exact fence required');
 return Object.freeze({job:captureJob(job),batch,fence});
}
const copy=<T>(x:T):T=>JSON.parse(JSON.stringify(x));
const bytes=(s:string)=>new TextEncoder().encode(s);
const hex=(s:string)=>Array.from(bytes(s),x=>x.toString(16).padStart(2,'0')).join('');
const hash=async(s:string)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes(s))),x=>x.toString(16).padStart(2,'0')).join('');
export function captureSubmit(input:SubmitInput):SubmitInput{
 if(!input||Object.keys(input).sort().join(',')!=='control,key,reference')throw Error('Exact local submission required');
 const {key,reference,control}=input;
 if(typeof key!=='string'||!key||bytes(key).length>1024||key.includes('\0')||new TextDecoder().decode(bytes(key))!==key)throw Error('Bounded submission key required');
 return Object.freeze({key,reference:captureSealReference(reference),control:captureSeal(control)});
}
export function captureJob(input:JobRef):JobRef{
 if(!input||Object.keys(input).sort().join(',')!=='id,namespace')throw Error('Exact JobRef required');
 const {namespace,id}=input;for(const s of [namespace,id])if(typeof s!=='string'||!/^[A-Za-z0-9_-]{1,128}$/.test(s))throw Error('Original JobRef required');return Object.freeze({namespace,id});
}
export function createBulk(db:PGlite,info:StoreInfo,sealer:ReturnType<typeof createSealer>,isOpen:()=>boolean,fence:()=>void){
 const jobKey=(job:JobRef)=>'browser:bulk-job:0.1:'+job.namespace+':'+job.id;
 const controlKey=(control:SealRequest)=>'browser:bulk-submit-control:0.1:'+hex(control.requestKey);
 const unknown=(control:SealRequest):SubmitResult=>({status:'control-unknown',operation:'submit',control:copy(control)});
 async function storedControl<T=SubmitResult>(tx:Pick<PGlite,'query'>,key:string,inputUtf8:string,profile='truss-browser-submit-control/0.1'):Promise<T|null>{
  const rows=(await tx.query<{value:any}>('SELECT value FROM truss.setting WHERE key=$1',[key])).rows;
  if(!rows.length)return null;const stored=rows[0]!.value;
  if(stored.profile!==profile||typeof stored.inputUtf8!=='string'||typeof stored.resultUtf8!=='string'||await hash(stored.inputUtf8)!==stored.inputSha256||await hash(stored.resultUtf8)!==stored.resultSha256)throw Error('Original control custody required');
  return stored.inputUtf8===inputUtf8?JSON.parse(stored.resultUtf8) as T:{status:'conflict',code:'TOKEN_REUSE'} as T;
 }
 async function saveControl(tx:Pick<PGlite,'query'>,key:string,inputUtf8:string,result:SubmitResult|ClaimResult,profile='truss-browser-submit-control/0.1'){
  const resultUtf8=JSON.stringify(result);
  await tx.query('INSERT INTO truss.setting(key,value) VALUES($1,$2::jsonb)',[key,JSON.stringify({profile,inputUtf8,inputSha256:await hash(inputUtf8),resultUtf8,resultSha256:await hash(resultUtf8)})]);
 }
 async function readJob(tx:Pick<PGlite,'query'>,job:JobRef){
  if(job.namespace!==info.storeId)throw new JobRefusal('Original local job namespace required');
  const rows=(await tx.query<{value:any}>('SELECT value FROM truss.setting WHERE key=$1',[jobKey(job)])).rows;
  if(!rows.length)throw new JobRefusal('Retained job required');const record=rows[0]!.value;
  if(record.profile!=='truss-browser-bulk-job/0.1'||typeof record.sourceUtf8!=='string'||await hash(record.sourceUtf8)!==record.sourceSha256||typeof record.intentUtf8!=='string'||await hash(record.intentUtf8)!==record.intentSha256||record.state?.job?.namespace!==job.namespace||record.state?.job?.id!==job.id)throw new SealCustodyUnavailable('Original job custody required');return record;
 }
 async function authorizedJob(tx:Pick<PGlite,'query'>,job:JobRef,authorization:{cut:string;actionPin:Record<string,unknown>},action:LocalAction,grant:SelectionReadGrant){
  const record=await readJob(tx,job);let source:any;
  try{source=JSON.parse(record.sourceUtf8);if(typeof source.cut!=='string'||!source.actionPin||!source.reference)throw Error('Original job source shape required');}catch(error){throw new SealCustodyUnavailable(String(error));}
  if(source.cut!==authorization.cut||JSON.stringify(source.actionPin)!==JSON.stringify(authorization.actionPin))throw new JobRefusal('Current original job action/source required');
  let retained;try{retained=await sealer.retained(tx,action,grant,source.reference);}catch(error){throw new SealCustodyUnavailable(String(error));}
  if(record.sourceUtf8!==JSON.stringify(retained.input))throw new SealCustodyUnavailable('Complete original job/seal correspondence required');
  return {record,source};
 }
 const admissionKey=(input:Pick<ExecuteInput,'job'|'batch'>)=>'browser:bulk-admission:0.1:'+input.job.namespace+':'+input.job.id+':'+input.batch;
 const outcomeKey=(input:Pick<ExecuteInput,'job'|'batch'>)=>'browser:bulk-outcome:0.1:'+input.job.namespace+':'+input.job.id+':'+input.batch;
 const indeterminate=(input:Pick<ExecuteInput,'job'|'batch'>):BatchOutcome=>({status:'indeterminate',job:copy(input.job),batch:input.batch});
 async function batchCustody(tx:Pick<PGlite,'query'>,input:ExecuteInput,sourceUtf8:string){
  const rows=(await tx.query<{value:any}>('SELECT value FROM truss.setting WHERE key=$1',[admissionKey(input)])).rows;
  if(!rows.length)return null;const admission=rows[0]!.value;
  if(admission.profile!=='truss-browser-effect-admission/0.1'||typeof admission.inputUtf8!=='string'||typeof admission.sourceUtf8!=='string'||await hash(admission.inputUtf8)!==admission.inputSha256||await hash(admission.sourceUtf8)!==admission.sourceSha256||admission.sourceUtf8!==sourceUtf8)throw new SealCustodyUnavailable('Original effect admission required');
  if(admission.inputUtf8!==JSON.stringify(input))return {result:{status:'unsupported',code:'PAP_FENCE'} as BatchOutcome};
  const outcomes=(await tx.query<{value:any}>('SELECT value FROM truss.setting WHERE key=$1',[outcomeKey(input)])).rows;
  if(!outcomes.length)return {admission,result:indeterminate(input)};
  const stored=outcomes[0]!.value;if(stored.profile!=='truss-browser-batch-outcome/0.1'||stored.admissionId!==admission.id||typeof stored.resultUtf8!=='string'||await hash(stored.resultUtf8)!==stored.resultSha256)throw new SealCustodyUnavailable('Exact original batch outcome required');
  return {admission,result:JSON.parse(stored.resultUtf8) as BatchOutcome};
 }
 async function terminalBatch(tx:Pick<PGlite,'query'>,input:ExecuteInput,record:any,admissionId:string,result:BatchOutcome){
  const resultUtf8=JSON.stringify(result);
  await tx.query('INSERT INTO truss.setting(key,value) VALUES($1,$2::jsonb)',[outcomeKey(input),JSON.stringify({profile:'truss-browser-batch-outcome/0.1',admissionId,resultUtf8,resultSha256:await hash(resultUtf8)})]);
  record.state.unresolvedBatch=null;record.claim=null;
  if(result.status==='committed'){
   record.state.nextBatch=input.batch+1;record.state.committedBatches=input.batch+1;record.state.stop=null;
   record.state.status=record.state.nextBatch===JSON.parse(JSON.parse(record.sourceUtf8).manifest.utf8).batches.length?'completed':'queued';
  }else if(result.status==='conflict'||result.status==='rejected'||result.status==='failed'){
   record.state.status='stopped';record.state.stop={batch:input.batch,code:result.code};
  }else throw new SealCustodyUnavailable('Terminal batch result required');
  await tx.query('UPDATE truss.setting SET value=$2::jsonb WHERE key=$1',[jobKey(input.job),JSON.stringify(record)]);
 }
 async function liveClaim(tx:Pick<PGlite,'query'>,record:any,input:ExecuteInput,admitted:boolean){
  const state=record.state,claim=record.claim;
  if(state.nextBatch!==input.batch||state.committedBatches!==input.batch||claim?.batch!==input.batch||claim?.fence!==input.fence||record.lastFence!==input.fence||claim?.job?.namespace!==input.job.namespace||claim?.job?.id!==input.job.id||state.status!==(admitted?'reconciling':'running')||state.unresolvedBatch!==(admitted?input.batch:null))return false;
  // Lease expiry cannot interrupt the already-admitted serialized transaction.
  return admitted||(await tx.query<{live:boolean}>('SELECT $1::timestamptz>clock_timestamp() AS live',[claim.leaseUntil])).rows[0]!.live;
 }
 return {
  async submit(action:LocalAction,grant:SelectionReadGrant,input:SubmitInput,recovery=false):Promise<SubmitResult>{
   if(!isOpen())return {status:'unsupported',code:'STORE_NOT_OPEN'};
   let inputUtf8:string|undefined;const key=controlKey(input.control);
   const sentinel=Symbol();let callbackFailure:unknown=sentinel;
   try{
    const result=await db.transaction<SubmitResult>(async tx=>{try{
     if(!isOpen())throw Error('Current local owner required');
     const authorization=await sealer.authorize(tx,action,grant);if(authorization.outcome!=='authorized')return {status:'unsupported',code:'ACTION_ADMISSION_REFUSED'};
     inputUtf8=JSON.stringify({profile:'truss-browser-submit/0.1',storeId:info.storeId,incarnation:info.incarnation,authorization,input});
     const prior=await storedControl(tx,key,inputUtf8);if(prior)return prior;
     if(recovery)return {status:'unresolved',code:'not_found',operation:'submit',control:copy(input.control)};
     let seal;try{seal=await sealer.retained(tx,action,grant,input.reference);}catch(error){if(!(error instanceof SealAdmissionRefusal))throw error;const refused:SubmitResult={status:'unsupported',code:'SEAL_ADMISSION_REFUSED'};await saveControl(tx,key,inputUtf8,refused);return refused;}
     const {reference:_sealControl,profile:_sealProfile,...intent}=seal.input;
     const intentUtf8=JSON.stringify(intent);
     const route='browser:bulk-submit-key:0.1:'+hex(input.key),sourceUtf8=JSON.stringify(seal.input);
     const existing=(await tx.query<{value:JobRef}>('SELECT value FROM truss.setting WHERE key=$1',[route])).rows;
     let result:SubmitResult;
     if(existing.length){let record;try{record=await readJob(tx,existing[0]!.value);}catch(error){throw new SealCustodyUnavailable(String(error));}result=record.intentUtf8===intentUtf8?{status:'submitted',state:copy(record.state)}:{status:'conflict',code:'TOKEN_REUSE'};}
     else{
      const body=JSON.parse(seal.input.manifest.utf8),job:JobRef={namespace:info.storeId,id:crypto.randomUUID()};
      const state:JobState={status:body.batches.length?'queued':'completed',job,manifestSha256:seal.input.manifest.sha256,nextBatch:0,committedBatches:0,unresolvedBatch:null,stop:null};
      await tx.query('INSERT INTO truss.setting(key,value) VALUES($1,$2::jsonb)',[jobKey(job),JSON.stringify({profile:'truss-browser-bulk-job/0.1',sourceUtf8,sourceSha256:await hash(sourceUtf8),intentUtf8,intentSha256:await hash(intentUtf8),state})]);
      await tx.query('INSERT INTO truss.setting(key,value) VALUES($1,$2::jsonb)',[route,JSON.stringify(job)]);result={status:'submitted',state};
     }
     await saveControl(tx,key,inputUtf8,result);if(!isOpen())throw Error('Current local owner required');return result;
    }catch(error){callbackFailure=error;throw error;}});
    await db.syncToFs();if(!isOpen()){fence();return unknown(input.control);}return result;
   }catch(error){
    if(recovery||callbackFailure!==error||inputUtf8===undefined||error instanceof SealCustodyUnavailable){fence();return unknown(input.control);}
    // Confirmed rollback is distinct from the original failure-observation commit.
    const result:SubmitResult={status:'control-failure',operation:'submit',control:copy(input.control),code:'CONTROL_NONCOMMIT',settlement:'current_attempt_rolled_back'};
    const retainedInput=inputUtf8;
    try{await db.transaction(async tx=>{const prior=await storedControl(tx,key,retainedInput);if(prior)throw Error('Unexpected concurrent original control');await saveControl(tx,key,retainedInput,result);});await db.syncToFs();if(!isOpen())throw Error('Current local owner required');return result;}catch{fence();return unknown(input.control);}
   }
  },
  async claim(action:LocalAction,grant:SelectionReadGrant,input:ClaimInput,recovery=false):Promise<ClaimResult>{
   if(!isOpen())return {status:'unsupported',code:'STORE_NOT_OPEN'};
   const profile='truss-browser-claim-control/0.1',key='browser:bulk-claim-control:0.1:'+hex(input.control.requestKey);
   const unknown=():ClaimResult=>({status:'control-unknown',operation:'claim',control:copy(input.control)});
   let inputUtf8:string|undefined;const sentinel=Symbol();let callbackFailure:unknown=sentinel;
   try{
    const result=await db.transaction<ClaimResult>(async tx=>{try{
     const authorization=await sealer.authorize(tx,action,grant);if(authorization.outcome!=='authorized')return {status:'unsupported',code:'ACTION_ADMISSION_REFUSED'};
     inputUtf8=JSON.stringify({profile:'truss-browser-claim/0.1',operation:'claim',storeId:info.storeId,incarnation:info.incarnation,authorization,input});
     const prior=await storedControl<ClaimResult>(tx,key,inputUtf8,profile);if(prior)return prior;
     if(recovery)return {status:'unresolved',code:'not_found',operation:'claim',control:copy(input.control)};
     let result:ClaimResult,record:any;
     try{
      const admitted=await authorizedJob(tx,input.job,authorization,action,grant);record=admitted.record;const source=admitted.source;
      const body=JSON.parse(source.manifest.utf8),state=record.state;
      if(!Number.isInteger(state.nextBatch)||state.nextBatch<0||state.nextBatch>body.batches.length||state.committedBatches!==state.nextBatch||state.manifestSha256!==source.manifest.sha256)throw new SealCustodyUnavailable('Original contiguous job progress required');
      if(state.status==='completed'){
       if(state.nextBatch!==body.batches.length)throw new SealCustodyUnavailable('Complete original job progress required');result={status:'idle',job:copy(input.job)};
      }else if(state.status==='stopped')result={status:'unsupported',code:'PAP_ORDER'};
      else if(state.status==='running'||state.status==='reconciling'){
       const active=record.claim;if(!active||active.status!=='claimed'||active.job?.namespace!==input.job.namespace||active.job?.id!==input.job.id||active.batch!==state.nextBatch||typeof active.fence!=='string'||!/^[1-9][0-9]{0,63}$/.test(active.fence)||active.fence!==record.lastFence||typeof active.leaseUntil!=='string')throw new SealCustodyUnavailable('Original active claim required');
       result={status:'unsupported',code:state.status==='reconciling'?'PAP_RECOVERY':'PAP_FENCE'};
      }
      else if(state.status!=='queued'||state.nextBatch>=body.batches.length)throw new SealCustodyUnavailable('Original queued batch required');
      else{
       if(record.claim!==undefined&&record.claim!==null)throw new SealCustodyUnavailable('Queued job must have no active claim');
       const old=record.lastFence??'0';if(typeof old!=='string'||!/^(0|[1-9][0-9]{0,63})$/.test(old))throw new SealCustodyUnavailable('Original exact fence required');
       const next=(BigInt(old)+1n).toString();if(next.length>64)result={status:'unsupported',code:'FENCE_EXHAUSTED'};
       else{
        const lease=(await tx.query<{until:string}>("SELECT to_char((clock_timestamp()+interval '60 seconds') AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"') AS until")).rows[0]!.until;
        result={status:'claimed',job:copy(input.job),batch:state.nextBatch,fence:next,leaseUntil:lease};
        record.lastFence=next;record.claim=copy(result);record.state.status='running';
        await tx.query('UPDATE truss.setting SET value=$2::jsonb WHERE key=$1',[jobKey(input.job),JSON.stringify(record)]);
       }
      }
     }catch(error){if(error instanceof JobRefusal||error instanceof SealAdmissionRefusal)result={status:'unsupported',code:'JOB_UNAVAILABLE'};else throw error;}
     await saveControl(tx,key,inputUtf8,result,profile);if(!isOpen())throw Error('Current local owner required');return result;
    }catch(error){callbackFailure=error;throw error;}});
    await db.syncToFs();if(!isOpen()){fence();return unknown();}return result;
   }catch(error){
    if(recovery||callbackFailure!==error||inputUtf8===undefined||error instanceof SealCustodyUnavailable){fence();return unknown();}
    const result:ClaimResult={status:'control-failure',operation:'claim',control:copy(input.control),code:'CONTROL_NONCOMMIT',settlement:'current_attempt_rolled_back'},retainedInput=inputUtf8;
    try{await db.transaction(async tx=>{const prior=await storedControl<ClaimResult>(tx,key,retainedInput,profile);if(prior)throw Error('Unexpected original claim control');await saveControl(tx,key,retainedInput,result,profile);});await db.syncToFs();if(!isOpen())throw Error('Current local owner required');return result;}catch{fence();return unknown();}
   }
  },
  async execute(action:LocalAction,grant:SelectionReadGrant,input:ExecuteInput,recovery=false):Promise<BatchOutcome>{
   if(!isOpen())return {status:'unsupported',code:'STORE_NOT_OPEN'};
   let dispatch:{id:string;sourceUtf8:string}|undefined;
   try{
    const admission=await db.transaction(async tx=>{
     const authorization=await sealer.authorize(tx,action,grant);if(authorization.outcome!=='authorized')return {status:'unsupported',code:'ACTION_ADMISSION_REFUSED'} as BatchOutcome;
     let record:any;try{record=(await authorizedJob(tx,input.job,authorization,action,grant)).record;}catch(error){if(error instanceof JobRefusal)return {status:'unsupported',code:'JOB_UNAVAILABLE'} as BatchOutcome;throw error;}
     const prior=await batchCustody(tx,input,record.sourceUtf8);if(prior)return prior.result;
     if(recovery)return indeterminate(input);
     if(!await liveClaim(tx,record,input,false))return {status:'unsupported',code:'PAP_FENCE'} as BatchOutcome;
     const id=crypto.randomUUID(),inputUtf8=JSON.stringify(input),sourceUtf8=record.sourceUtf8;
     await tx.query('INSERT INTO truss.setting(key,value) VALUES($1,$2::jsonb)',[admissionKey(input),JSON.stringify({profile:'truss-browser-effect-admission/0.1',id,inputUtf8,inputSha256:await hash(inputUtf8),sourceUtf8,sourceSha256:await hash(sourceUtf8)})]);
     record.state.status='reconciling';record.state.unresolvedBatch=input.batch;
     await tx.query('UPDATE truss.setting SET value=$2::jsonb WHERE key=$1',[jobKey(input.job),JSON.stringify(record)]);
     return {dispatch:{id,sourceUtf8}};
    });
    // No business callback is invoked until original admission commit AND flush.
    await db.syncToFs();if(!isOpen()){fence();return indeterminate(input);}
    if(!('dispatch' in admission))return admission;dispatch=admission.dispatch;
   }catch{fence();return indeterminate(input);}
   const sentinel=Symbol();let callbackFailure:unknown=sentinel;
   try{
    const result=await db.transaction<BatchOutcome>(async tx=>{try{
     const authorization=await sealer.authorize(tx,action,grant);if(authorization.outcome!=='authorized')throw new BatchRefusal('rejected','ACTION_ADMISSION_REFUSED',0);
     const {record,source}=await authorizedJob(tx,input.job,authorization,action,grant),custody=await batchCustody(tx,input,record.sourceUtf8);
     if(!custody?.admission||custody.admission.id!==dispatch!.id||record.sourceUtf8!==dispatch!.sourceUtf8||custody.result.status!=='indeterminate')throw new SealCustodyUnavailable('Original dispatched admission required');
     if(!await liveClaim(tx,record,input,true))throw new BatchRefusal('rejected','PAP_FENCE',0);
     await tx.exec("SET LOCAL statement_timeout='5000ms'");
     const applied=await applyFrozenBatch(tx,info,source,input.job,input.batch);
     if(!isOpen()||!await liveClaim(tx,record,input,true))throw new BatchRefusal('rejected','PAP_FENCE',0);
     const result:BatchOutcome={status:'committed',job:copy(input.job),batch:input.batch,manifestSha256:source.manifest.sha256,items:applied.items,receipt:applied.receipt};
     await terminalBatch(tx,input,record,dispatch!.id,result);return result;
    }catch(error){callbackFailure=error;throw error;}});
    await db.syncToFs();if(!isOpen()){fence();return indeterminate(input);}return result;
   }catch(error){
    if(callbackFailure!==error||error instanceof SealCustodyUnavailable){fence();return indeterminate(input);}
    // This exact callback error is observed only after the original rollback ACK.
    const result:BatchOutcome=error instanceof BatchRefusal?{status:error.status,job:copy(input.job),batch:input.batch,code:error.code,item:error.item}:{status:'failed',job:copy(input.job),batch:input.batch,code:'BATCH_ROLLED_BACK'};
    try{
     await db.transaction(async tx=>{
      const authorization=await sealer.authorize(tx,action,grant);if(authorization.outcome!=='authorized')throw Error('Current original action required');
      const {record}=await authorizedJob(tx,input.job,authorization,action,grant),custody=await batchCustody(tx,input,record.sourceUtf8);
      if(!custody?.admission||custody.admission.id!==dispatch!.id||custody.result.status!=='indeterminate')throw Error('Original rolled-back admission required');
      await terminalBatch(tx,input,record,dispatch!.id,result);
     });await db.syncToFs();if(!isOpen())throw Error('Current open store required');return result;
    }catch{fence();return indeterminate(input);}
   }
  },
  async status(action:LocalAction,grant:SelectionReadGrant,job:JobRef):Promise<JobReview>{
   if(!isOpen())throw Error('Current local owner required');
   try{const authorization=await sealer.authorize(db,action,grant);if(authorization.outcome!=='authorized')return {status:'unsupported',code:'JOB_UNAVAILABLE'};const {record,source}=await authorizedJob(db,job,authorization,action,grant);if(!isOpen())throw Error('Current local owner required');return {state:copy(record.state),manifest:copy(source.manifest)};}catch(error){if(error instanceof JobRefusal||error instanceof SealAdmissionRefusal)return {status:'unsupported',code:'JOB_UNAVAILABLE'};fence();throw error;}
  }
 };
}
