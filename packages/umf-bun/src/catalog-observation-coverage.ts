/** Observation correspondence only: never an enforcement or complete assertion report. */
import {createHash} from 'node:crypto';
import type {createCatalogInputPreparation} from './catalog-input';
import {requireOriginalCatalogObservationCollection,type collectCatalogAssertionObservations} from './catalog-assertion-observations';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type Collection=ReturnType<typeof collectCatalogAssertionObservations>;
export function assessCatalogObservationCoverage(prepared:Prepared,collection:Collection){
 requireOriginalCatalogObservationCollection(prepared,collection);
 if(!collection.fieldProfile)throw Error('Complete Field observation bundle required');
 for(const [profile,identity] of [[collection.profile,'umf-declaration-inspection'],[collection.fieldProfile,'umf-field-assertion-inspection']] as const)
  if(profile.identity!==identity||profile.version!==prepared.umfProfile.version||!/^[0-9a-f]{64}$/.test(profile.sha256))throw Error('Original observation profile correspondence required');
 const expected:{documentIndex:number;operation:string;identity:unknown;basis:'original'|'reversible_target';field:boolean}[]=[];
 const add=(documentIndex:number,operation:string,identity:unknown,basis:'original'|'reversible_target',field=false)=>{
  if(expected.length>=4096)throw Error('Observation coverage component capacity exceeded');expected.push({documentIndex,operation,identity,basis,field});
 };
 for(let i=0;i<prepared.documents.length;i++){
  const document=prepared.documents[i],source=document.interpretation.source,basis=document.interpretation.transition?'reversible_target':'original';
  add(i,'schema_properties',{scope:'document'},basis);
  for(const module of source.modules){
   add(i,'schema_properties',{scope:'module',module:module.id},basis);add(i,'relationships',{module:module.id},'original');
   for(const element of module.elements){
    add(i,'schema_properties',{scope:'element',module:module.id,element:element.id},basis);
    for(const operation of ['kind','nullability','cardinality','facets'])add(i,operation,{module:module.id,element:element.id},'original',true);
    if(element.kind==='record')add(i,'keys',{module:module.id,element:element.id},'original');
   }
  }
 }
 if(collection.observations.length!==expected.length)throw Error('Complete original observation inventory required');
 const unavailable:{documentId:string;operation:string;identity:unknown;code:string|null;path:string|null}[]=[];let bytesRetained=0;
 for(let index=0;index<expected.length;index++){
  const requirement=expected[index],observed=collection.observations[index],document=prepared.documents[requirement.documentIndex];
  if(observed.documentId!==document.documentId||observed.operation!==requirement.operation||observed.basis!==requirement.basis||JSON.stringify(observed.identity)!==JSON.stringify(requirement.identity))throw Error('Original ordered observation identity/basis mismatch');
  const result=observed.result as {state?:unknown;code?:unknown;path?:unknown};
  if(!result||!['observed','unavailable'].includes(result.state as string))throw Error('Explicit observation availability required');
  const original=JSON.stringify({profile:requirement.field?collection.fieldProfile:collection.profile,documentId:document.documentId,contentSha256:prepared.original.documents[requirement.documentIndex].sha256,basis:requirement.basis,operation:requirement.operation,identity:requirement.identity,result:observed.result});
  const bytes=Buffer.from(original,'utf8');bytesRetained+=bytes.length;if(bytesRetained>4194304)throw Error('Observation coverage evidence capacity exceeded');
  if(observed.evidence.bytesBase64!==bytes.toString('base64')||observed.evidence.sha256!==createHash('sha256').update(bytes).digest('hex')||observed.evidence.identity!=='truss.owner-declaration-observation/'+requirement.documentIndex+'/'+index)throw Error('Original observation evidence correspondence required');
  if(result.state==='unavailable'){
   if(!(result.code===null||typeof result.code==='string')||!(result.path===null||typeof result.path==='string'))throw Error('Original unavailable result required');
   unavailable.push(Object.freeze({documentId:document.documentId,operation:requirement.operation,identity:Object.freeze(requirement.identity as object),code:result.code,path:result.path}));
  }
 }
 return Object.freeze({observationsRequired:String(expected.length),observationsAvailable:String(expected.length-unavailable.length),unavailable:Object.freeze(unavailable),availability:unavailable.length?'incomplete' as const:'available' as const,scope:'original_owner_observation_correspondence_only' as const});
}
