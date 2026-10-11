/** Private original type receipt ingress/report candidate; never issuer or admission authority. */
import {createHash} from 'node:crypto';
import {copyOriginalByteCustody} from '../../postgresql/src/original-byte-custody';
import {decodeAcceptanceJson,indexSourceJsonOccurrences,originalSourceOccurrenceBytes} from '../../postgresql/src/acceptance-json';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import {requireLoadedUmfAssertionOwner,type loadUmfRecordTypeReceiptProducer} from './index';
import {parseOriginalReceiptJson,freezeInertReceiptJson,sameReceiptMeaning} from './catalog-receipt-json';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type Owner=Awaited<ReturnType<typeof loadUmfRecordTypeReceiptProducer>>;
const issued=new WeakMap<object,Prepared>();
const sha=(b:Uint8Array)=>createHash('sha256').update(b).digest('hex');
function object(v:any,keys:readonly string[]):void{if(!v||typeof v!=='object'||Array.isArray(v)||Object.keys(v).length!==keys.length||keys.some(k=>!Object.hasOwn(v,k)))throw Error('Original type receipt request shape required')}
function text(v:unknown):asserts v is string{if(typeof v!=='string'||!v||v.length>4096)throw Error('Original type receipt identity required')}
export function requireOriginalCatalogTypeReceipts(prepared:Prepared,collection:object):void{
 requireOriginalCatalogPreparation(prepared);if(issued.get(collection)!==prepared)throw Error('Original type receipt collection custody required');
}
/** Closed private requests are original bytes, not mutable caller objects. The whole packet refuses on any invalid receipt. */
export function collectCatalogTypeReceipts(prepared:Prepared,owner:Owner,originalRequests:Uint8Array){
 requireOriginalCatalogPreparation(prepared);requireLoadedUmfAssertionOwner(owner,'record-type-receipts');
 const wire=copyOriginalByteCustody(originalRequests,true),requests=decodeAcceptanceJson(wire) as any;object(requests,['version','receipts']);
 if(requests.version!=='0.1.0'||!Array.isArray(requests.receipts)||requests.receipts.length>64)throw Error('Original type receipt request profile/capacity required');
 freezeInertReceiptJson(requests);
 const ownerProfile=Object.freeze({identity:'umf-record-type-receipt-inspection',version:owner.sourceRevision,sha256:owner.bundleSha256}),entries=[];let retained=wire.length;const owners=new Set<string>(),artifactIds=new Set<string>();
 for(const request of requests.receipts){
  object(request,['documentId','documentRevision','field','artifact']);text(request.documentId);text(request.documentRevision);object(request.field,['module','element']);text(request.field.module);text(request.field.element);object(request.artifact,['identity','bytesBase64','sha256']);text(request.artifact.identity);
  const di=prepared.documents.findIndex(d=>d.documentId===request.documentId),document=prepared.documents[di],input=prepared.original.input.documents[di];
  if(!document||document.revision!==request.documentRevision||input!.documentRevision!==request.documentRevision)throw Error('Original type receipt document/revision correspondence required');
  const identity=Object.freeze({module:request.field.module as string,element:request.field.element as string}),key=JSON.stringify([request.documentId,identity]);
  if(owners.has(key)||artifactIds.has(request.artifact.identity))throw Error('Duplicate original type receipt owner/artifact');owners.add(key);artifactIds.add(request.artifact.identity);
  const artifact=request.artifact;
  if(typeof artifact.bytesBase64!=='string'||artifact.bytesBase64.length>1398104||typeof artifact.sha256!=='string'||!/^[0-9a-f]{64}$/.test(artifact.sha256))throw Error('Original type receipt artifact required');
  const bytes=Buffer.from(artifact.bytesBase64,'base64');if(bytes.toString('base64')!==artifact.bytesBase64||sha(bytes)!==artifact.sha256||bytes.length>1048576)throw Error('Original type receipt artifact correspondence required');
  retained+=bytes.length;if(retained>4194304)throw Error('Type receipt ingress evidence capacity exceeded');
  const receipt=parseOriginalReceiptJson(bytes) as any;freezeInertReceiptJson(receipt);
  const source=document.interpretation.source;
  if(!receipt||!sameReceiptMeaning(receipt.target,source)||!sameReceiptMeaning(receipt.fieldAuthor?.identity,identity))throw Error('Original type receipt current/Field correspondence required');
  const result=owner.inspectRecordTypeReceipt(source,identity,receipt);freezeInertReceiptJson(result);
  const mi=source.modules.findIndex((m:any)=>m.id===identity.module),ei=source.modules[mi]?.elements.findIndex((e:any)=>e.id===identity.element)??-1;
  const element=source.modules[mi]?.elements[ei],index=element?.references?.length-1,path=`/modules/${mi}/elements/${ei}/references/${index}`,reference=element?.references?.[index];
  const ti=source.modules.findIndex((m:any)=>m.id===receipt.reference?.module),te=source.modules[ti]?.elements.findIndex((e:any)=>e.id===receipt.reference?.element)??-1,target=source.modules[ti]?.elements[te],recordPath=`/modules/${ti}/elements/${te}`;
  if(mi<0||ei<0||ti<0||te<0||element.kind!=='field'||target.kind!=='record'||reference?.role!=='record-type'||!sameReceiptMeaning(reference,receipt.reference))throw Error('Original type receipt qualified authored link required');
  const uninterpretedPaths=document.validation.sourceValidation.diagnostics.filter((d:any)=>d.severity==='warning'&&d.code==='UNKNOWN_CORE_FIELD'&&(d.path===path||d.path.startsWith(path+'/'))).map((d:any)=>d.path);
  const expected={operation:'inspect-core-record-type-receipt',version:'0.1.0',source,identity,path,recordPath,link:{index,path,reference,target:{identity:{module:receipt.reference.module,element:receipt.reference.element},path:recordPath,kind:'record'},uninterpretedPaths,typeAssertion:'unverified'},receipt,receiptConsistency:'verified',issuerAuthority:'unverified',enforcement:'none'};
  if(!sameReceiptMeaning(result,expected))throw Error('Original type receipt full owner result correspondence required');
  const originalSource=input!.artifact,sourceIndex=indexSourceJsonOccurrences(Buffer.from(originalSource.bytesBase64,'base64')),position=sourceIndex.occurrences.findIndex(row=>row.pointer===path);
  if(position<0)throw Error('Original type receipt pointer occurrence required');
  const occurrenceBytes=originalSourceOccurrenceBytes(sourceIndex,position);
  const evidenceBytes=Buffer.from(JSON.stringify({ownerProfile,documentId:request.documentId,documentRevision:request.documentRevision,originalSourceSha256:originalSource.sha256,receiptArtifact:artifact,identity,result}));
  retained+=evidenceBytes.length;if(retained>4194304)throw Error('Type receipt ingress evidence capacity exceeded');
  entries.push(Object.freeze({documentId:request.documentId as string,documentRevision:request.documentRevision as string,identity,source:originalSource,sourcePointer:path,ownerProfile,receiptArtifact:artifact as Readonly<{identity:string;bytesBase64:string;sha256:string}>,ownerMeaning:result as unknown,
   originalReferenceBytesBase64:Buffer.from(occurrenceBytes).toString('base64'),ownerEvidence:Object.freeze({identity:'truss.original-type-receipt-observation/'+entries.length,bytesBase64:evidenceBytes.toString('base64'),sha256:sha(evidenceBytes)}),receiptConsistency:'verified' as const,issuerAuthority:'unverified' as const,enforcement:'none' as const,interpretationQualified:false as const}));
 }
 const requestArtifact=Object.freeze({identity:'truss.original-type-receipt-requests',bytesBase64:Buffer.from(wire).toString('base64'),sha256:sha(wire)});
 const collection=Object.freeze({ownerProfile,requestArtifact,entries:Object.freeze(entries),complete:false as const,issuerAuthority:'unverified' as const,enforcement:'none' as const,scope:'original_exact_current_type_receipt_ingress_correspondence_only' as const});issued.set(collection,prepared);return collection;
}
