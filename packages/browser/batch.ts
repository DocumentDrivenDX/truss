// SPDX-License-Identifier: MIT OR Apache-2.0
import {expandKeyReceipts} from './key-receipt-storage';
import * as umf from '@truss/umf-local-actions';
import type {PGlite} from '@electric-sql/pglite';
import {readCatalog} from './catalog';
import {journalHorizon,targetSource} from './objects';
import {SealCustodyUnavailable,type Artifact} from './materialize';
import type {StoreInfo} from './store';
import type {JobRef} from './bulk';
export class BatchRefusal extends Error {constructor(readonly status:'conflict'|'rejected',readonly code:string,readonly item:number){super(code);}}
const copy=<T>(x:T):T=>JSON.parse(JSON.stringify(x));
const hex=(s:string)=>Array.from(new TextEncoder().encode(s),n=>n.toString(16).padStart(2,'0')).join('');
const hash=async(s:string)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s))),n=>n.toString(16).padStart(2,'0')).join('');
const positive=(s:unknown):s is string=>typeof s==='string'&&/^[1-9][0-9]{0,18}$/.test(s)&&BigInt(s)<=9223372036854775807n;
export interface ItemResult {ordinal:number;result:{status:'committed';token:string;noOp:boolean;identity:{id:string;typeId:string};version:string;changes:{propertyId:string;before:{string:string};after:{string:string}}[];verification:{profile:'truss-browser-set-verification/0.1';requiredEffects:true;frame:true;keysUnchanged:true}}}
type BatchTx=Pick<PGlite,'query'|'exec'>;
function prepareFrozenSource(source:any){
 const model=JSON.parse(source.model.utf8),plan=JSON.parse(source.plan.utf8),manifest=JSON.parse(source.manifest.utf8);
 const context={registry:umf.createUmfRegistry(),models:[{pin:source.modelPin,artifact:source.model}],actions:[{pin:source.actionPin,artifact:source.model}],selections:[{profile:plan.selection.profile,inspect:(artifact:any,document:any,target:any)=>({eligible:JSON.stringify(artifact)===JSON.stringify(plan.selection.artifact)&&JSON.stringify(document)===JSON.stringify(model)&&target.module===plan.target.module&&target.element===plan.target.element&&target.key===plan.target.key,dependencies:copy(plan.selection.dependencies),diagnostics:[]})}]};
 const prepared=umf.prepareActionPlanModel(source.modelPin,source.actionPin,context);
 if(prepared.utf8!==source.preparation.utf8||prepared.sha256!==source.preparation.sha256||!umf.inspectActionManifest(source.manifest,context).eligible)throw new SealCustodyUnavailable('Original action/manifest preparation required');
 const preparation=JSON.parse(prepared.utf8),inspection=umf.inspectActions(model,context.registry);
 const actions=inspection.actions.filter((a:any)=>a.module===source.actionPin.identity.module&&a.action.id===source.actionPin.identity.action);
 if(actions.length!==1)throw new SealCustodyUnavailable('Exact original action required');const action=actions[0].action;
 const keyTuples=umf.prepareCoreKeyTuples(model),identities=umf.prepareActionIdentities(model,action);
 const keyReceipts=expandKeyReceipts(source);
 return {source,manifest,preparation,action,keyTuples,identities,keyReceipts};
}
type PreparedBatch=ReturnType<typeof prepareFrozenSource>;
const freezePrepared=<T>(value:T):T=>{if(value!==null&&typeof value==='object'&&!Object.isFrozen(value)){for(const child of Object.values(value))freezePrepared(child);Object.freeze(value);}return value;};
/** Stateless internal entry; callers cannot supply a pre-admitted result. */
export async function applyFrozenBatch(tx:BatchTx,info:StoreInfo,source:any,job:JobRef,batch:number){
 return applyPreparedBatch(tx,info,prepareFrozenSource(source),job,batch);
}
/** Per-open, one-entry pure source cache. All native checks remain in the call. */
export function createFrozenBatchApplier(info:StoreInfo){
 let retained:{input:string;prepared:PreparedBatch}|undefined;
 return async(tx:BatchTx,sourceUtf8:string,job:JobRef,batch:number)=>{
  if(typeof sourceUtf8!=='string')throw new SealCustodyUnavailable('Exact authorized source bytes required');
  let prepared=retained?.input===sourceUtf8?retained.prepared:undefined;
  if(!prepared){
   prepared=freezePrepared(prepareFrozenSource(JSON.parse(sourceUtf8)));
   retained={input:sourceUtf8,prepared};
  }
  return applyPreparedBatch(tx,info,prepared,job,batch);
 };
}
async function applyPreparedBatch(tx:BatchTx,info:StoreInfo,prepared:PreparedBatch,job:JobRef,batch:number){
 const {source,manifest,preparation,action,keyTuples,identities,keyReceipts}=prepared;
 const catalog=await readCatalog(tx),metadata=await targetSource(catalog,{documentId:source.modelPin.documentId,module:preparation.target.module,record:preparation.target.element});
 const partition=manifest.batches[batch];if(!partition||partition.ordinal!==batch)throw new SealCustodyUnavailable('Original frozen partition required');
 const namespace=JSON.stringify({profile:'truss-browser-key-namespace/0.1',storeId:info.storeId,incarnation:info.incarnation,document:catalog!.document.sourceSha256,typeId:metadata.type.typeId,keyId:metadata.key.keyId,keyNumber:metadata.key.keyNumber});
 const planned:any[]=[],ids=new Set<string>();
 const frozenItems=manifest.items.slice(partition.start,partition.start+partition.count);
 const frozenIds=new Set<string>();
 for(const item of frozenItems){
  if(!positive(item.guard.identity)||!positive(item.guard.version)||item.guard.store!==info.storeId||item.guard.epoch!==info.incarnation||frozenIds.has(item.guard.identity))throw new BatchRefusal('conflict','PAP_GUARD',item.ordinal);
  frozenIds.add(item.guard.identity);
 }
 const lockedRows=(await tx.query<any>(`SELECT id::text,ver::text AS version,props,retained,root_id::text,root_type::text,rev::text,
  to_char(created_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') AS "createdAt",
  to_char(updated_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') AS "updatedAt"
  FROM truss.object WHERE id=ANY($1::bigint[]) AND type_id=$2::int ORDER BY truss.object.id FOR UPDATE`,[[...frozenIds],metadata.type.typeId])).rows;
 const rowsById=new Map(lockedRows.map(row=>[row.id,row]));
 const wantedKeys=frozenItems.map((item:any)=>({id:item.guard.identity,keyHex:hex('umf-key-tuple-v1:hex:'+keyReceipts[item.ordinal].bytesHex)}));
 const keyRows=(await tx.query<any>(`SELECT k.object_id::text AS "objectId",convert_from(k.original_context_bytes,'UTF8') AS context,g.generation::text,
  EXISTS(SELECT 1 FROM truss.object_key_reservation_bucket r WHERE r.namespace_sha256=k.namespace_sha256 AND r.key_sha256=k.key_sha256 AND r.namespace_bytes=k.namespace_bytes AND r.key_bytes=k.key_bytes AND r.original_reservation_bytes=k.original_context_bytes) AS reserved
  FROM jsonb_to_recordset($1::jsonb) AS wanted(id text,"keyHex" text)
  JOIN truss.object_key_bucket k ON k.object_id=wanted.id::bigint
  JOIN truss.key_bucket_guard g USING(namespace_sha256,key_sha256)
  WHERE k.type_id=$2::int AND k.key_num=$3::smallint
   AND k.namespace_sha256=sha256(decode($4,'hex')) AND k.namespace_bytes=decode($4,'hex')
   AND k.key_sha256=sha256(decode(wanted."keyHex",'hex')) AND k.key_bytes=decode(wanted."keyHex",'hex')`,[JSON.stringify(wantedKeys),metadata.type.typeId,metadata.key.keyNumber,hex(namespace)])).rows;
 const keysById=new Map<string,any[]>();
 for(const key of keyRows){const bucket=keysById.get(key.objectId)??[];bucket.push(key);keysById.set(key.objectId,bucket);}

 // Finish every item's input/frame/key/version check before any business effect.
 for(const item of frozenItems){
  const ordinal=item.ordinal;
  const inputs=identities.admitInputs(item.inputs),receipt=keyTuples.verify(keyReceipts[ordinal]);
  if(!positive(item.guard.identity)||!positive(item.guard.version)||item.guard.store!==info.storeId||item.guard.epoch!==info.incarnation||ids.has(item.guard.identity))throw new BatchRefusal('conflict','PAP_GUARD',ordinal);ids.add(item.guard.identity);
  for(const frame of [...action.reads,...action.writes])if(identities.select(frame.id,inputs).tupleHex!==receipt.bytesHex)throw new BatchRefusal('rejected','ACTION_FRAME',ordinal);
  const found=rowsById.get(item.guard.identity),rows=found?[found]:[];
  if(rows.length!==1||rows[0].version!==item.guard.version)throw new BatchRefusal('conflict','PAP_GUARD',ordinal);
  const row=rows[0];if(row.root_id!==null||row.root_type!==null||row.retained!==null||Object.keys(row.props).length!==metadata.members.length)throw new BatchRefusal('rejected','UNSUPPORTED_OBJECT_PROFILE',ordinal);
  for(const member of metadata.members){const cell=row.props[member.propertyId];if(!cell||Object.keys(cell).sort().join(',')!=='kind,text'||cell.kind!=='string'||typeof cell.text!=='string')throw new BatchRefusal('rejected','INVALID_STORED_VALUE',ordinal);}
  const actual=keyTuples.encode(preparation.target,[{string:row.props[metadata.key.propertyIds[0]].text}]);
  if(actual.bytesHex!==receipt.bytesHex)throw new BatchRefusal('conflict','PAP_REBOUND',ordinal);
  const keys=keysById.get(row.id)??[];
  if(keys.length!==1||!keys[0]!.reserved||BigInt(keys[0]!.generation)<1n)throw new BatchRefusal('conflict','PAP_REBOUND',ordinal);
  const custody=JSON.parse(keys[0]!.context),originalKey=keyTuples.verify(JSON.parse(custody.ownerReceiptUtf8));
  if(custody.object.id!==row.id||custody.object.typeId!==metadata.type.typeId||custody.namespaceUtf8!==namespace||originalKey.bytesHex!==actual.bytesHex)throw new SealCustodyUnavailable('Original key custody required');
  const props=copy(row.props),changes:ItemResult['result']['changes']=[];
  for(const assignment of preparation.assignments){
   const member=metadata.members.find((m:any)=>m.module===assignment.field.module&&m.element===assignment.field.element);
   const value=inputs[assignment.input];if(!member||metadata.key.propertyIds.includes(member.propertyId)||!value||Object.keys(value).join(',')!=='string'||typeof value.string!=='string')throw new BatchRefusal('rejected','ACTION_VALUE',ordinal);
   if(props[member.propertyId].text!==value.string){changes.push({propertyId:member.propertyId,before:{string:props[member.propertyId].text},after:{string:value.string}});props[member.propertyId]={kind:'string',text:value.string};}
  }
  if(changes.length&&BigInt(row.version)===9223372036854775807n)throw new BatchRefusal('rejected','VERSION_EXHAUSTED',ordinal);
  planned.push({item,row,props,changes});
 }
 if(planned.length!==partition.count)throw new SealCustodyUnavailable('Complete original batch required');
 await journalHorizon(tx);const items:ItemResult[]=[],journal:string[]=[];
 const writer=(await tx.query<{xid:string}>('SELECT pg_current_xact_id()::text AS xid')).rows[0]!.xid;
 const record=(row:any,props:any,version:string,updatedAt:string)=>({interfaceVersion:'truss-browser-history-record/0.1',kind:'object',identity:{id:row.id,typeId:metadata.type.typeId,version},recordVersion:version,catalogRevision:catalog!.catalogRevision,documentSha256:catalog!.document.sourceSha256,createdAt:row.createdAt,updatedAt,properties:metadata.members.map((m:any)=>({propertyId:m.propertyId,value:props[m.propertyId]})),retained:[],ownership:{state:'rootless'}});
 for(const entry of planned){
  const {item,row,props,changes}=entry;let version=row.version,updatedAt=row.updatedAt;
  if(changes.length){
   const updated=(await tx.query<{version:string;updatedAt:string}>(`UPDATE truss.object SET props=$3::jsonb,ver=ver+1,rev=$4::int,updated_at=clock_timestamp()
    WHERE id=$1::bigint AND type_id=$2::int AND ver=$5::bigint RETURNING ver::text AS version,to_char(updated_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') AS "updatedAt"`,[row.id,metadata.type.typeId,JSON.stringify(props),catalog!.catalogRevision,row.version])).rows;
   if(updated.length!==1)throw new BatchRefusal('conflict','PAP_GUARD',item.ordinal);version=updated[0]!.version;updatedAt=updated[0]!.updatedAt;
   for(const change of changes){
    const seq=(await tx.query<{seq:string}>("SELECT nextval('truss.journal_seq')::text AS seq")).rows[0]!.seq;
    const origin={profile:'truss-browser-local-origin/0.1',storeId:info.storeId,incarnation:info.incarnation,job,batch,item:item.ordinal};
    const event=JSON.stringify({interfaceVersion:'truss-browser-history-event/0.1',historyProfile:'truss-browser-set/0.1',operation:'property',storeId:info.storeId,incarnation:info.incarnation,job,batch,inputIndex:item.ordinal.toString(),xid:writer,seq,identity:{id:row.id,typeId:metadata.type.typeId,version},eventVersion:version,eventCatalogRevision:catalog!.catalogRevision,propertyId:change.propertyId,origin,before:record(row,row.props,row.version,row.updatedAt),after:record(row,props,version,updatedAt),oldValue:change.before,newValue:change.after});
    await tx.query(`WITH bytes AS (SELECT $6::jsonb::text AS event,$7::jsonb::text AS origin), wrappers AS (
     SELECT jsonb_build_object('interfaceVersion','truss-browser-journal-exact-bytes/0.1','eventInterfaceVersion','truss-browser-history-event/0.1','component',component,'canonicalizationProfile',jsonb_build_object('identity','truss-pg18-jsonb-text','version','0.1','sha256','e5eec0aa3dfd5195250bb2e781626c6229f645d71a5c21095ee3d10008aadc97'),'bytesBase64',replace(encode(convert_to(content,'UTF8'),'base64'),chr(10),''),'bytesSha256',encode(sha256(convert_to(content,'UTF8')),'hex')) AS wrapper,component FROM bytes CROSS JOIN LATERAL (VALUES ('event',bytes.event),('origin',bytes.origin)) entries(component,content))
     INSERT INTO truss.journal(seq,entity_kind,entity_id,entity_type,ver,op,prop_id,rev,new_value,origin) VALUES($1::bigint,'o',$2::bigint,$3::int,$4::bigint,'update',$5::int,$8::int,(SELECT wrapper FROM wrappers WHERE component='event'),(SELECT wrapper FROM wrappers WHERE component='origin'))`,[seq,row.id,metadata.type.typeId,version,change.propertyId,event,JSON.stringify(origin),catalog!.catalogRevision]);journal.push(seq);
   }
  }
  const verified=(await tx.query<{ok:boolean}>('SELECT props=$3::jsonb AND ver=$4::bigint AND root_id IS NULL AND root_type IS NULL AND retained IS NULL AS ok FROM truss.object WHERE id=$1::bigint AND type_id=$2::int',[row.id,metadata.type.typeId,JSON.stringify(props),version])).rows;
  if(verified.length!==1||!verified[0]!.ok)throw new BatchRefusal('rejected','EFFECT_VERIFICATION',item.ordinal);
  items.push({ordinal:item.ordinal,result:{status:'committed',token:'pap1/'+job.namespace+'/'+job.id+'/'+batch+'/'+item.ordinal,noOp:changes.length===0,identity:{id:row.id,typeId:metadata.type.typeId},version,changes,verification:{profile:'truss-browser-set-verification/0.1',requiredEffects:true,frame:true,keysUnchanged:true}}});
 }
 const utf8=JSON.stringify({profile:'truss-browser-batch-receipt/0.1',storeId:info.storeId,incarnation:info.incarnation,job,batch,manifestSha256:source.manifest.sha256,writerXid:writer,journal,items});
 const receipt:Artifact={mediaType:'application/json',utf8,sha256:await hash(utf8)};
 return {items,receipt};
}
