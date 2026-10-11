/** Complete original value positions with explicitly incomplete assertion interpretation. */
import {indexSourceJsonOccurrences,originalSourceOccurrenceBytes} from '../../postgresql/src/acceptance-json';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import {collectCatalogCoreAssertionIdentities} from './catalog-core-assertion-identities';
import type {collectCatalogAssertionObservations} from './catalog-assertion-observations';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type Collection=ReturnType<typeof collectCatalogAssertionObservations>;
type Index=ReturnType<typeof indexSourceJsonOccurrences>;
const issued=new WeakMap<object,{prepared:Prepared;indexes:readonly Index[]}>();
export function collectCatalogOriginalOccurrenceInventory(prepared:Prepared,collection:Collection){
 requireOriginalCatalogPreparation(prepared);
 // This call also requires original observation collection custody. No caller supplied classifications.
 const core=collectCatalogCoreAssertionIdentities(prepared,collection),indexes:Index[]=[];
 const documents=prepared.documents.map((document,position)=>{
  const source=prepared.original.input.documents[position]!.artifact;
  const index=indexSourceJsonOccurrences(Buffer.from(source.bytesBase64,'base64'));indexes.push(index);
  const byPointer=new Map<string,typeof core.entries[number][]>();
  for(const entry of core.entries){if(entry.assertion.owner.documentId!==document.documentId)continue;
   if(entry.source!==source)throw Error('Original assertion artifact correspondence required');
   const rows=byPointer.get(entry.assertion.sourcePointer)??[];rows.push(entry);byPointer.set(entry.assertion.sourcePointer,rows);
  }
  const linkPointers=new Map<string,typeof core.referenceLinks[number][]>(),declarationPointers=new Map<string,typeof core.referenceLinkDeclarations[number][]>();
  for(const [rows,map] of [[core.referenceLinks,linkPointers],[core.referenceLinkDeclarations,declarationPointers]] as const)for(const link of rows){
   if(link.documentId!==document.documentId)continue;
   if(link.source!==source)throw Error('Original reference-link artifact correspondence required');
   const found=map.get(link.sourcePointer)??[];found.push(link);map.set(link.sourcePointer,found);
  }
  const remainingLinks=new Set([...linkPointers.keys(),...declarationPointers.keys()]);
  const remaining=new Set(byPointer.keys());
  const occurrences=index.occurrences.map(value=>{
   const assertions=byPointer.get(value.pointer)??[];remaining.delete(value.pointer);remainingLinks.delete(value.pointer);
   return Object.freeze({...value,sourceSha256:source.sha256,owner:Object.freeze({scope:'document' as const,documentId:document.documentId}),
    disposition:assertions.length?'assertion' as const:'unavailable' as const,
    interpretationState:assertions.length?'partial' as const:'unavailable' as const,assertionMembershipComplete:false as const,
    assertions:Object.freeze([...assertions]),referenceLinks:Object.freeze([...(linkPointers.get(value.pointer)??[])]),referenceLinkDeclarations:Object.freeze([...(declarationPointers.get(value.pointer)??[])]),reason:assertions.length?'original_inspected_core_subset' as const:'original_semantic_classification_unavailable' as const});
  });
  if(remaining.size)throw Error('Every original assertion pointer must occur in original source');
  if(remainingLinks.size)throw Error('Every original reference-link pointer must occur in original source');
  return Object.freeze({documentId:document.documentId,sourceVersion:document.umfVersion,source,originalByteLength:index.originalByteLength,occurrences:Object.freeze(occurrences)});
 });
 const result=Object.freeze({documents:Object.freeze(documents),core,sourceCoverageComplete:true as const,complete:false as const,
  interpretationQualified:false as const,scope:'complete_original_json_values_partial_assertion_interpretation' as const});
 issued.set(result,{prepared,indexes:Object.freeze(indexes)});return result;
}
type Inventory=ReturnType<typeof collectCatalogOriginalOccurrenceInventory>;
export function originalCatalogOccurrenceBytes(prepared:Prepared,inventory:Inventory,documentPosition:number,occurrencePosition:number):Uint8Array{
 requireOriginalCatalogPreparation(prepared);const custody=issued.get(inventory);
 if(!custody||custody.prepared!==prepared)throw Error('Original catalog occurrence inventory custody required');
 if(!Number.isSafeInteger(documentPosition)||documentPosition<0||documentPosition>=custody.indexes.length)throw Error('Original document occurrence position required');
 return originalSourceOccurrenceBytes(custody.indexes[documentPosition]!,occurrencePosition);
}
