// SPDX-License-Identifier: MIT OR Apache-2.0
import * as umf from '@truss/umf-local-actions';
import type {PGlite} from '@electric-sql/pglite';
import {readCatalog,prepareDocument,type CatalogSnapshot} from './catalog';
import {captureSeal,type SealRequest} from './materialize';
import type {StoreInfo} from './store';
export interface RecordIdentity {documentId:string;module:string;record:string}
export interface ObjectRow {id:string;typeId:string;version:string;fields:{module:string;field:string;value:string}[]}
export interface ObjectPageInput {target:RecordIdentity;limit:number;afterId:string|null}
export interface ObjectPage {objects:ObjectRow[];nextAfterId:string|null}
export function captureObjectPage(input:ObjectPageInput):ObjectPageInput{
 if(!input||Object.keys(input).sort().join(',')!=='afterId,limit,target')throw Error('Complete page position required');
 const {target:rawTarget,limit,afterId}=input;
 if(!Number.isInteger(limit)||limit<1||limit>512)throw Error('Page limit1..512 required');
 if(afterId!==null){text(afterId,19);if(!/^[1-9][0-9]{0,18}$/.test(afterId)||afterId.length===19&&afterId>'9223372036854775807')throw Error('Native object position required');}
 return Object.freeze({target:captureTarget(rawTarget),limit,afterId});
}
export interface LoadInput {target:RecordIdentity;rows:{fields:{module:string;field:string;value:string}[]}[];request:SealRequest}
export type LoadOutcome={outcome:'loaded';request:SealRequest;objects:{id:string;typeId:string;version:string}[];journal:string[]}
 |{outcome:'refused';code:string;reason:string;request:SealRequest}
 |{outcome:'unresolved';code:'not_found';request:SealRequest}
 |{outcome:'conflict';code:'request_key_conflict';request:SealRequest}
 |{outcome:'unknown';code:'storage_outcome_unknown';request:SealRequest}
 |{outcome:'failure';code:string;reason:string;request:SealRequest;settlement:'not_dispatched'|'current_attempt_rolled_back'};
