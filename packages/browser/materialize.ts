import * as umf from '@truss/umf-local-actions';
import * as weft from '@truss/weft-local';
import type {PGlite} from '@electric-sql/pglite';
import scalarsSql from '../python/src/truss/_catalog_runtime/scalars.sql' with {type:'text'};
import {readCatalog,type CatalogSnapshot} from './catalog';
import {createActionIssuer,type LocalAction,type SelectionReadGrant} from './actions';
import type {StoreInfo} from './store';
export interface Artifact {mediaType:string;utf8:string;sha256:string}
declare const workBrand:unique symbol;
export interface FrozenWork {readonly [workBrand]:true}
export interface MaterializeInput {sql:string;parameters:Record<string,{string:string}>;batchSize:number;maxItems:number}
export interface Materialization {work:FrozenWork;plan:Artifact;manifest:Artifact;count:number;batches:{ordinal:number;start:number;count:number}[]}
const copy=<T>(x:T):T=>JSON.parse(JSON.stringify(x));
const bytes=(x:unknown)=>new TextEncoder().encode(typeof x==='string'?x:JSON.stringify(x));
const hash=async(x:string)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes(x)))).map(n=>n.toString(16).padStart(2,'0')).join('');
const positive=(s:unknown):s is string=>typeof s==='string'&&/^[1-9][0-9]{0,18}$/.test(s)&&BigInt(s)<=9223372036854775807n;
let wasmReady:Promise<unknown>|undefined;
export function captureMaterialize(input:MaterializeInput):Readonly<MaterializeInput>{
 if(!input||Object.keys(input).sort().join(',')!=='batchSize,maxItems,parameters,sql')throw Error('Exact materialization input required');
 const {sql,batchSize,maxItems,parameters}=input;
 if(typeof sql!=='string'||bytes(sql).length>65536||sql.includes('\0')||new TextDecoder().decode(bytes(sql))!==sql
  ||!Number.isInteger(batchSize)||batchSize<1||batchSize>100||!Number.isInteger(maxItems)||maxItems<1||maxItems>10000
  ||!parameters||typeof parameters!=='object'||Array.isArray(parameters)||Object.keys(parameters).length>64)throw Error('Bounded materialization input required');
 const captured:Record<string,{string:string}>=Object.create(null);
 for(const [name,value] of Object.entries(parameters)){
  if(!name||name.length>256||!value||Object.keys(value).join(',')!=='string'||typeof value.string!=='string'||value.string.includes('\0')||new TextDecoder().decode(bytes(value.string))!==value.string)throw Error('Exact String parameters required');
  captured[name]=Object.freeze({string:value.string});
 }
 if(bytes(captured).length>1048576)throw Error('Parameter input limit');
 return Object.freeze({sql,batchSize,maxItems,parameters:Object.freeze(captured)});
}
const definitions=async(tx:Pick<PGlite,'query'>)=>(await tx.query<{name:string;definition:string}>("SELECT p.proname AS name,pg_get_functiondef(p.oid) AS definition FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss' AND p.proname IN ('valid_scalar_cell','logical_scalar_cell','valid_scalar_property') ORDER BY p.proname,pg_get_function_identity_arguments(p.oid)")).rows;
async function ensureScalars(tx:Pick<PGlite,'query'|'exec'>){
 const digest=await hash(scalarsSql);
 if(digest!=='03fd6a50ed7676e855959fb80887a8c733f3965b5958fda632967e3b961d244c')throw Error('Original scalar helper required');
 const prior=(await tx.query<{value:any}>("SELECT value FROM truss.setting WHERE key='browser:scalars:0.1'")).rows;
 let actual=await definitions(tx);
 if(prior.length===0){
  if(actual.length)throw Error('Partial or foreign scalar helper installation');
  await tx.exec(scalarsSql);actual=await definitions(tx);
  if(actual.length!==3)throw Error('Complete scalar helper installation required');
  await tx.query("INSERT INTO truss.setting(key,value) VALUES('browser:scalars:0.1',$1::jsonb)",[JSON.stringify({profile:'truss-browser-scalars/0.1',sourceSha256:digest,definitions:actual})]);
 }else if(prior.length!==1||prior[0]!.value.profile!=='truss-browser-scalars/0.1'||prior[0]!.value.sourceSha256!==digest||JSON.stringify(prior[0]!.value.definitions)!==JSON.stringify(actual))throw Error('Original scalar helper correspondence required');
}
interface RetainedWork {action:LocalAction;grant:SelectionReadGrant;cut:string;manifest:Artifact;plan:Artifact;keyReceipts:any[];rows:any[];context:any}
export function createMaterializer(db:PGlite,info:StoreInfo,issuer:ReturnType<typeof createActionIssuer>,isOpen:()=>boolean,fence:()=>void){
 const works=new WeakMap<FrozenWork,RetainedWork>();
 const open=()=>{if(!isOpen())throw Error('Current open store required');};
 return Object.freeze({
  async materialize(action:LocalAction,grant:SelectionReadGrant,input:Readonly<MaterializeInput>):Promise<Materialization>{
   open();let catalog:CatalogSnapshot|null;
   try{catalog=await readCatalog(db);}catch(error){fence();throw error;}
   const original=issuer.requireGrant(catalog,action,grant);
   await (wasmReady??=weft.default());open();
   const compiler=new weft.MutationCompiler(JSON.stringify({actions:[{pin:original.actionPin,snapshot:original.model,preparation:original.preparation}],selectionBackends:[]}));
   try{
    const request={interfaceVersion:'weft-mutation-compile/0.1.0',dialect:'weft-mutation/0.1.0',sql:input.sql,parameters:input.parameters,model:original.model,modelPin:original.modelPin,action:original.actionPin,target:original.target,selectionProfile:{id:'weft.update-selection',version:'1'},batchSize:input.batchSize,limits:{maxItems:input.maxItems,maxManifestBytes:16777216}};
    const compiled=JSON.parse(compiler.compile_json(JSON.stringify(request)));
    if(compiled.status!=='compiled')throw Error('Original Weft compilation refused: '+JSON.stringify(compiled.diagnostics));
    const planArtifact:Artifact=compiled.plan,plan=JSON.parse(planArtifact.utf8),source=JSON.parse(original.model.utf8);
    const types=(catalog!.types as any[]).filter(t=>t.moduleId===original.target.module&&t.recordId===original.target.element&&t.documentId===original.modelPin.documentId);
    if(types.length!==1)throw Error('Exact catalog target required');const type=types[0];
    const fields=original.fields.map(f=>{const matches=(catalog!.properties as any[]).filter(p=>p.typeId===type.typeId&&p.moduleId===f.module&&p.fieldId===f.element);if(matches.length!==1)throw Error('Original catalog member required');return {identity:{documentId:original.modelPin.documentId,revision:original.modelPin.revision,...f},propertyId:matches[0].propertyId};});
    const keys=(catalog!.keys as any[]).filter(k=>k.typeId===type.typeId&&k.keyId===original.target.key&&k.primary);
    if(keys.length!==1)throw Error('Original primary Key required');
    for(const dependency of [...plan.selection.dependencies,...plan.inputs.assignments.map((a:any)=>a.field)])if(!original.fields.some(f=>f.module===dependency.module&&f.element===dependency.element))throw Error('Selection dependency outside issued read grant');
    const bindingValue={interfaceVersion:'truss-browser-binding/0.1',pgliteVersion:'0.5.10',postgresqlVersion:'18.6',store:info,catalogRevision:catalog!.catalogRevision,document:original.modelPin,maximumScanRows:10000,record:{identity:{documentId:original.modelPin.documentId,revision:original.modelPin.revision,module:type.moduleId,element:type.recordId},typeId:type.typeId,fields,key:{keyId:keys[0].keyId,propertyIds:keys[0].propertyIds}}};
    const bindingText=JSON.stringify(bindingValue),binding={mediaType:'application/json',utf8:bindingText,sha256:await hash(bindingText)};
    const handle=compiler.register_browser_selection(JSON.stringify({model:original.model,modelPin:original.modelPin,binding}));
    const lowered=JSON.parse(compiler.lower_selection_json(handle,JSON.stringify({selection:plan.selection.artifact,model:original.model,binding,maxItems:input.maxItems})));
    if(lowered.status!=='lowered')throw Error('Original Weft lowering refused: '+JSON.stringify(lowered.diagnostics));
    const dependencies=copy(plan.selection.dependencies),selectedArtifact=copy(plan.selection.artifact),target=copy(original.target),sourceIdentity=JSON.stringify(source);
    const context={...original.context,selections:[{profile:{id:'weft.update-selection',version:'1'},inspect:(artifact:any,model:any,key:any)=>{
     const eligible=artifact&&Object.keys(artifact).sort().join(',')==='mediaType,sha256,utf8'&&artifact.mediaType===selectedArtifact.mediaType&&artifact.utf8===selectedArtifact.utf8&&artifact.sha256===selectedArtifact.sha256&&JSON.stringify(model)===sourceIdentity&&JSON.stringify(key)===JSON.stringify(target);
     return {eligible:!!eligible,dependencies:eligible?copy(dependencies):[],diagnostics:eligible?[]:[{code:'WFT_SELECTION_CUSTODY',path:'',message:'Exact original compiled and lowered selection required'}]};
    }}]};
    const parameters=(items:any[])=>items.map(p=>{if(!p.value||Object.keys(p.value).join(',')!=='string'||typeof p.value.string!=='string')throw Error('Original String SQL parameter required');return p.value.string;});
    let constructed:any,selectedRows:any[]=[];
    const noCallbackFailure=Symbol();let callbackFailure:unknown=noCallbackFailure;
    try{
     await db.transaction(async tx=>{
      try{
      open();issuer.requireGrant(await readCatalog(tx),action,grant);
      await tx.exec("SET LOCAL statement_timeout='5000ms'");await ensureScalars(tx);
      for(const preflight of lowered.preflight){const result=(await tx.query<{violations:string}>(preflight.sql,parameters(preflight.parameters))).rows;if(result.length!==1||result[0]!.violations!=='0')throw Error('Complete population preflight refused');}
      const size=(await tx.query<{n:string}>('SELECT coalesce(sum(octet_length(props::text)),0)::text AS n FROM truss.object WHERE type_id=$1::int',[type.typeId])).rows[0]!.n;
      if(!/^[0-9]+$/.test(size)||BigInt(size)>8388608n)throw Error('Logical target byte limit');
      selectedRows=(await tx.query(lowered.sql,parameters(lowered.parameters))).rows;
      if(selectedRows.length>input.maxItems)throw Error('Complete selection exceeds maxItems');
      if(selectedRows.length*(bytes(sourceIdentity).length+4096)+Number(size)>16777216)throw Error('Original key receipt size limit');
      const xid=(await tx.query<{xid:string}>('SELECT pg_current_xact_id()::text AS xid')).rows[0]!.xid;
      if(!positive(xid))throw Error('Original transaction cut required');
      const rows=selectedRows.map(row=>{
       if(Object.keys(row).sort().join(',')!=='identity,key0,version'||!positive(row.identity)||!positive(row.version)||typeof row.key0!=='string')throw Error('Original typed identity/version/Key required');
       const keyReceipt=umf.encodeCoreKeyTuple(source,target,[{string:row.key0}]);
       return {entity:{key:copy(target),components:[{string:row.key0}]},guard:{profile:{id:'truss-browser-object-version',version:'1'},store:info.storeId,epoch:info.incarnation,identity:row.identity,version:row.version},keyReceipt};
      });
      constructed=umf.constructActionManifest({plan:planArtifact,action:{target:{module:(original.actionPin.identity as any).module,action:(original.actionPin.identity as any).action,revision:original.modelPin.revision},documentSha256:original.model.sha256,invocation:{id:'umf.actions.local-tx',version:'1'}},basis:{profile:{id:'truss-browser-store-cut',version:'1'},store:info.storeId,epoch:info.incarnation,cut:catalog!.catalogRevision+':'+xid+':'+binding.sha256,selectionSha256:plan.selection.artifact.sha256},rows},context);
      if(!umf.inspectActionManifest(constructed.artifact,context).eligible)throw Error('Original manifest inspection refused');
      issuer.requireGrant(await readCatalog(tx),action,grant);open();
      }catch(error){callbackFailure=error;throw error;}
     });
     await db.syncToFs();
    }catch(error){if(callbackFailure!==error)fence();throw error;}
    open();const work=Object.freeze(Object.create(null)) as FrozenWork;
    const manifest:Artifact=copy(constructed.artifact),body=JSON.parse(manifest.utf8);
    works.set(work,{action,grant,cut:original.cut,manifest,plan:copy(planArtifact),keyReceipts:copy(constructed.keyReceipts),rows:copy(selectedRows),context});
    return {work,plan:copy(planArtifact),manifest:copy(manifest),count:body.items.length,batches:copy(body.batches)};
   }finally{compiler.free();}
  },
  original(catalog:CatalogSnapshot|null,action:LocalAction,grant:SelectionReadGrant,work:FrozenWork){
   open();const current=issuer.requireGrant(catalog,action,grant),value=works.get(work);
   if(!value||value.action!==action||value.grant!==grant||value.cut!==current.cut)throw Error('Current original materialization required');
   return value;
  }
 });
}

