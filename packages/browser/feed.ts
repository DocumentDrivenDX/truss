// SPDX-License-Identifier: MIT OR Apache-2.0
import type {PGlite} from '@electric-sql/pglite';
import {readCatalog} from './catalog';
import {journalHorizon,targetSource} from './objects';
import type {StoreInfo} from './store';
import {captureSeal,type Artifact,type SealRequest} from './materialize';
import type {JobRef} from './bulk';
export interface FeedCursor {profile:'truss-browser-feed-cursor/0.1';storeId:string;incarnation:string;afterSeq:string}
export interface FeedInput {cursor:FeedCursor|null;limit:number}
export interface LogicalJournalObject {id:string;typeId:string;version:string;createdAt:string;updatedAt:string;fields:{module:string;field:string;name:string;value:string}[]}
export type JournalContext={kind:'load';request:SealRequest;index:string}|{kind:'batch';job:JobRef;batch:number;item:number};
export interface JournalEntry {context:JournalContext;sequence:string;transactionId:string;at:string;operation:'create'|'property';catalogRevision:string;target:{documentId:string;module:string;record:string};before:LogicalJournalObject|null;after:LogicalJournalObject;change:null|{module:string;field:string;name:string;before:string;after:string};event:Artifact;origin:Artifact}
export type FeedPage={status:'page';profile:'truss-browser-journal-page/0.1';events:JournalEntry[];cursor:FeedCursor;hasMore:boolean}
 |{status:'refused';code:'CURSOR_SCOPE'|'READ_LIMIT'|'STORE_NOT_OPEN'};
