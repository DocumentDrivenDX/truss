/** Original inspected core subset. Never a complete enforcement inventory. */
import {createHash} from 'node:crypto';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import {requireOriginalCatalogObservationCollection,type collectCatalogAssertionObservations} from './catalog-assertion-observations';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type Collection=ReturnType<typeof collectCatalogAssertionObservations>;
export function collectCatalogCoreAssertionIdentities(prepared:Prepared,collection:Collection){
 requireOriginalCatalogPreparation(prepared);requireOriginalCatalogObservationCollection(prepared,collection);
 const manifestBytes=Buffer.from(JSON.stringify({interfaceVersion:'truss-core-assertion-source-identity/0.3.0',producers:{fields:collection.fieldProfile,declarations:collection.profile},
  operations:['kind','nullability','cardinality','facets','keys','relationships','schema_properties'],basis:'original',schemaPropertyAssertions:['allowedValues','default','facets'],annotations:'retained separately; not constraint assertions',identity:'original document digest, qualified owner and exact owner-produced pointer',authored:'retain exact declaration ID with full original occurrence pointer',missing:'retained absence observation; no assertion invented',enforcement:'none/unqualified'}));
 const manifest=Object.freeze({identity:'truss.core-assertion-source-identity/0.3.0',bytesBase64:manifestBytes.toString('base64'),sha256:createHash('sha256').update(manifestBytes).digest('hex')});
 const profile=Object.freeze({identity:'truss-core-assertion-source-identity',version:'0.3.0',sha256:manifest.sha256});
 const entries=[];const absent=[];const deferred=[];const identities=new Set<string>();
 for(const observed of collection.observations){
  if(observed.basis!=='original'||!['kind','nullability','cardinality','facets','keys','relationships','schema_properties'].includes(observed.operation)){deferred.push(observed);continue}
  const result=observed.result as any;if(result.state!=='observed'){deferred.push(observed);continue}
  const original=result.observation,meaning=original.meaning;
  if(observed.operation==='schema_properties'){
   const di=prepared.documents.findIndex(d=>d.documentId===observed.documentId),document=prepared.documents[di],identity=observed.identity as any;
   if(!document||JSON.stringify(original.source)!==JSON.stringify(document.interpretation.source)||typeof original.path!=='string'||original.source.umf!=='0.8.0')throw Error('Original schema-property source required');
   const properties=original.properties;if(properties===null||typeof properties!=='object'||Array.isArray(properties))throw Error('Original owner property map required');
   const selected=Object.keys(properties).filter(k=>['allowedValues','default','facets'].includes(k));
   if(Object.keys(properties).length===0)absent.push(observed);
   if(Object.keys(properties).some(k=>!selected.includes(k)))deferred.push(observed);
   const owner=identity.scope==='document'?Object.freeze({scope:'document' as const,documentId:document.documentId}):Object.freeze({documentId:document.documentId,moduleId:identity.module as string});
   if(identity.scope!=='document'&&typeof identity.module!=='string')throw Error('Original schema-property owner required');
   const source=prepared.original.input.documents[di].artifact;
   for(const key of selected){const pointer=original.path+'/'+key;let node:any=original.source;
    for(const token of pointer.slice(1).split('/')){const part=token.replace(/~1/g,'/').replace(/~0/g,'~');if(node===null||typeof node!=='object'||!Object.hasOwn(node,part))throw Error('Original schema-property node absent');node=node[part]}
    if(JSON.stringify(node)!==JSON.stringify(properties[key]))throw Error('Original schema-property value correspondence required');
    const uniqueness=JSON.stringify([source.sha256,owner,pointer]);if(identities.has(uniqueness))throw Error('Duplicate original core assertion source identity');identities.add(uniqueness);
    entries.push(Object.freeze({assertion:Object.freeze({sourceKind:'umf_document' as const,owner,definitionPin:source.sha256,sourcePointer:pointer,kind:'source' as const,sourceIdentityProfile:profile}),source,ruleName:'core.schema_properties.'+key,ruleNameOrigin:'profile_generated' as const,enforcement:'none' as const,reason:'unqualified' as const,ownerEvidence:observed.evidence}));
   }
   continue;
  }
  if(meaning?.state==='missing'){absent.push(observed);continue}
  if(!['known','partial'].includes(meaning?.state)){deferred.push(observed);continue}
  const di=prepared.documents.findIndex(d=>d.documentId===observed.documentId),document=prepared.documents[di],identity=observed.identity as any;
  if(!document||JSON.stringify(original.source)!==JSON.stringify(document.interpretation.source)||typeof original.path!=='string'||!original.path.startsWith('/')||typeof identity?.module!=='string')throw Error('Original core source/owner pointer required');
  let node:any=original.source;
  for(const token of original.path.slice(1).split('/')){const key=token.replace(/~1/g,'/').replace(/~0/g,'~');if(node===null||typeof node!=='object'||!Object.hasOwn(node,key))throw Error('Original asserted source node absent');node=node[key]}
  const source=prepared.original.input.documents[di].artifact,owner=Object.freeze({documentId:document.documentId,moduleId:identity.module});
  const declaration=observed.operation==='keys'||observed.operation==='relationships';
  const originalNodes=declaration?node:[node],ownerNodes=declaration?meaning[observed.operation]:[node];
  if(!Array.isArray(originalNodes)||!Array.isArray(ownerNodes)||originalNodes.length!==ownerNodes.length)throw Error('Complete original declaration occurrence correspondence required');
  if(originalNodes.length===0){absent.push(observed);continue}
  for(let index=0;index<originalNodes.length;index++){
   const pointer=original.path+(declaration?'/'+index:'');
   const uniqueness=JSON.stringify([source.sha256,owner,pointer]);if(identities.has(uniqueness))throw Error('Duplicate original core assertion source identity');identities.add(uniqueness);
   const authored=declaration&&typeof originalNodes[index]?.id==='string'&&originalNodes[index].id.length>0;
   if(declaration&&originalNodes[index]?.id!==ownerNodes[index]?.id)throw Error('Original authored declaration identity correspondence required');
   const identity=authored?{kind:'authored' as const,authoredIdentity:originalNodes[index].id as string}:{kind:'source' as const,sourceIdentityProfile:profile};
   entries.push(Object.freeze({assertion:Object.freeze({sourceKind:'umf_document' as const,owner,definitionPin:source.sha256,sourcePointer:pointer,...identity}),
    source,ruleName:'core.'+observed.operation,ruleNameOrigin:'profile_generated' as const,enforcement:'none' as const,reason:'unqualified' as const,ownerEvidence:observed.evidence}));
  }
 }
 return Object.freeze({profile,manifest,entries:Object.freeze(entries),absent:Object.freeze(absent),deferred:Object.freeze(deferred),complete:false as const,scope:'original_inspected_core_source_identity_subset_only' as const});
}