export interface SealRequest {requestKey:string;attempt:string}
export interface SealReference {profile:'truss-browser-seal-reference/0.1';storeId:string;incarnation:string;requestKey:string;attempt:string;manifestSha256:string;planSha256:string;modelSha256:string}
export type SealOutcome={outcome:'sealed';reference:SealReference;manifest:Artifact;receipt:Artifact}
 |{outcome:'conflict';code:'request_key_conflict';reference:SealReference}
 |{outcome:'unknown';code:'storage_outcome_unknown';reference:SealReference}
 |{outcome:'unresolved';code:'not_found';reference:SealReference}
 |{outcome:'refused';code:string;control:SealRequest;reason:string}
 |{outcome:'failure';code:string;control:SealRequest;reference?:SealReference;sqlState?:string;reason:string;settlement:'not_dispatched'|'current_attempt_rolled_back'};
export function captureSeal(input:SealRequest):Readonly<SealRequest>{
 if(!input||Object.keys(input).sort().join(',')!=='attempt,requestKey')throw Error('Original stable seal key and attempt required');
 const {requestKey,attempt}=input;
 for(const text of [requestKey,attempt])if(typeof text!=='string'||!text||bytes(text).length>256||text.includes('\0')||new TextDecoder().decode(bytes(text))!==text)throw Error('Bounded original seal identity required');
 return Object.freeze({requestKey,attempt});
}
export function captureSealReference(input:SealReference):SealReference{
 if(!input||Object.keys(input).sort().join(',')!=='attempt,incarnation,manifestSha256,modelSha256,planSha256,profile,requestKey,storeId'||input.profile!=='truss-browser-seal-reference/0.1')throw Error('Exact original seal reference required');
 const identity=captureSeal({requestKey:input.requestKey,attempt:input.attempt});
 if([input.manifestSha256,input.planSha256,input.modelSha256].some(s=>typeof s!=='string'||!/^[0-9a-f]{64}$/.test(s))||[input.storeId,input.incarnation].some(s=>typeof s!=='string'||s.length!==36))throw Error('Original store/source seal reference required');
 return Object.freeze({...input,...identity});
}
const sealKey=(requestKey:string)=>'browser:seal:0.1:'+Array.from(bytes(requestKey),b=>b.toString(16).padStart(2,'0')).join('');
export function createSealer(db:PGlite,info:StoreInfo,issuer:ReturnType<typeof createActionIssuer>,materializer:ReturnType<typeof createMaterializer>,isOpen:()=>boolean,fence:()=>void){
 const open=()=>{if(!isOpen())throw Error('Current open store required');};
 const readOriginal=async(tx:Pick<PGlite,'query'>,reference:SealReference)=>{
  const found=(await tx.query<{value:any}>('SELECT value FROM truss.setting WHERE key=$1',[sealKey(reference.requestKey)])).rows;
  if(found.length===0)return null;if(found.length!==1)throw Error('Unambiguous original seal required');
  const stored=found[0]!.value;
  if(stored.profile!=='truss-browser-seal/0.1'||typeof stored.inputUtf8!=='string'||typeof stored.outcomeUtf8!=='string'||await hash(stored.inputUtf8)!==stored.inputSha256||await hash(stored.outcomeUtf8)!==stored.outcomeSha256)throw Error('Original sealed custody integrity required');
  const input=JSON.parse(stored.inputUtf8),outcome=JSON.parse(stored.outcomeUtf8) as Extract<SealOutcome,{outcome:'sealed'}>;
  if(outcome.outcome!=='sealed'||!outcome.receipt||await hash(outcome.receipt.utf8)!==outcome.receipt.sha256||await hash(outcome.manifest.utf8)!==outcome.manifest.sha256)throw Error('Original seal outcome integrity required');
  const receipt=JSON.parse(outcome.receipt.utf8);
  if(input.profile!=='truss-browser-seal/0.1'||receipt.profile!=='truss-browser-seal-receipt/0.1'||receipt.inputSha256!==stored.inputSha256
   ||!matches(input.reference,outcome.reference)||!matches(receipt.reference,outcome.reference)
   ||JSON.stringify(input.manifest)!==JSON.stringify(outcome.manifest)||outcome.manifest.sha256!==outcome.reference.manifestSha256
   ||input.plan?.sha256!==outcome.reference.planSha256||input.model?.sha256!==outcome.reference.modelSha256
   ||await hash(input.plan.utf8)!==input.plan.sha256||await hash(input.model.utf8)!==input.model.sha256||await hash(input.preparation.utf8)!==input.preparation.sha256)throw Error('Complete original seal correspondence required');
  return {stored,input,outcome};
 };
 const matches=(a:SealReference,b:SealReference)=>['profile','storeId','incarnation','requestKey','attempt','manifestSha256','planSha256','modelSha256'].every(k=>(a as any)?.[k]===(b as any)?.[k]);
 return Object.freeze({
  async seal(action:LocalAction,grant:SelectionReadGrant,work:FrozenWork,request:Readonly<SealRequest>):Promise<SealOutcome>{
   let catalog:CatalogSnapshot|null,original:ReturnType<typeof issuer.requireGrant>,frozen:ReturnType<typeof materializer.original>;
   if(!isOpen())return {outcome:'refused',code:'store_not_open',control:copy(request),reason:'Current open store required'};
   try{catalog=await readCatalog(db);}catch(error){fence();return {outcome:'failure',code:'admission_failed',control:copy(request),reason:String(error),settlement:'not_dispatched'};}
   try{original=issuer.requireGrant(catalog,action,grant);frozen=materializer.original(catalog,action,grant,work);}catch(error){return {outcome:'refused',code:'admission_refused',control:copy(request),reason:String(error)};}
   const reference:SealReference={profile:'truss-browser-seal-reference/0.1',storeId:info.storeId,incarnation:info.incarnation,requestKey:request.requestKey,attempt:request.attempt,manifestSha256:frozen.manifest.sha256,planSha256:frozen.plan.sha256,modelSha256:original.model.sha256};
   // Capture the complete original control input before dispatch; keep strings intact in JSONB.
   const inputUtf8=JSON.stringify({profile:'truss-browser-seal/0.1',reference,cut:original.cut,model:original.model,modelPin:original.modelPin,actionPin:original.actionPin,preparation:original.preparation,plan:frozen.plan,manifest:frozen.manifest,keyReceipts:frozen.keyReceipts,rows:frozen.rows}),inputSha256=await hash(inputUtf8);
   if(bytes(inputUtf8).length>33554432)return {outcome:'refused',code:'input_limit',control:copy(request),reason:'Original seal input byte limit'};
   const noCallbackFailure=Symbol();let callbackFailure:unknown=noCallbackFailure;
   try{
    const outcome=await db.transaction<SealOutcome>(async tx=>{
     try{
     open();issuer.requireGrant(await readCatalog(tx),action,grant);
     const existing=await readOriginal(tx,reference);
     if(existing)return existing.stored.inputUtf8===inputUtf8&&matches(existing.outcome.reference,reference)?copy(existing.outcome):{outcome:'conflict',code:'request_key_conflict',reference};
     const xid=(await tx.query<{xid:string}>('SELECT pg_current_xact_id()::text AS xid')).rows[0]!.xid;if(!positive(xid))throw Error('Original seal writer required');
     const receiptUtf8=JSON.stringify({profile:'truss-browser-seal-receipt/0.1',reference,inputSha256,writerXid:xid,manifestSha256:frozen.manifest.sha256});
     const outcome:Extract<SealOutcome,{outcome:'sealed'}>={outcome:'sealed',reference,manifest:copy(frozen.manifest),receipt:{mediaType:'application/json',utf8:receiptUtf8,sha256:await hash(receiptUtf8)}};
     const outcomeUtf8=JSON.stringify(outcome);
     await tx.query('INSERT INTO truss.setting(key,value) VALUES($1,$2::jsonb)',[sealKey(request.requestKey),JSON.stringify({profile:'truss-browser-seal/0.1',inputUtf8,inputSha256,outcomeUtf8,outcomeSha256:await hash(outcomeUtf8)})]);
     open();issuer.requireGrant(await readCatalog(tx),action,grant);return outcome;
     }catch(error){callbackFailure=error;throw error;}
    });
    await db.syncToFs();open();return outcome;
   }catch(error){
    // PGlite rethrows this exact callback error only after awaited ROLLBACK succeeds.
    if(callbackFailure===error)return {outcome:'failure',code:'seal_transaction_failed',control:copy(request),reference,sqlState:typeof (error as any)?.code==='string'?(error as any).code:undefined,reason:String(error),settlement:'current_attempt_rolled_back'};
    fence();return {outcome:'unknown',code:'storage_outcome_unknown',reference};
   }
  },
  async recover(action:LocalAction,grant:SelectionReadGrant,reference:SealReference):Promise<SealOutcome>{
   let original:ReturnType<typeof issuer.requireGrant>,catalog:CatalogSnapshot|null;
   if(!isOpen())return {outcome:'refused',code:'store_not_open',control:{requestKey:reference.requestKey,attempt:reference.attempt},reason:'Current open store required'};
   try{catalog=await readCatalog(db);}catch{fence();return {outcome:'unknown',code:'storage_outcome_unknown',reference:copy(reference)};}
   try{original=issuer.requireGrant(catalog,action,grant);}catch(error){return {outcome:'refused',code:'recovery_admission_refused',control:{requestKey:reference.requestKey,attempt:reference.attempt},reason:String(error)};}
   if(reference.storeId!==info.storeId||reference.incarnation!==info.incarnation||reference.modelSha256!==original.model.sha256)return {outcome:'refused',code:'reference_scope_mismatch',control:{requestKey:reference.requestKey,attempt:reference.attempt},reason:'Original seal store/source required'};
   try{
   const found=await readOriginal(db,reference);open();
   if(!found)return {outcome:'unresolved',code:'not_found',reference:copy(reference)};
   if(!matches(found.outcome.reference,reference)||found.input.cut!==original.cut||JSON.stringify(found.input.actionPin)!==JSON.stringify(original.actionPin))return {outcome:'conflict',code:'request_key_conflict',reference:copy(reference)};
   await db.syncToFs();open();return copy(found.outcome);
   }catch{fence();return {outcome:'unknown',code:'storage_outcome_unknown',reference:copy(reference)};}
  }
 });
}
