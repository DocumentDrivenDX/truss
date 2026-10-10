/** Private original supplied-source ordering; no registered extension or acceptance authority. */
import {createCatalogEndpointIntentBasis} from './catalog-endpoint-intent-basis';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import {orderCatalogDocuments} from './catalog-document-order';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
export async function createCatalogEndpointDocumentOrder(dependenciesPackage:string){
 const basis=await createCatalogEndpointIntentBasis(dependenciesPackage);
 return Object.freeze({order(prepared:Prepared,maximumOccurrences:number,limits:Parameters<typeof orderCatalogDocuments>[2]){
  requireOriginalCatalogPreparation(prepared);
  // Charge the complete original set, including documents with no candidate extension.
  if(!Number.isSafeInteger(limits.documents)||limits.documents<0||prepared.documents.length>limits.documents)throw Error('Selected document bound exceeded');
  const nodes=prepared.documents.map(document=>document.documentId);
  orderCatalogDocuments(nodes,[],limits); // Validate identities and every selected bound before collecting references.
  const originalBasis=basis.collect(prepared,maximumOccurrences);
  const edges:(readonly [string,string])[]=[];
  for(const document of originalBasis.documents)for(const occurrence of document.referenceOccurrences){
   if(occurrence.kind==='dependency'){
    if(edges.length>=limits.edges)throw Error('Selected graph bound exceeded');
    edges.push([document.documentId,occurrence.selection.document]);
   }
  }
  const graph=orderCatalogDocuments(nodes,edges,limits);
  const byId=new Map(prepared.documents.map(document=>[document.documentId,document]));
  return Object.freeze({originalBasis,components:graph.components,
   documents:Object.freeze(graph.order.map(id=>byId.get(id)!)),
   scope:'original_supplied_endpoint_dependency_order_only' as const});
 }});
}
