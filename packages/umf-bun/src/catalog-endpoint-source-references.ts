/** Private original supplied-source correspondence, not endpoint/model admission. */
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
export interface EndpointSourceSelection {
 readonly document:string;
 readonly revision:string;
 readonly sourceReference:string;
}
export function resolveCatalogEndpointSuppliedSources(
 prepared:Prepared,contextDocumentId:string,selections:readonly EndpointSourceSelection[],maximumReferences:number,
){
 requireOriginalCatalogPreparation(prepared);
 if(!Number.isSafeInteger(maximumReferences)||maximumReferences<0||!Array.isArray(selections)||selections.length>maximumReferences)
  throw Error('Selected source-reference bound required');
 const declarations=prepared.original.input.documents;
 const context=declarations.filter(document=>document.documentId===contextDocumentId);
 if(context.length!==1)throw Error('Original containing source context required');
 const inventory=new Map<string,typeof declarations[number]>();
 const revisions=new Set<string>();
 for(const declaration of declarations){
  const reference=declaration.artifact.identity;
  const key=JSON.stringify([declaration.documentId,declaration.documentRevision]);
  if(inventory.has(reference)||revisions.has(key))throw Error('Ambiguous original supplied-source inventory');
  inventory.set(reference,declaration);revisions.add(key);
 }
 const matches=selections.map(selection=>{
  if(typeof selection.document!=='string'||!selection.document||typeof selection.revision!=='string'||!selection.revision||typeof selection.sourceReference!=='string'||!selection.sourceReference)
   throw Error('Complete admitted source selection required');
  const original=inventory.get(selection.sourceReference);
  if(!original||original.documentId!==selection.document||original.documentRevision!==selection.revision)
   throw Error('Original supplied document/revision/reference correspondence unavailable');
  if(selection.document===contextDocumentId&&(selection.revision!==context[0]!.documentRevision||selection.sourceReference!==context[0]!.artifact.identity))
   throw Error('Local selection must name its containing original source');
  const document=prepared.documents.filter(item=>item.documentId===original.documentId&&item.revision===original.documentRevision);
  if(document.length!==1)throw Error('Original interpreted source membership unavailable');
  return Object.freeze({documentId:original.documentId,documentRevision:original.documentRevision,
   artifact:Object.freeze({...original.artifact}),originalText:document[0]!.originalText,umfVersion:document[0]!.umfVersion});
 });
 return Object.freeze({matches:Object.freeze(matches),scope:'original_supplied_source_reference_correspondence_only' as const});
}
