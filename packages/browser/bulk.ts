import type {PGlite} from '@electric-sql/pglite';
import type {LocalAction,SelectionReadGrant} from './actions';
import {SealAdmissionRefusal,SealCustodyUnavailable,captureSeal,captureSealReference,type SealReference,type SealRequest,type Artifact,createSealer} from './materialize';
import type {StoreInfo} from './store';
export interface JobRef {namespace:string;id:string}
export type JobReview={state:JobState;manifest:Artifact}|{status:'unsupported';code:'JOB_UNAVAILABLE'};
class JobRefusal extends Error {}
export interface SubmitInput {key:string;reference:SealReference;control:SealRequest}
export interface JobState {status:'queued'|'completed';job:JobRef;manifestSha256:string;nextBatch:number;committedBatches:number;unresolvedBatch:null;stop:null}
export type SubmitResult={status:'submitted';state:JobState}
 |{status:'conflict';code:'TOKEN_REUSE'}
 |{status:'unsupported';code:string}
 |{status:'control-unknown';operation:'submit';control:SealRequest}
 |{status:'control-failure';operation:'submit';control:SealRequest;code:'CONTROL_NONCOMMIT';settlement:'current_attempt_rolled_back'}
 |{status:'unresolved';code:'not_found';operation:'submit';control:SealRequest};
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
 async function storedControl(tx:Pick<PGlite,'query'>,key:string,inputUtf8:string){
  const rows=(await tx.query<{value:any}>('SELECT value FROM truss.setting WHERE key=$1',[key])).rows;
  if(!rows.length)return null;const stored=rows[0]!.value;
  if(stored.profile!=='truss-browser-submit-control/0.1'||typeof stored.inputUtf8!=='string'||typeof stored.resultUtf8!=='string'||await hash(stored.inputUtf8)!==stored.inputSha256||await hash(stored.resultUtf8)!==stored.resultSha256)throw Error('Original control custody required');
  return stored.inputUtf8===inputUtf8?JSON.parse(stored.resultUtf8) as SubmitResult:{status:'conflict',code:'TOKEN_REUSE'} as SubmitResult;
 }
 async function saveControl(tx:Pick<PGlite,'query'>,key:string,inputUtf8:string,result:SubmitResult){
  const resultUtf8=JSON.stringify(result);
  await tx.query('INSERT INTO truss.setting(key,value) VALUES($1,$2::jsonb)',[key,JSON.stringify({profile:'truss-browser-submit-control/0.1',inputUtf8,inputSha256:await hash(inputUtf8),resultUtf8,resultSha256:await hash(resultUtf8)})]);
 }
 async function readJob(tx:Pick<PGlite,'query'>,job:JobRef){
  if(job.namespace!==info.storeId)throw new JobRefusal('Original local job namespace required');
  const rows=(await tx.query<{value:any}>('SELECT value FROM truss.setting WHERE key=$1',[jobKey(job)])).rows;
  if(!rows.length)throw new JobRefusal('Retained job required');const record=rows[0]!.value;
  if(record.profile!=='truss-browser-bulk-job/0.1'||typeof record.sourceUtf8!=='string'||await hash(record.sourceUtf8)!==record.sourceSha256||typeof record.intentUtf8!=='string'||await hash(record.intentUtf8)!==record.intentSha256||record.state.job.namespace!==job.namespace||record.state.job.id!==job.id)throw new SealCustodyUnavailable('Original job custody required');return record;
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
  async status(action:LocalAction,grant:SelectionReadGrant,job:JobRef):Promise<JobReview>{
   if(!isOpen())throw Error('Current local owner required');
   try{const authorization=await sealer.authorize(db,action,grant);if(authorization.outcome!=='authorized')return {status:'unsupported',code:'JOB_UNAVAILABLE'};const record=await readJob(db,job),source=JSON.parse(record.sourceUtf8);const retained=await sealer.retained(db,action,grant,source.reference);if(record.sourceUtf8!==JSON.stringify(retained.input))throw Error('Complete original job/seal correspondence required');if(!isOpen())throw Error('Current local owner required');return {state:copy(record.state),manifest:copy(source.manifest)};}catch(error){if(error instanceof JobRefusal||error instanceof SealAdmissionRefusal)return {status:'unsupported',code:'JOB_UNAVAILABLE'};fence();throw error;}
  }
 };
}