const copy=<T>(x:T):T=>JSON.parse(JSON.stringify(x));
const utf8=(s:string)=>new TextEncoder().encode(s);
const hex=(b:Uint8Array)=>Array.from(b,n=>n.toString(16).padStart(2,'0')).join('');
const hash=async(s:string)=>hex(new Uint8Array(await crypto.subtle.digest('SHA-256',utf8(s))));
function text(s:unknown,max=4096):asserts s is string {if(typeof s!=='string'||utf8(s).length>max||s.includes('\0')||new TextDecoder().decode(utf8(s))!==s)throw Error('Bounded exact String required');}
export function captureTarget(input:RecordIdentity):RecordIdentity{
 if(!input||Object.keys(input).sort().join(',')!=='documentId,module,record')throw Error('Qualified Record required');
 const {documentId,module,record}=input;for(const value of [documentId,module,record]){text(value,256);if(!value)throw Error('Nonempty identity required');}return Object.freeze({documentId,module,record});
}
export function captureLoad(input:LoadInput):LoadInput{
 if(!input||Object.keys(input).sort().join(',')!=='request,rows,target')throw Error('Bounded complete load required');
 const {target:rawTarget,request:rawRequest,rows:rawRows}=input;
 if(!Array.isArray(rawRows)||rawRows.length<1||rawRows.length>100)throw Error('Bounded complete load required');
 const target=captureTarget(rawTarget),request=captureSeal(rawRequest);
 const rows=Array.from(rawRows,row=>{
  if(!row||Object.keys(row).join(',')!=='fields')throw Error('Complete member fields required');
  const {fields}=row;
  if(!Array.isArray(fields)||fields.length<1||fields.length>64)throw Error('Complete member fields required');
  return Object.freeze({fields:Object.freeze(Array.from(fields,f=>{
   if(!f||Object.keys(f).sort().join(',')!=='field,module,value')throw Error('Qualified field value required');const {module,field,value}=f;text(module,256);text(field,256);text(value,65536);return Object.freeze({module,field,value});
  }))});
 });
 if(utf8(JSON.stringify(rows)).length>1048576)throw Error('Load byte limit');
 return Object.freeze({target,request,rows}) as unknown as LoadInput;
}
export async function targetSource(catalog:CatalogSnapshot|null,target:RecordIdentity){
 if(!catalog||catalog.document.documentId!==target.documentId)throw Error('Accepted document required');
 const prepared=await prepareDocument({documentId:target.documentId,documentRevision:catalog.document.documentRevision as string,sourceUtf8:catalog.document.sourceUtf8 as string});
 const types=(catalog.types as any[]).filter(t=>t.documentId===target.documentId&&t.moduleId===target.module&&t.recordId===target.record);
 if(types.length!==1)throw Error('Accepted Record required');const type=types[0];
 const observations=prepared.documents[0]!.validation.observations.filter((o:any)=>o.operation==='inspectCoreRecordMembers'&&o.identity.module===target.module&&o.identity.element===target.record);
 if(observations.length!==1||observations[0].result.meaning.state!=='known')throw Error('Original member observation required');
 const members=observations[0].result.meaning.members.map((m:any)=>{
  const props=(catalog.properties as any[]).filter(p=>p.typeId===type.typeId&&p.moduleId===m.module&&p.fieldId===m.element);if(props.length!==1)throw Error('Original property correspondence required');return {...m,propertyId:props[0].propertyId};
 });
 const keys=(catalog.keys as any[]).filter(k=>k.typeId===type.typeId);if(keys.length!==1||!keys[0].primary||keys[0].propertyIds.length!==1)throw Error('Single primary Key required');
 return {type,members, key:keys[0],source:JSON.parse(catalog.document.sourceUtf8 as string)};
}
const originalJournalChecks=[
 {name:'journal_complete_origin',definition:"CHECK ((((jsonb_typeof(origin) = 'object'::text) AND ((origin ->> 'interfaceVersion'::text) = 'truss-journal-exact-bytes/0.2.0-proposal'::text) AND ((origin ->> 'component'::text) = 'origin'::text)) IS TRUE))"},
 {name:'journal_complete_payload',definition:"CHECK (((old_value IS NULL) AND (new_value IS NOT NULL) AND (((jsonb_typeof(new_value) = 'object'::text) AND ((new_value ->> 'interfaceVersion'::text) = 'truss-journal-exact-bytes/0.2.0-proposal'::text) AND ((new_value ->> 'component'::text) = 'event'::text)) IS TRUE)))"}
];
const checksEqual=(actual:{name:string;definition:string}[],expected:{name:string;definition:string}[])=>actual.length===expected.length&&actual.every((c,i)=>c.name===expected[i]!.name&&c.definition===expected[i]!.definition);
export async function journalHorizon(tx:Pick<PGlite,'query'|'exec'>,install=true){
 await tx.exec("SET TimeZone='UTC'; SET DateStyle='ISO, YMD'");
 const key='browser:journal:0.1';
 const definitions=async()=>(await tx.query<{name:string;definition:string}>("SELECT conname AS name,pg_get_constraintdef(oid) AS definition FROM pg_constraint WHERE conrelid='truss.journal'::regclass AND conname IN ('journal_complete_payload','journal_complete_origin') ORDER BY conname")).rows;
 const existing=(await tx.query<{value:any}>('SELECT value FROM truss.setting WHERE key=$1',[key])).rows;
 const partitions=async()=>(await tx.query<{name:string;bound:string}>("SELECT c.relname AS name,pg_get_expr(c.relpartbound,c.oid) AS bound FROM pg_inherits i JOIN pg_class c ON c.oid=i.inhrelid WHERE i.inhparent='truss.journal'::regclass ORDER BY c.relname")).rows;
 let actual=await partitions();
 if(!existing.length){
  if(actual.length)throw Error('Foreign journal partition refused');
  if(!checksEqual(await definitions(),originalJournalChecks))throw Error('Exact original journal constraints required before browser adjunct');
  if(!install)return;
  await tx.exec("ALTER TABLE truss.journal DROP CONSTRAINT journal_complete_payload, DROP CONSTRAINT journal_complete_origin; ALTER TABLE truss.journal ADD CONSTRAINT journal_complete_payload CHECK (old_value IS NULL AND new_value IS NOT NULL AND (jsonb_typeof(new_value)='object' AND new_value->>'interfaceVersion'='truss-browser-journal-exact-bytes/0.1' AND new_value->>'component'='event') IS TRUE), ADD CONSTRAINT journal_complete_origin CHECK ((jsonb_typeof(origin)='object' AND origin->>'interfaceVersion'='truss-browser-journal-exact-bytes/0.1' AND origin->>'component'='origin') IS TRUE)");
  await tx.exec("DO $$ DECLARE lo timestamptz:=date_trunc('month',clock_timestamp())-interval '1 month'; hi timestamptz:=date_trunc('month',clock_timestamp())+interval '13 months'; BEGIN EXECUTE format('CREATE TABLE truss.journal_browser_horizon PARTITION OF truss.journal FOR VALUES FROM (%L) TO (%L)',lo,hi); END $$");
  actual=await partitions();await tx.query('INSERT INTO truss.setting(key,value) VALUES($1,$2::jsonb)',[key,JSON.stringify({profile:'truss-browser-journal/0.1',eventInterfaceVersion:'truss-browser-history-event/0.1',wrapperInterfaceVersion:'truss-browser-journal-exact-bytes/0.1',constraints:await definitions(),partitions:actual})]);
 }else if(existing.length!==1||existing[0]!.value.profile!=='truss-browser-journal/0.1'||!Array.isArray(existing[0]!.value.partitions)||existing[0]!.value.partitions.length!==actual.length||actual.some((p,i)=>{const retained=existing[0]!.value.partitions[i];return !retained||Object.keys(retained).sort().join(',')!=='bound,name'||retained.name!==p.name||retained.bound!==p.bound;}))throw Error('Original finite journal horizon required');
 if(existing.length){if(actual.length!==1||actual[0]!.name!=='journal_browser_horizon')throw Error('Exact browser journal partition required');const expected=existing[0]!.value.constraints,found=await definitions();if(!checksEqual(found,originalJournalChecks.map(c=>({...c,definition:c.definition.replace('truss-journal-exact-bytes/0.2.0-proposal','truss-browser-journal-exact-bytes/0.1')}))))throw Error('Exact browser journal constraints required');if(existing[0]!.value.eventInterfaceVersion!=='truss-browser-history-event/0.1'||existing[0]!.value.wrapperInterfaceVersion!=='truss-browser-journal-exact-bytes/0.1'||!Array.isArray(expected)||expected.length!==2||found.length!==2||found.some((c,i)=>expected[i]?.name!==c.name||expected[i]?.definition!==c.definition))throw Error('Original browser journal carrier constraints required');}
}
function logicalObjects(metadata:Awaited<ReturnType<typeof targetSource>>,rows:{id:string;version:string;props:Record<string,any>}[]):ObjectRow[]{
 return rows.map(row=>{
  if(Object.keys(row.props).length!==metadata.members.length)throw Error('Complete logical members required');
  return {id:row.id,typeId:metadata.type.typeId,version:row.version,fields:metadata.members.map((m:any)=>{const cell=row.props[m.propertyId];if(!cell||Object.keys(cell).sort().join(',')!=='kind,text'||cell.kind!=='string'||typeof cell.text!=='string')throw Error('Original String cell required');return {module:m.module,field:m.element,value:cell.text};})};
 });
}
export function createObjectAccess(db:PGlite,info:StoreInfo,isOpen:()=>boolean,fence:()=>void){
 const open=()=>{if(!isOpen())throw Error('Current issued local owner required');};
 return {
  async read(target:RecordIdentity){
   open();let catalog:CatalogSnapshot|null;try{catalog=await readCatalog(db);}catch(error){fence();throw error;}
   const metadata=await targetSource(catalog,target);
   let rows:{id:string;version:string;props:Record<string,any>}[];
   try{
    rows=(await db.query<{id:string;version:string;props:Record<string,any>}>("SELECT o.id::text,o.ver::text AS version,o.props FROM truss.object o WHERE o.type_id=$1::int ORDER BY o.id LIMIT 101",[metadata.type.typeId])).rows;
   }catch(error){fence();throw error;}
    if(rows.length>100||utf8(JSON.stringify(rows)).length>8388608)throw Error('Bounded read limit');
   try{
    return logicalObjects(metadata,rows);
   }catch(error){fence();throw error;}
  },
  async readPage(input:ObjectPageInput):Promise<ObjectPage>{
   open();let catalog:CatalogSnapshot|null;try{catalog=await readCatalog(db);}catch(error){fence();throw error;}
   const metadata=await targetSource(catalog,input.target);
   let rows:{id:string;version:string;props:Record<string,any>}[];
   try{
    rows=(await db.query<{id:string;version:string;props:Record<string,any>}>("SELECT o.id::text,o.ver::text AS version,o.props FROM truss.object o WHERE o.type_id=$1::int AND ($2::bigint IS NULL OR o.id>$2::bigint) ORDER BY o.id LIMIT $3::int",[metadata.type.typeId,input.afterId,input.limit+1])).rows;
   }catch(error){fence();throw error;}
   if(utf8(JSON.stringify(rows)).length>8388608)throw Error('Bounded read byte limit');
   try{
    const more=rows.length>input.limit,objects=logicalObjects(metadata,rows.slice(0,input.limit));
    return {objects,nextAfterId:more?objects[objects.length-1]!.id:null};
   }catch(error){fence();throw error;}
  },
  async load(input:LoadInput,recovery=false):Promise<LoadOutcome>{
   const request=copy(input.request);let catalog:CatalogSnapshot|null,metadata:Awaited<ReturnType<typeof targetSource>>;
   if(!isOpen()&&recovery)return {outcome:'refused',code:'store_not_open',reason:'Current open store required',request};
   if(!isOpen())return {outcome:'failure',code:'store_not_open',reason:'Current open store required',request,settlement:'not_dispatched'};
   try{catalog=await readCatalog(db);}catch(error){fence();if(recovery)return {outcome:'unknown',code:'storage_outcome_unknown',request};return {outcome:'failure',code:'admission_failed',reason:String(error),request,settlement:'not_dispatched'};}
   try{metadata=await targetSource(catalog,input.target);}catch(error){if(recovery)return {outcome:'refused',code:'recovery_input_refused',reason:String(error),request};return {outcome:'failure',code:'invalid_input',reason:String(error),request,settlement:'not_dispatched'};}
   const cut=JSON.stringify({info,catalog}),inputUtf8=JSON.stringify({profile:'truss-browser-load/0.1',cut,input});
   const storageKey='browser:load:0.1:'+hex(utf8(request.requestKey));
   const namespaceUtf8=JSON.stringify({profile:'truss-browser-key-namespace/0.1',storeId:info.storeId,incarnation:info.incarnation,document:catalog!.document.sourceSha256,typeId:metadata.type.typeId,keyId:metadata.key.keyId,keyNumber:metadata.key.keyNumber});
   let planned:{props:Record<string,unknown>;keyHex:string;receiptUtf8:string}[];
   try{
    planned=input.rows.map(row=>{
     if(row.fields.length!==metadata.members.length)throw Error('Complete Record members required');
     const props:Record<string,unknown>={};
     for(const member of metadata.members){const fields=row.fields.filter(f=>f.module===member.module&&f.field===member.element);if(fields.length!==1)throw Error('Unique complete member values required');props[member.propertyId]={kind:'string',text:fields[0]!.value};}
     const value=(props[metadata.key.propertyIds[0]] as {text:string}).text;
     const receipt=umf.encodeCoreKeyTuple(metadata.source,{module:input.target.module,element:input.target.record,key:metadata.key.keyId},[{string:value}]);
     if(receipt.operation!=='encode-core-key-tuple'||receipt.profile!=='umf-key-tuple-v1'||typeof receipt.bytesHex!=='string'||!/^(?:[0-9a-f]{2})+$/.test(receipt.bytesHex))throw Error('Original UMF key receipt required');
     return {props,keyHex:hex(utf8('umf-key-tuple-v1:hex:'+receipt.bytesHex)),receiptUtf8:JSON.stringify(receipt)};
    });
    if(new Set(planned.map(p=>p.keyHex)).size!==planned.length)throw Error('Duplicate load key');
   }catch(error){if(recovery)return {outcome:'refused',code:'recovery_input_refused',reason:String(error),request};return {outcome:'failure',code:'invalid_input',reason:String(error),request,settlement:'not_dispatched'};}
   const sentinel=Symbol();let callbackFailure:unknown=sentinel;
   try{
    const result=await db.transaction<LoadOutcome>(async tx=>{try{
     open();if(JSON.stringify({info,catalog:await readCatalog(tx)})!==cut)throw Error('Original catalog cut required');
     await tx.exec("SET LOCAL statement_timeout='5000ms'; SET LOCAL TimeZone='UTC'");
     const prior=(await tx.query<{value:any}>('SELECT value FROM truss.setting WHERE key=$1',[storageKey])).rows;
     if(prior.length){const stored=prior[0]!.value;if(stored.profile!=='truss-browser-load/0.1'||typeof stored.inputUtf8!=='string'||typeof stored.outcomeUtf8!=='string'||await hash(stored.inputUtf8)!==stored.inputSha256||await hash(stored.outcomeUtf8)!==stored.outcomeSha256)throw Error('Original load custody required');if(stored.inputUtf8!==inputUtf8)return {outcome:'conflict',code:'request_key_conflict',request};return JSON.parse(stored.outcomeUtf8);}
     if(recovery)return {outcome:'unresolved',code:'not_found',request};
     await journalHorizon(tx);
     const ns=hex(utf8(namespaceUtf8));
     for(const row of planned){
      const collisions=(await tx.query<{n:string}>("SELECT (SELECT count(*) FROM truss.object_key_bucket WHERE namespace_sha256=sha256(decode($1,'hex')) AND key_sha256=sha256(decode($2,'hex')) AND namespace_bytes=decode($1,'hex') AND key_bytes=decode($2,'hex'))+(SELECT count(*) FROM truss.object_key_reservation_bucket WHERE namespace_sha256=sha256(decode($1,'hex')) AND key_sha256=sha256(decode($2,'hex')) AND namespace_bytes=decode($1,'hex') AND key_bytes=decode($2,'hex')) AS n",[ns,row.keyHex])).rows[0];
      if(String(collisions!.n)!=='0')throw Error('Key allocated or reserved');
     }
     const objects:Extract<LoadOutcome,{outcome:'loaded'}>['objects']=[],journal:string[]=[];
     for(const row of planned){
      const object=(await tx.query<{id:string;typeId:string;version:string}>('INSERT INTO truss.object(type_id,props,rev) VALUES($1::int,$2::jsonb,$3::int) RETURNING id::text,"type_id"::text AS "typeId",ver::text AS version',[metadata.type.typeId,JSON.stringify(row.props),catalog!.catalogRevision])).rows[0]!;
      const custody=JSON.stringify({profile:'truss-browser-load-key/0.1',request,object,namespaceUtf8,ownerReceiptUtf8:row.receiptUtf8});
      const before=(await tx.query<{generation:string}>("SELECT generation::text FROM truss.key_bucket_guard WHERE namespace_sha256=sha256(decode($1,'hex')) AND key_sha256=sha256(decode($2,'hex'))",[ns,row.keyHex])).rows;
      const expected=before.length?BigInt(before[0]!.generation)+1n:1n;
      const guarded=(await tx.query<{generation:string}>("INSERT INTO truss.key_bucket_guard(namespace_sha256,key_sha256,generation) VALUES(sha256(decode($1,'hex')),sha256(decode($2,'hex')),1) ON CONFLICT(namespace_sha256,key_sha256) DO UPDATE SET generation=truss.key_bucket_guard.generation+1 RETURNING generation::text",[ns,row.keyHex])).rows;
      if(guarded.length!==1||BigInt(guarded[0]!.generation)!==expected)throw Error('Exact key generation required');
      await tx.query("INSERT INTO truss.object_key_bucket(type_id,key_num,object_id,namespace_bytes,key_bytes,original_context_bytes) VALUES($1::int,$2::smallint,$3::bigint,decode($4,'hex'),decode($5,'hex'),convert_to($6,'UTF8'))",[object.typeId,metadata.key.keyNumber,object.id,ns,row.keyHex,custody]);
      await tx.query("INSERT INTO truss.object_key_reservation_bucket(namespace_bytes,key_bytes,original_reservation_bytes) VALUES(decode($1,'hex'),decode($2,'hex'),convert_to($3,'UTF8'))",[ns,row.keyHex,custody]);
      const stored=(await tx.query<{members:string;reservations:string}>("SELECT (SELECT count(*)::text FROM truss.object_key_bucket WHERE object_id=$1::bigint AND type_id=$2::int AND key_num=$3::smallint AND namespace_bytes=decode($4,'hex') AND key_bytes=decode($5,'hex') AND original_context_bytes=convert_to($6,'UTF8')) AS members,(SELECT count(*)::text FROM truss.object_key_reservation_bucket WHERE namespace_sha256=sha256(decode($4,'hex')) AND key_sha256=sha256(decode($5,'hex')) AND namespace_bytes=decode($4,'hex') AND key_bytes=decode($5,'hex') AND original_reservation_bytes=convert_to($6,'UTF8')) AS reservations",[object.id,object.typeId,metadata.key.keyNumber,ns,row.keyHex,custody])).rows[0]!;
      if(stored.members!=='1'||stored.reservations!=='1')throw Error('Exact original key custody required');
      const actual=(await tx.query<{createdAt:string;updatedAt:string;xid:string;seq:string}>("SELECT to_char(created_at AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"') AS \"createdAt\",to_char(updated_at AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"') AS \"updatedAt\",pg_current_xact_id()::text AS xid,nextval('truss.journal_seq')::text AS seq FROM truss.object WHERE id=$1::bigint AND type_id=$2::int",[object.id,object.typeId])).rows[0]!;
      const origin={profile:'truss-browser-local-origin/0.1',storeId:info.storeId,incarnation:info.incarnation};
      const event=JSON.stringify({interfaceVersion:'truss-browser-history-event/0.1',historyProfile:'truss-browser-create/0.1',operation:'create',storeId:info.storeId,incarnation:info.incarnation,request,inputIndex:objects.length.toString(),xid:actual.xid,seq:actual.seq,identity:object,eventVersion:'1',eventCatalogRevision:catalog!.catalogRevision,origin,after:{interfaceVersion:'truss-browser-history-record/0.1',kind:'object',identity:object,recordVersion:'1',catalogRevision:catalog!.catalogRevision,documentSha256:catalog!.document.sourceSha256,createdAt:actual.createdAt,updatedAt:actual.updatedAt,properties:metadata.members.map((m:any)=>({propertyId:m.propertyId,value:row.props[m.propertyId]})),retained:[],ownership:{state:'rootless'}}});
      const entry=(await tx.query<{seq:string}>(`WITH bytes AS (SELECT $4::jsonb::text AS event,$5::jsonb::text AS origin), wrappers AS (
       SELECT jsonb_build_object('interfaceVersion','truss-browser-journal-exact-bytes/0.1','eventInterfaceVersion','truss-browser-history-event/0.1','component',component,'canonicalizationProfile',jsonb_build_object('identity','truss-pg18-jsonb-text','version','0.1','sha256','e5eec0aa3dfd5195250bb2e781626c6229f645d71a5c21095ee3d10008aadc97'),'bytesBase64',replace(encode(convert_to(content,'UTF8'),'base64'),chr(10),''),'bytesSha256',encode(sha256(convert_to(content,'UTF8')),'hex')) AS wrapper,component
       FROM bytes CROSS JOIN LATERAL (VALUES ('event',bytes.event),('origin',bytes.origin)) entries(component,content))
       INSERT INTO truss.journal(seq,entity_kind,entity_id,entity_type,ver,op,rev,new_value,origin) VALUES($6::bigint,'o',$1::bigint,$2::int,1,'create',$3::int,(SELECT wrapper FROM wrappers WHERE component='event'),(SELECT wrapper FROM wrappers WHERE component='origin')) RETURNING seq::text`,[object.id,object.typeId,catalog!.catalogRevision,event,JSON.stringify(origin),actual.seq])).rows[0]!;
      objects.push(object);journal.push(entry.seq);
     }
     const outcome:LoadOutcome={outcome:'loaded',request,objects,journal},outcomeUtf8=JSON.stringify(outcome);
     await tx.query('INSERT INTO truss.setting(key,value) VALUES($1,$2::jsonb)',[storageKey,JSON.stringify({profile:'truss-browser-load/0.1',inputUtf8,inputSha256:await hash(inputUtf8),outcomeUtf8,outcomeSha256:await hash(outcomeUtf8)})]);open();return outcome;
    }catch(error){callbackFailure=error;throw error;}});
    await db.syncToFs();open();return result;
   }catch(error){if(recovery){fence();return {outcome:'unknown',code:'storage_outcome_unknown',request};}if(callbackFailure===error)return {outcome:'failure',code:'load_refused',reason:String(error),request,settlement:'current_attempt_rolled_back'};fence();return {outcome:'unknown',code:'storage_outcome_unknown',request};}
  }
 };
}
