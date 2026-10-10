/** Private original Record/key correspondence; no interpretation or native authority. */
import {createCatalogEndpointIntentBasis} from './catalog-endpoint-intent-basis';
import type {createCatalogInputPreparation} from './catalog-input';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type OriginalRecord=Prepared['declarations'][number]['records'][number];
type EndpointCorrespondence=Readonly<{documentId:string;pointer:string;endpoint:any;state:'pending'|'supplied';record:OriginalRecord|null;key:OriginalRecord['keys'][number]|null}>;
export async function createCatalogEndpointRecords(dependenciesPackage:string){
 const basis=await createCatalogEndpointIntentBasis(dependenciesPackage);
 return Object.freeze({resolve(prepared:Prepared,maximumOccurrences:number){
  const originalBasis=basis.collect(prepared,maximumOccurrences),endpoints:EndpointCorrespondence[]=[];
  const owners=new Map<string,typeof prepared.declarations[number]>();
  // Empty documents still have source membership; do not infer ownership from a first Record.
  for(let i=0;i<prepared.documents.length;i++)owners.set(prepared.documents[i].documentId,prepared.declarations[i]);
  for(const document of originalBasis.documents)for(let i=0;i<document.payload.intents.length;i++){
   const intent=document.payload.intents[i],prefix=`/extensions/${basis.extensionId}/intents/${i}`;
   const resolve=(endpoint:any,pointer:string)=>{
    if(endpoint.definition.state==='pending'){
     endpoints.push(Object.freeze({documentId:document.documentId,pointer,endpoint,state:'pending' as const,record:null,key:null}));return;
    }
    const matches=owners.get(endpoint.document)?.records.filter(record=>record.moduleId===endpoint.module&&record.elementId===endpoint.element)??[];
    if(matches.length!==1)throw Error('Exact original endpoint Record correspondence unavailable');
    const record=matches[0];let key:typeof record.keys[number]|null=null;
    if(endpoint.key?.state==='selected'){
     const keys=record.keys.filter(key=>key.name===endpoint.key.name);
     if(keys.length!==1)throw Error('Exact original owning Record key name correspondence unavailable');
     key=keys[0];
    }
    endpoints.push(Object.freeze({documentId:document.documentId,pointer,endpoint,state:'supplied' as const,record,key}));
   };
   for(const slot of ['sources','targets'] as const)for(let j=0;j<intent[slot].length;j++)resolve(intent[slot][j],`${prefix}/${slot}/${j}`);
   if(intent.associationRecord!==null)resolve(intent.associationRecord,prefix+'/associationRecord');
  }
  return Object.freeze({originalBasis,endpoints:Object.freeze(endpoints),scope:'original_supplied_endpoint_record_key_correspondence_only' as const});
 }});
}