const bytes=(s:string)=>new TextEncoder().encode(s);
const digest=async(s:string|Uint8Array)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',typeof s==='string'?bytes(s):Uint8Array.from(s))),n=>n.toString(16).padStart(2,'0')).join('');
const unsigned=(s:unknown,max=9223372036854775807n):s is string=>typeof s==='string'&&/^(0|[1-9][0-9]{0,19})$/.test(s)&&BigInt(s)<=max;
function exact(value:any,keys:string[]){if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).sort().join(',')!==keys.slice().sort().join(','))throw Error('Exact browser journal custody required');}
export function captureFeed(input:FeedInput):FeedInput{
 exact(input,['cursor','limit']);const {cursor,limit}=input;if(!Number.isInteger(limit)||limit<1||limit>100)throw Error('Feed limit1..100 required');
 if(cursor===null)return Object.freeze({cursor:null,limit});
 exact(cursor,['profile','storeId','incarnation','afterSeq']);const {profile,storeId,incarnation,afterSeq}=cursor;
 if(profile!=='truss-browser-feed-cursor/0.1'||typeof storeId!=='string'||storeId.length!==36||typeof incarnation!=='string'||incarnation.length!==36||!unsigned(afterSeq))throw Error('Original scoped feed cursor required');
 return Object.freeze({cursor:Object.freeze({profile,storeId,incarnation,afterSeq}),limit});
}
class ReadLimit extends Error {}
class NotOpen extends Error {}
async function originalEnvelope(value:any,component:'event'|'origin'):Promise<Artifact>{
 exact(value,['interfaceVersion','eventInterfaceVersion','component','canonicalizationProfile','bytesBase64','bytesSha256']);
 exact(value.canonicalizationProfile,['identity','version','sha256']);
 if(value.interfaceVersion!=='truss-browser-journal-exact-bytes/0.1'||value.eventInterfaceVersion!=='truss-browser-history-event/0.1'||value.component!==component
  ||value.canonicalizationProfile.identity!=='truss-pg18-jsonb-text'||value.canonicalizationProfile.version!=='0.1'||value.canonicalizationProfile.sha256!=='e5eec0aa3dfd5195250bb2e781626c6229f645d71a5c21095ee3d10008aadc97'
  ||typeof value.bytesBase64!=='string'||typeof value.bytesSha256!=='string'||!/^[0-9a-f]{64}$/.test(value.bytesSha256))throw Error('Original browser journal envelope required');
 const binary=atob(value.bytesBase64);if(btoa(binary)!==value.bytesBase64)throw Error('Canonical original base64 required');
 const raw=Uint8Array.from(binary,c=>c.charCodeAt(0));
 if(await digest(raw)!==value.bytesSha256)throw Error('Original journal bytes required');
 const utf8=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(raw);return {mediaType:'application/json',utf8,sha256:value.bytesSha256};
}
export function createFeed(db:PGlite,info:StoreInfo,isOpen:()=>boolean,fence:()=>void){
 return async(input:FeedInput):Promise<FeedPage>=>{
  if(!isOpen())return {status:'refused',code:'STORE_NOT_OPEN'};
  if(input.cursor&&(input.cursor.storeId!==info.storeId||input.cursor.incarnation!==info.incarnation))return {status:'refused',code:'CURSOR_SCOPE'};
  const after=input.cursor?.afterSeq??'0',cursor=(seq:string):FeedCursor=>({profile:'truss-browser-feed-cursor/0.1',storeId:info.storeId,incarnation:info.incarnation,afterSeq:seq});
  try{
   return await db.transaction<FeedPage>(async tx=>{
    await tx.exec('SET TRANSACTION READ ONLY');await journalHorizon(tx,false);
    const catalog=await readCatalog(tx);
    const sizes=(await tx.query<{seq:string;n:string}>('SELECT seq::text, (octet_length(new_value::text)+octet_length(origin::text))::text AS n FROM truss.journal j WHERE j.seq>$1::bigint ORDER BY j.seq LIMIT $2::int',[after,input.limit+1])).rows;
    let previous=BigInt(after);for(const row of sizes){if(!unsigned(row.seq)||row.seq==='0'||BigInt(row.seq)<=previous)throw Error('Strict original sequence order required');previous=BigInt(row.seq);}
    if(sizes.slice(0,input.limit).reduce((n,r)=>n+BigInt(r.n),0n)>8388608n)throw new ReadLimit();
    const rows=(await tx.query<any>(`SELECT seq::text,xid::text,to_char(at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') AS at,
     entity_kind,entity_id::text,entity_type::text,ver::text,op,prop_id::text,old_value,new_value,origin,rev::text
     FROM truss.journal j WHERE j.seq>$1::bigint ORDER BY j.seq LIMIT $2::int`,[after,input.limit])).rows;
    if(rows.length!==Math.min(sizes.length,input.limit)||rows.some((r,i)=>r.seq!==sizes[i]!.seq))throw Error('Coherent original journal page required');
    if(!catalog&&rows.length)throw Error('Original accepted journal source required');
    let metadata:Awaited<ReturnType<typeof targetSource>>|undefined,target:JournalEntry['target']|undefined;
    if(catalog){const types=catalog.types as any[];if(types.length!==1)throw Error('Single original browser Record required');target={documentId:types[0].documentId,module:types[0].moduleId,record:types[0].recordId};metadata=await targetSource(catalog,target);}
    const events:JournalEntry[]=[];
    for(const row of rows){
     if(row.entity_kind!=='o'||row.old_value!==null||!unsigned(row.entity_id)||row.entity_id==='0'||!unsigned(row.ver)||row.ver==='0'||!unsigned(row.xid,18446744073709551615n)||row.xid==='0'||row.entity_type!==metadata!.type.typeId)throw Error('Original physical journal identity required');
     const event=await originalEnvelope(row.new_value,'event'),origin=await originalEnvelope(row.origin,'origin'),value=JSON.parse(event.utf8),originValue=JSON.parse(origin.utf8);
     const create=row.op==='create'&&row.prop_id===null,property=row.op==='update'&&row.prop_id!==null;
     if(!create&&!property)throw Error('Supported browser journal operation required');
     exact(value,create?['interfaceVersion','historyProfile','operation','storeId','incarnation','request','inputIndex','xid','seq','identity','eventVersion','eventCatalogRevision','origin','after']:['interfaceVersion','historyProfile','operation','storeId','incarnation','job','batch','inputIndex','xid','seq','identity','eventVersion','eventCatalogRevision','propertyId','origin','before','after','oldValue','newValue']);
     exact(value.identity,['id','typeId','version']);
     if(value.interfaceVersion!=='truss-browser-history-event/0.1'||value.historyProfile!==(create?'truss-browser-create/0.1':'truss-browser-set/0.1')||value.operation!==(create?'create':'property')||value.storeId!==info.storeId||value.incarnation!==info.incarnation||value.seq!==row.seq||value.xid!==row.xid||value.identity.id!==row.entity_id||value.identity.typeId!==row.entity_type||value.identity.version!==row.ver||value.eventVersion!==row.ver||value.eventCatalogRevision!==row.rev||row.rev!==catalog!.catalogRevision||JSON.stringify(value.origin)!==JSON.stringify(originValue)||originValue.profile!=='truss-browser-local-origin/0.1'||originValue.storeId!==info.storeId||originValue.incarnation!==info.incarnation)throw Error('Original event/row/origin correspondence required');
     if(typeof value.inputIndex!=='string'||!/^(0|[1-9][0-9]{0,3})$/.test(value.inputIndex))throw Error('Original bounded input index required');
     let context:JournalContext;
     if(create){exact(originValue,['profile','storeId','incarnation']);context={kind:'load',request:captureSeal(value.request),index:value.inputIndex};}
     else{
      exact(originValue,['profile','storeId','incarnation','job','batch','item']);exact(value.job,['namespace','id']);
      if(value.job.namespace!==info.storeId||typeof value.job.id!=='string'||!/^[A-Za-z0-9_-]{1,128}$/.test(value.job.id)||!Number.isInteger(value.batch)||value.batch<0||value.batch>9999||originValue.batch!==value.batch||originValue.item!==Number(value.inputIndex)||JSON.stringify(originValue.job)!==JSON.stringify(value.job))throw Error('Original batch origin required');
      context={kind:'batch',job:value.job,batch:value.batch,item:originValue.item};
     }
     const logical=(image:any,version:string):LogicalJournalObject=>{
      exact(image,['interfaceVersion','kind','identity','recordVersion','catalogRevision','documentSha256','createdAt','updatedAt','properties','retained','ownership']);exact(image.identity,['id','typeId','version']);exact(image.ownership,['state']);
      if(image.interfaceVersion!=='truss-browser-history-record/0.1'||image.kind!=='object'||image.identity.id!==row.entity_id||image.identity.typeId!==row.entity_type||image.identity.version!==version||image.recordVersion!==version||image.catalogRevision!==row.rev||image.documentSha256!==catalog!.document.sourceSha256||typeof image.createdAt!=='string'||typeof image.updatedAt!=='string'||!Array.isArray(image.properties)||image.properties.length!==metadata!.members.length||!Array.isArray(image.retained)||image.retained.length||image.ownership.state!=='rootless')throw Error('Complete original browser image required');
      const fields=metadata!.members.map((member:any,i:number)=>{const property=image.properties[i];exact(property,['propertyId','value']);exact(property.value,['kind','text']);if(property.propertyId!==member.propertyId||property.value.kind!=='string'||typeof property.value.text!=='string')throw Error('Original declared member order/value required');const prop=(catalog!.properties as any[]).find(p=>p.propertyId===member.propertyId);return {module:member.module,field:member.element,name:prop.name,value:property.value.text};});
      return {id:row.entity_id,typeId:row.entity_type,version,createdAt:image.createdAt,updatedAt:image.updatedAt,fields};
     };
     const afterImage=logical(value.after,row.ver);let before:LogicalJournalObject|null=null,change:JournalEntry['change']=null;
     if(property){
      if(value.propertyId!==row.prop_id||BigInt(row.ver)<2n)throw Error('Original property/version correspondence required');before=logical(value.before,(BigInt(row.ver)-1n).toString());
      exact(value.oldValue,['string']);exact(value.newValue,['string']);const index=metadata!.members.findIndex((m:any)=>m.propertyId===row.prop_id);if(index<0||value.oldValue.string!==before.fields[index]!.value||value.newValue.string!==afterImage.fields[index]!.value)throw Error('Original property values required');const field=afterImage.fields[index]!;change={module:field.module,field:field.field,name:field.name,before:value.oldValue.string,after:value.newValue.string};
     }else if(row.ver!=='1')throw Error('Original creation version required');
     events.push({context,sequence:row.seq,transactionId:row.xid,at:row.at,operation:create?'create':'property',catalogRevision:row.rev,target:target!,before,after:afterImage,change,event,origin});
    }
    const result:FeedPage={status:'page',profile:'truss-browser-journal-page/0.1',events,cursor:cursor(rows.at(-1)?.seq??after),hasMore:sizes.length>input.limit};
    if(bytes(JSON.stringify(result)).length>8388608)throw new ReadLimit();if(!isOpen())throw new NotOpen();return result;
   });
  }catch(error){if(error instanceof ReadLimit)return {status:'refused',code:'READ_LIMIT'};if(error instanceof NotOpen)return {status:'refused',code:'STORE_NOT_OPEN'};fence();throw error;}
 };
}
