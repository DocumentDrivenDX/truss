/** Original inspected core subset. Never a complete enforcement inventory. */
import {createHash} from 'node:crypto';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import {requireOriginalCatalogObservationCollection,type collectCatalogAssertionObservations} from './catalog-assertion-observations';
/** Owner results are already retained frozen JSON; object order is immaterial,
 * array order and every opaque member remain part of original correspondence. */
function sameOriginalMeaning(a:any,b:any):boolean{
 if(a===null||b===null||typeof a!=='object'||typeof b!=='object')return Object.is(a,b);
 if(Array.isArray(a)!==Array.isArray(b))return false;
 const keys=Object.keys(a);if(keys.length!==Object.keys(b).length)return false;
 if(Array.isArray(a)&&a.length!==b.length)return false;
 return keys.every(key=>Object.hasOwn(b,key)&&sameOriginalMeaning(a[key],b[key]));
}
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type Collection=ReturnType<typeof collectCatalogAssertionObservations>;
export function collectCatalogCoreAssertionIdentities(prepared:Prepared,collection:Collection){
 requireOriginalCatalogPreparation(prepared);requireOriginalCatalogObservationCollection(prepared,collection);
 const manifestBytes=Buffer.from(JSON.stringify({interfaceVersion:'truss-core-assertion-source-identity/0.3.0',producers:{fields:collection.fieldProfile,declarations:collection.profile},
  operations:['kind','nullability','cardinality','facets','keys','relationships','schema_properties'],basis:'original',schemaPropertyAssertions:['allowedValues','default','facets'],annotations:'retained separately; not constraint assertions',identity:'original document digest, qualified owner and exact owner-produced pointer',authored:'retain exact declaration ID with full original occurrence pointer',missing:'retained absence observation; no assertion invented',enforcement:'none/unqualified'}));
 const manifest=Object.freeze({identity:'truss.core-assertion-source-identity/0.3.0',bytesBase64:manifestBytes.toString('base64'),sha256:createHash('sha256').update(manifestBytes).digest('hex')});
 const profile=Object.freeze({identity:'truss-core-assertion-source-identity',version:'0.3.0',sha256:manifest.sha256});
 const entries=[];const declarationMeanings=[];const fieldMeanings=[];const absent=[];const deferred=[];const identities=new Set<string>();
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
  // Validate selected original 0.7 Field families before state filtering.
  // Opaque item-type qualifiers and optional-member presence remain significant.
  if(['kind','nullability','cardinality','facets'].includes(observed.operation)){
   const document=prepared.documents.find(d=>d.documentId===observed.documentId),requested=observed.identity as any;
   if(document?.umfVersion==='0.7.0'){
    const family=observed.operation as 'kind'|'nullability'|'cardinality'|'facets';
    const versions={kind:'6.0.0',nullability:'5.0.0',cardinality:'4.0.0',facets:'3.0.0'};
    const known={kind:['field','record','group'],nullability:['required','absent-allowed','unspecified'],cardinality:['one','array','map','unspecified'],facets:[] as string[]};
    const source=document.interpretation.source,mi=source.modules.findIndex((m:any)=>m.id===requested.module);
    const ei=mi<0?-1:source.modules[mi]!.elements.findIndex((e:any)=>e.id===requested.element);
    if(!collection.fieldProfile||mi<0||ei<0||!sameOriginalMeaning(original.source,source)||
      !sameOriginalMeaning(original.identity,requested)||original.operation!=='inspect-core-'+family||original.version!==versions[family]||
      original.path!=='/modules/'+mi+'/elements/'+ei+'/'+family)throw Error('Original '+family+' owner context correspondence required');
    const element=source.modules[mi]!.elements[ei]!,present=Object.hasOwn(element,family),value=element[family];
    let expected:any=present?(known[family].includes(value as string)?
     {state:'known',[family]:value,...(family==='cardinality'&&Object.hasOwn(element,'itemType')?{itemType:element.itemType}:{})}:
     {state:'unknown',value}):{state:family==='kind'?'unspecified':element.kind==='field'?'missing':'inapplicable'};
    if(family==='facets'&&present){
     const facets=value as any,interpreted:any={};
     if(facets.length&&['unicode-scalar','byte'].includes(facets.length.unit))interpreted.length={max:facets.length.max,unit:facets.length.unit};
     if(facets.integerWidth)interpreted.integerWidth={bits:facets.integerWidth.bits,signed:facets.integerWidth.signed};
     if(facets.precision!==undefined){interpreted.precision=facets.precision;interpreted.scale=facets.scale}
     // Derive unknown paths from the separately captured original document
     // validator, not from this Field observation's own claimed classification.
     const path='/modules/'+mi+'/elements/'+ei+'/facets';
     const uninterpretedPaths=document.interpretation.sourceValidation.diagnostics.filter((d:any)=>
      d.severity==='warning'&&['UNKNOWN_FACET','UNKNOWN_FACET_UNIT'].includes(d.code)&&(d.path===path||d.path.startsWith(path+'/'))).map((d:any)=>d.path);
     expected={state:uninterpretedPaths.length?'partial':'known',facets,interpreted,uninterpretedPaths};
    }
    if(!sameOriginalMeaning(meaning,expected))throw Error('Original '+family+' meaning correspondence required');
   }
  }
  if(!['known','partial','missing'].includes(meaning?.state)){deferred.push(observed);continue}
  const di=prepared.documents.findIndex(d=>d.documentId===observed.documentId),document=prepared.documents[di],identity=observed.identity as any;
  if(!document||JSON.stringify(original.source)!==JSON.stringify(document.interpretation.source)||typeof original.path!=='string'||!original.path.startsWith('/')||typeof identity?.module!=='string')throw Error('Original core source/owner pointer required');
  const mi=original.source.modules.findIndex((m:any)=>m.id===identity.module);
  const ei=mi<0?-1:original.source.modules[mi].elements.findIndex((e:any)=>e.id===identity.element);
  const expectedPath=observed.operation==='relationships'?'/modules/'+mi+'/relationships':'/modules/'+mi+'/elements/'+ei+'/'+observed.operation;
  if(mi<0||(observed.operation!=='relationships'&&ei<0)||original.path!==expectedPath)throw Error('Original requested owner pointer correspondence required');
  let node:any=original.source,present=true;const tokens=original.path.slice(1).split('/');
  for(let i=0;i<tokens.length;i++){const key=tokens[i]!.replace(/~1/g,'/').replace(/~0/g,'~');
   if(node===null||typeof node!=='object')throw Error('Original asserted source parent absent');
   if(!Object.hasOwn(node,key)){if(i!==tokens.length-1)throw Error('Original asserted source parent absent');present=false;break}node=node[key];
  }
  if(meaning.state==='missing'){
   if(present)throw Error('Complete original declaration meaning correspondence required: authored value cannot be missing');
   absent.push(observed);continue;
  }
  if(!present)throw Error('Original asserted source node absent');
  const source=prepared.original.input.documents[di].artifact,owner=Object.freeze({documentId:document.documentId,moduleId:identity.module});
  const declaration=observed.operation==='keys'||observed.operation==='relationships';
  const originalNodes=declaration?node:[node],ownerNodes=declaration?meaning[observed.operation]:[node];
  if(!Array.isArray(originalNodes)||!Array.isArray(ownerNodes)||originalNodes.length!==ownerNodes.length)throw Error('Complete original declaration occurrence correspondence required');
  if(declaration&&!sameOriginalMeaning(originalNodes,ownerNodes))throw Error('Complete original declaration meaning correspondence required');
  if(originalNodes.length===0){absent.push(observed);continue}
  for(let index=0;index<originalNodes.length;index++){
   const pointer=original.path+(declaration?'/'+index:'');
   const uniqueness=JSON.stringify([source.sha256,owner,pointer]);if(identities.has(uniqueness))throw Error('Duplicate original core assertion source identity');identities.add(uniqueness);
   const authored=declaration&&typeof originalNodes[index]?.id==='string'&&originalNodes[index].id.length>0;
   if(declaration&&originalNodes[index]?.id!==ownerNodes[index]?.id)throw Error('Original authored declaration identity correspondence required');
   const identity=authored?{kind:'authored' as const,authoredIdentity:originalNodes[index].id as string}:{kind:'source' as const,sourceIdentityProfile:profile};
   const entry=Object.freeze({assertion:Object.freeze({sourceKind:'umf_document' as const,owner,definitionPin:source.sha256,sourcePointer:pointer,...identity}),
    source,ruleName:'core.'+observed.operation,ruleNameOrigin:'profile_generated' as const,enforcement:'none' as const,reason:'unqualified' as const,ownerEvidence:observed.evidence});
   entries.push(entry);
   if(['kind','nullability','cardinality','facets'].includes(observed.operation)&&original.source.umf==='0.7.0')fieldMeanings.push(Object.freeze({assertion:entry,
    ownerProfile:collection.fieldProfile!,ownerState:meaning.state as 'known'|'partial',originalMeaning:meaning,
    meaningCorrespondence:true as const,interpretationQualified:false as const,scope:`original_${observed.operation}_owner_meaning_only` as const}));
   if(declaration)declarationMeanings.push(Object.freeze({assertion:entry,ownerProfile:collection.profile,
    ownerState:meaning.state as 'known'|'partial',originalMeaning:ownerNodes[index],
    // Keep whole-owner unknown-path diagnostics; never infer local completeness.
    uninterpretedPaths:meaning.uninterpretedPaths,meaningCorrespondence:true as const,
    interpretationQualified:false as const,scope:'original_declaration_owner_meaning_only' as const}));
  }
 }
 return Object.freeze({profile,manifest,entries:Object.freeze(entries),declarationMeanings:Object.freeze(declarationMeanings),fieldMeanings:Object.freeze(fieldMeanings),absent:Object.freeze(absent),deferred:Object.freeze(deferred),complete:false as const,scope:'original_inspected_core_source_identity_subset_only' as const});
}
