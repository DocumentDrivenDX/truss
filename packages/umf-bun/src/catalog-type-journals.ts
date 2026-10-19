// SPDX-License-Identifier: MIT OR Apache-2.0
/** Private original journal ingress; no issuer, accepted-report or enforcement authority. */
import {createTypeJournalEvidenceBudget} from './catalog-type-journal-evidence-budget';
import {createHash} from 'node:crypto';
import {copyOriginalByteCustody} from '../../postgresql/src/original-byte-custody';
import {decodeAcceptanceJson,indexSourceJsonOccurrences,originalSourceOccurrenceBytes} from '../../postgresql/src/acceptance-json';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import {requireLoadedUmfAssertionOwner,type loadUmfRecordTypeJournalProducer} from './index';
import {parseOriginalReceiptJson,freezeInertReceiptJson,sameReceiptMeaning} from './catalog-receipt-json';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type Owner=Awaited<ReturnType<typeof loadUmfRecordTypeJournalProducer>>;
const issued=new WeakMap<object,Prepared>(),sha=(b:Uint8Array)=>createHash('sha256').update(b).digest('hex');
function object(v:any,keys:readonly string[]):void{if(!v||typeof v!=='object'||Array.isArray(v)||Object.keys(v).length!==keys.length||keys.some(k=>!Object.hasOwn(v,k)))throw Error('Original type journal request shape required')}
function text(v:unknown):asserts v is string{if(typeof v!=='string'||!v||v.length>4096)throw Error('Original type journal identity required')}
export function requireOriginalCatalogTypeJournals(prepared:Prepared,collection:object):void{
 requireOriginalCatalogPreparation(prepared);if(issued.get(collection)!==prepared)throw Error('Original type journal collection custody required');
}
/** Whole original-byte packet refuses atomically. Bounds count retained evidence, not whole-operation heap/CPU. */
export function collectCatalogTypeJournals(prepared:Prepared,owner:Owner,originalRequests:Uint8Array){
 requireOriginalCatalogPreparation(prepared);requireLoadedUmfAssertionOwner(owner,'record-type-journals');
 const wire=copyOriginalByteCustody(originalRequests,true),requests=decodeAcceptanceJson(wire) as any;object(requests,['version','journals']);
 if(requests.version!=='0.1.0'||!Array.isArray(requests.journals)||requests.journals.length>64)throw Error('Original type journal request profile/capacity required');
 freezeInertReceiptJson(requests);
 const ownerProfile=Object.freeze({identity:'umf-record-type-journal-inspection',version:owner.sourceRevision,sha256:owner.bundleSha256});
 const journals=[],entries=[],budget=createTypeJournalEvidenceBudget();budget.charge(wire.length);const documents=new Set<string>(),artifactIds=new Set<string>();
 for(const request of requests.journals){
  object(request,['documentId','documentRevision','artifact']);text(request.documentId);text(request.documentRevision);object(request.artifact,['identity','bytesBase64','sha256']);text(request.artifact.identity);
  const di=prepared.documents.findIndex(d=>d.documentId===request.documentId),document=prepared.documents[di],input=prepared.original.input.documents[di];
  if(!document||document.revision!==request.documentRevision||input!.documentRevision!==request.documentRevision||document.umfVersion!=='0.7.0')throw Error('Original type journal document/revision/profile correspondence required');
  if(documents.has(request.documentId)||artifactIds.has(request.artifact.identity))throw Error('Duplicate original type journal document/artifact');documents.add(request.documentId);artifactIds.add(request.artifact.identity);
  const artifact=request.artifact;
  if(typeof artifact.bytesBase64!=='string'||artifact.bytesBase64.length>1398104||typeof artifact.sha256!=='string'||!/^[0-9a-f]{64}$/.test(artifact.sha256))throw Error('Original type journal artifact required');
  const bytes=Buffer.from(artifact.bytesBase64,'base64');if(bytes.length>1048576||bytes.toString('base64')!==artifact.bytesBase64||sha(bytes)!==artifact.sha256)throw Error('Original type journal artifact correspondence required');
  budget.charge(bytes.length);
  const journal=parseOriginalReceiptJson(bytes) as any;freezeInertReceiptJson(journal);object(journal,['version','base','events']);
  if(journal.version!=='0.1.0'||journal.base?.umf!=='0.7.0'||!Array.isArray(journal.events)||journal.events.length<1||journal.events.length>32)throw Error('Original type journal event profile/capacity required');
  const source=document.interpretation.source;
  const result=owner.inspectRecordTypeJournal(journal.base,source,journal.events);freezeInertReceiptJson(result);
  const types=[];
  for(const [eventIndex,event] of journal.events.entries()){
   if(event.version!=='6.0.0'||!['declare-core-kind','declare-core-record-type'].includes(event.operation))throw Error('Original type journal event profile required');
   if(event.operation==='declare-core-kind')continue;
   const identity=event.fieldAuthor?.identity,mi=source.modules.findIndex((m:any)=>m.id===identity?.module),ei=source.modules[mi]?.elements.findIndex((e:any)=>e.id===identity?.element)??-1;
   const element=source.modules[mi]?.elements[ei],index=element?.references?.findIndex((_:unknown,i:number)=>`/modules/${mi}/elements/${ei}/references/${i}`===event.provenance?.idealPath),path=event.provenance?.idealPath,reference=element?.references?.[index];
   const ti=source.modules.findIndex((m:any)=>m.id===event.reference?.module),te=source.modules[ti]?.elements.findIndex((e:any)=>e.id===event.reference?.element)??-1,target=source.modules[ti]?.elements[te],recordPath=`/modules/${ti}/elements/${te}`;
   if(mi<0||ei<0||ti<0||te<0||index<0||element.kind!=='field'||target.kind!=='record'||reference?.role!=='record-type'||!sameReceiptMeaning(reference,event.reference)||recordPath!==event.provenance?.recordPath)throw Error('Original type journal qualified current link required');
   const uninterpretedPaths=document.validation.sourceValidation.diagnostics.filter((d:any)=>d.severity==='warning'&&d.code==='UNKNOWN_CORE_FIELD'&&(d.path===path||d.path.startsWith(path+'/'))).map((d:any)=>d.path);
   types.push({eventIndex,identity,path,recordPath,link:{index,path,reference,target:{identity:{module:reference.module,element:reference.element},path:recordPath,kind:'record'},uninterpretedPaths,typeAssertion:'unverified'},receipt:event});
  }
  const expected={operation:'inspect-core-record-type-journal',version:'0.1.0',base:journal.base,source,events:journal.events,types,receiptConsistency:'verified',issuerAuthority:'unverified',enforcement:'none'};
  if(!sameReceiptMeaning(result,expected))throw Error('Original type journal full owner result correspondence required');
  const originalSource=input!.artifact,sourceIndex=indexSourceJsonOccurrences(Buffer.from(originalSource.bytesBase64,'base64'));
  const evidenceBytes=Buffer.from(JSON.stringify({ownerProfile,documentId:request.documentId,documentRevision:request.documentRevision,originalSourceSha256:originalSource.sha256,journalArtifact:artifact,result}));
  budget.charge(evidenceBytes.length);
  const ownerEvidence:Readonly<{identity:string;bytesBase64:string;sha256:string}>=Object.freeze({identity:'truss.original-type-journal-observation/'+journals.length,bytesBase64:evidenceBytes.toString('base64'),sha256:sha(evidenceBytes)});
  const common={documentId:request.documentId as string,documentRevision:request.documentRevision as string,source:originalSource,ownerProfile,journalArtifact:artifact as Readonly<{identity:string;bytesBase64:string;sha256:string}>,ownerEvidence,receiptConsistency:'verified' as const,issuerAuthority:'unverified' as const,enforcement:'none' as const,interpretationQualified:false as const};
  journals.push(Object.freeze({...common,ownerMeaning:result as unknown}));
  for(const type of (result as any).types){
   const position=sourceIndex.occurrences.findIndex(row=>row.pointer===type.path);if(position<0)throw Error('Original type journal pointer occurrence required');
   entries.push(Object.freeze({...common,eventIndex:type.eventIndex as number,eventPointer:'/events/'+type.eventIndex,identity:type.identity as Readonly<{module:string;element:string}>,sourcePointer:type.path as string,originalMeaning:type as unknown,originalReferenceBytesBase64:Buffer.from(originalSourceOccurrenceBytes(sourceIndex,position)).toString('base64')}));
  }
 }
 const requestArtifact=Object.freeze({identity:'truss.original-type-journal-requests',bytesBase64:Buffer.from(wire).toString('base64'),sha256:sha(wire)});
 const collection=Object.freeze({ownerProfile,requestArtifact,journals:Object.freeze(journals),entries:Object.freeze(entries),complete:false as const,issuerAuthority:'unverified' as const,enforcement:'none' as const,scope:'original_explicit_type_journal_ingress_correspondence_only' as const});issued.set(collection,prepared);return collection;
}
