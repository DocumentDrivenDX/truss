/** Owner observations for report preparation, never complete assertion/enforcement admission. */
import {createHash} from 'node:crypto';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import {requireLoadedUmfAssertionOwner,type loadUmfDeclarationProducer,type loadUmfFieldAssertionProducer} from './index';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
const originalCollections=new WeakMap<object,Prepared>();
/** Private in-process issuance correspondence; not native or durable authority. */
export function requireOriginalCatalogObservationCollection(prepared:Prepared,collection:object):void{
 if(originalCollections.get(collection)!==prepared)throw Error('Original observation collection custody required');
}
type Owner=Awaited<ReturnType<typeof loadUmfDeclarationProducer>>;
export function collectCatalogAssertionObservations(prepared:Prepared,owner:Owner,fields?:Awaited<ReturnType<typeof loadUmfFieldAssertionProducer>>){
 requireOriginalCatalogPreparation(prepared);
 requireLoadedUmfAssertionOwner(owner,'declarations');
 if(fields)requireLoadedUmfAssertionOwner(fields,'assertion-fields');
 if(owner.sourceRevision!==prepared.umfProfile.version)throw Error('Original owner observation source mismatch');
 if(fields&&fields.sourceRevision!==prepared.umfProfile.version)throw Error('Original Field owner observation source mismatch');
 const fieldProfile=fields?Object.freeze({identity:'umf-field-assertion-inspection',version:fields.sourceRevision,sha256:fields.bundleSha256}):null;
 const profile=Object.freeze({identity:'umf-declaration-inspection',version:owner.sourceRevision,sha256:owner.bundleSha256});
 const observations:{documentId:string;basis:'original'|'reversible_target';operation:string;identity:unknown;result:unknown;evidence:{identity:string;bytesBase64:string;sha256:string}}[]=[];let retainedBytes=0;let calls=0;
 function capture(documentIndex:number,operation:string,identity:unknown,basis:'original'|'reversible_target',run:()=>unknown,observationProfile:{readonly identity:string;readonly version:string;readonly sha256:string}=profile){
  if(++calls>4096)throw Error('Declaration observation component call capacity exceeded');
  const document=prepared.documents[documentIndex];let result:unknown;
  try{result={state:'observed',observation:run()}}catch(error){result={state:'unavailable',name:error instanceof Error?error.name:null,code:typeof (error as any)?.code==='string'?(error as any).code:null,path:typeof (error as any)?.path==='string'?(error as any).path:null,message:error instanceof Error?error.message:String(error)}}
  const bytes=Buffer.from(JSON.stringify({profile:observationProfile,documentId:document.documentId,contentSha256:prepared.original.documents[documentIndex].sha256,basis,operation,identity,result}),'utf8');
  retainedBytes+=bytes.length;if(retainedBytes>4194304)throw Error('Declaration observation component output capacity exceeded');
  observations.push(Object.freeze({documentId:document.documentId,basis,operation,identity,result,
   evidence:Object.freeze({identity:'truss.owner-declaration-observation/'+documentIndex+'/'+(calls-1),bytesBase64:bytes.toString('base64'),sha256:createHash('sha256').update(bytes).digest('hex')})}));
 }
 for(let index=0;index<prepared.documents.length;index++){
  const document=prepared.documents[index];const source=document.interpretation.source;const target=document.interpretation.target;const propertyBasis=document.interpretation.transition?'reversible_target' as const:'original' as const;
  capture(index,'schema_properties',{scope:'document'},propertyBasis,()=>owner.inspectSchemaProperties(target,{scope:'document'}));
  for(const module of source.modules){
   const moduleIdentity={scope:'module',module:module.id};
   capture(index,'schema_properties',moduleIdentity,propertyBasis,()=>owner.inspectSchemaProperties(target,moduleIdentity));
   capture(index,'relationships',{module:module.id},'original',()=>owner.inspectRelationships(source,{module:module.id}));
   for(const element of module.elements){
    const identity={scope:'element',module:module.id,element:element.id};
    capture(index,'schema_properties',identity,propertyBasis,()=>owner.inspectSchemaProperties(target,identity));
    if(fields){const fieldIdentity={module:module.id,element:element.id};for(const [operation,inspect] of [['kind',fields.inspectKind],['nullability',fields.inspectNullability],['cardinality',fields.inspectCardinality],['facets',fields.inspectFacets]] as const)capture(index,operation,fieldIdentity,'original',()=>inspect(source,fieldIdentity),fieldProfile!);}
    if(element.kind==='record')capture(index,'keys',{module:module.id,element:element.id},'original',()=>owner.inspectKeys(source,{module:module.id,element:element.id}));
   }
  }
 }
 function freeze(value:unknown):void{if(value&&typeof value==='object'){for(const child of Object.values(value))freeze(child);Object.freeze(value)}}freeze(observations);
 const collection=Object.freeze({profile,fieldProfile,observations:Object.freeze(observations),scope:'original_owner_assertion_observations_only' as const});
 originalCollections.set(collection,prepared);return collection;
}
