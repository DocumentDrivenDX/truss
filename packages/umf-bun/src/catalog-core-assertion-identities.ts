// SPDX-License-Identifier: MIT OR Apache-2.0
import {compactCatalogSources,resolveCatalogObservation,catalogSourceArtifact} from './catalog-source-reference';
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
 const current=prepared.documents.every(d=>d.umfVersion==='0.8.0');
 const identityVersion=compactCatalogSources(prepared)?'0.8.0':current?'0.7.0':'0.6.0';
 const manifestBytes=Buffer.from(JSON.stringify({interfaceVersion:'truss-core-assertion-source-identity/'+identityVersion,producers:{fields:collection.fieldProfile,scalar:collection.scalarProfile,members:collection.membersProfile,referenceLinks:collection.referenceLinksProfile,declarations:collection.profile},
  operations:['kind','nullability','cardinality','facets','scalarType','members','referenceLinks','keys','relationships','schema_properties'],basis:'original',referenceLinks:'generic_core_links_not_verified_type_assertions',schemaPropertyAssertions:['allowedValues','default','facets'],annotations:'retained separately; not constraint assertions',identity:'original document digest, qualified owner and exact owner-produced pointer',authored:'retain exact declaration ID with full original occurrence pointer',missing:'retained absence observation; no assertion invented',enforcement:'none/unqualified'}));
 const manifest=Object.freeze({identity:'truss.core-assertion-source-identity/'+identityVersion,bytesBase64:manifestBytes.toString('base64'),sha256:createHash('sha256').update(manifestBytes).digest('hex')});
 const profile=Object.freeze({identity:'truss-core-assertion-source-identity',version:identityVersion,sha256:manifest.sha256});
 type Entry={assertion:{sourceKind:'umf_document';owner:{scope:'document';documentId:string}|{documentId:string;moduleId:string};definitionPin:string;sourcePointer:string;kind:'source'|'authored';sourceIdentityProfile?:typeof profile;authoredIdentity?:string};source:ReturnType<typeof catalogSourceArtifact>;ruleName:string;ruleNameOrigin:'profile_generated';enforcement:'none';reason:'unqualified';ownerEvidence:Collection['observations'][number]['evidence']};
 type LinkEvidence={documentId:string;owner:{moduleId:string;elementId:string};source:Entry['source'];sourcePointer:string;ownerProfile:NonNullable<Collection['referenceLinksProfile']>;ownerEvidence:Collection['observations'][number]['evidence'];originalMeaning:unknown;typeAssertion:'unverified';meaningCorrespondence:true;interpretationQualified:false;scope:'original_direct_core_reference_links_only'};
 const referenceLinks:LinkEvidence[]=[],referenceLinkDeclarations:LinkEvidence[]=[];
 const entries:Entry[]=[];const declarationMeanings=[];const membershipMeanings:{assertion:typeof entries[number];ownerProfile:NonNullable<Collection['membersProfile']>;ownerState:'known'|'partial';originalMeaning:unknown;uninterpretedPaths:readonly string[];meaningCorrespondence:true;interpretationQualified:false;scope:'original_record_member_owner_meaning_only'}[]=[];const fieldMeanings=[];const absent=[];const deferred=[];const identities=new Set<string>();
 for(const observed of collection.observations){
  if(observed.basis!=='original'||!['kind','nullability','cardinality','facets','scalarType','members','referenceLinks','keys','relationships','schema_properties'].includes(observed.operation)){deferred.push(observed);continue}
  const result=observed.result as any;if(result.state!=='observed'){deferred.push(observed);continue}
  const original=resolveCatalogObservation(prepared,observed),meaning=original.meaning;
  if(observed.operation==='schema_properties'){
   const di=prepared.documents.findIndex(d=>d.documentId===observed.documentId),document=prepared.documents[di],identity=observed.identity as any;
   if(!document||JSON.stringify(original.source)!==JSON.stringify(document.interpretation.source)||typeof original.path!=='string'||original.source.umf!=='0.8.0')throw Error('Original schema-property source required');
   const properties=original.properties;if(properties===null||typeof properties!=='object'||Array.isArray(properties))throw Error('Original owner property map required');
   const selected=Object.keys(properties).filter(k=>(current?['allowedValues','default']:['allowedValues','default','facets']).includes(k));
   if(Object.keys(properties).length===0)absent.push(observed);
   if(Object.keys(properties).some(k=>!selected.includes(k)))deferred.push(observed);
   const owner=identity.scope==='document'?Object.freeze({scope:'document' as const,documentId:document.documentId}):Object.freeze({documentId:document.documentId,moduleId:identity.module as string});
   if(identity.scope!=='document'&&typeof identity.module!=='string')throw Error('Original schema-property owner required');
   const source=catalogSourceArtifact(prepared,di);
   for(const key of selected){const pointer=original.path+'/'+key;let node:any=original.source;
    for(const token of pointer.slice(1).split('/')){const part=token.replace(/~1/g,'/').replace(/~0/g,'~');if(node===null||typeof node!=='object'||!Object.hasOwn(node,part))throw Error('Original schema-property node absent');node=node[part]}
    if(JSON.stringify(node)!==JSON.stringify(properties[key]))throw Error('Original schema-property value correspondence required');
    const uniqueness=JSON.stringify([source.sha256,owner,pointer]);if(identities.has(uniqueness))throw Error('Duplicate original core assertion source identity');identities.add(uniqueness);
    entries.push(Object.freeze({assertion:Object.freeze({sourceKind:'umf_document' as const,owner,definitionPin:source.sha256,sourcePointer:pointer,kind:'source' as const,sourceIdentityProfile:profile}),source,ruleName:'core.schema_properties.'+key,ruleNameOrigin:'profile_generated' as const,enforcement:'none' as const,reason:'unqualified' as const,ownerEvidence:observed.evidence}));
   }
   continue;
  }
  if(observed.operation==='referenceLinks'){
   const di=prepared.documents.findIndex(d=>d.documentId===observed.documentId),document=prepared.documents[di],requested=observed.identity as any;
   if(!document||!['0.7.0','0.8.0'].includes(document.umfVersion)||!collection.referenceLinksProfile)throw Error('Original referenceLinks owner context correspondence required');
   const source=document.interpretation.source,mi=source.modules.findIndex((m:any)=>m.id===requested.module),ei=mi<0?-1:source.modules[mi]!.elements.findIndex((e:any)=>e.id===requested.element);
   if(mi<0||ei<0)throw Error('Original referenceLinks owner context correspondence required');
   const element=source.modules[mi]!.elements[ei]!,path='/modules/'+mi+'/elements/'+ei+'/references';
   const expected=!Object.hasOwn(element,'references')?{state:'missing'}:{state:'present',links:element.references!.map((reference:any,index:number)=>{
    const ti=source.modules.findIndex((m:any)=>m.id===reference.module),te=ti<0?-1:source.modules[ti]!.elements.findIndex((e:any)=>e.id===reference.element);
    if(ti<0||te<0)throw Error('Original referenceLinks target correspondence required');
    const target=source.modules[ti]!.elements[te]!,at=path+'/'+index;
    return {index,path:at,reference,target:{identity:{module:reference.module,element:reference.element},path:'/modules/'+ti+'/elements/'+te,...(Object.hasOwn(target,'kind')?{kind:target.kind}:{})},uninterpretedPaths:document.interpretation.sourceValidation.diagnostics.filter((d:any)=>d.severity==='warning'&&d.code==='UNKNOWN_CORE_FIELD'&&(d.path===at||d.path.startsWith(at+'/'))).map((d:any)=>d.path),typeAssertion:'unverified'};
   })};
   if(!sameOriginalMeaning(original,{operation:'inspect-core-reference-links',version:document.umfVersion==='0.8.0'?'0.2.0':'0.1.0',source,identity:requested,path,meaning:expected,provenance:'unverified'}))throw Error('Original referenceLinks full result correspondence required');
   if(expected.state==='missing'){absent.push(observed);continue}
   const common={documentId:document.documentId,owner:Object.freeze({moduleId:requested.module as string,elementId:requested.element as string}),source:catalogSourceArtifact(prepared,di),ownerProfile:collection.referenceLinksProfile,ownerEvidence:observed.evidence,typeAssertion:'unverified' as const,meaningCorrespondence:true as const,interpretationQualified:false as const,scope:'original_direct_core_reference_links_only' as const};
   referenceLinkDeclarations.push(Object.freeze({...common,sourcePointer:path,originalMeaning:meaning}));
   for(const link of meaning.links)referenceLinks.push(Object.freeze({...common,sourcePointer:link.path,originalMeaning:link}));
   // Generic links carry original correspondence, never authored record-type duties.
   continue;
  }
  if(observed.operation==='members'){
   const di=prepared.documents.findIndex(d=>d.documentId===observed.documentId),document=prepared.documents[di],requested=observed.identity as any;
   if(!document||!['0.7.0','0.8.0'].includes(document.umfVersion)||!collection.membersProfile)throw Error('Original members owner context correspondence required');
   const source=document.interpretation.source,mi=source.modules.findIndex((m:any)=>m.id===requested.module),ei=mi<0?-1:source.modules[mi]!.elements.findIndex((e:any)=>e.id===requested.element);
   if(mi<0||ei<0)throw Error('Original members owner context correspondence required');
   const element=source.modules[mi]!.elements[ei]!,path='/modules/'+mi+'/elements/'+ei+'/members';
   const uninterpretedPaths=Object.freeze(document.interpretation.sourceValidation.diagnostics.filter((d:any)=>d.severity==='warning'&&d.code==='UNKNOWN_KEY_QUALIFIER'&&(d.path===path||d.path.startsWith(path+'/'))).map((d:any)=>d.path));
   const expected=element.kind!=='record'?{state:'inapplicable'}:!Object.hasOwn(element,'members')?{state:'missing'}:{state:uninterpretedPaths.length?'partial':'known',members:element.members,uninterpretedPaths};
   if(!sameOriginalMeaning(original,{operation:'inspect-core-record-members',version:document.umfVersion==='0.8.0'?'0.2.0':'0.1.0',source,identity:requested,path,meaning:expected,provenance:'unverified'}))throw Error('Original members full result correspondence required');
   if(expected.state==='missing'){absent.push(observed);continue}
   if(expected.state==='inapplicable'){deferred.push(observed);continue}
   const artifact=catalogSourceArtifact(prepared,di),owner=Object.freeze({documentId:document.documentId,moduleId:requested.module as string});
   // The explicit declaration itself is a duty even when its list is empty.
   // Member occurrence duties keep ordered qualified references and opaque qualifiers.
   const addMemberEntry=(pointer:string,ruleName:string,originalMeaning:unknown)=>{
    const uniqueness=JSON.stringify([artifact.sha256,owner,pointer]);if(identities.has(uniqueness))throw Error('Duplicate original core assertion source identity');identities.add(uniqueness);
    const entry=Object.freeze({assertion:Object.freeze({sourceKind:'umf_document' as const,owner,definitionPin:artifact.sha256,sourcePointer:pointer,kind:'source' as const,sourceIdentityProfile:profile}),source:artifact,ruleName,ruleNameOrigin:'profile_generated' as const,enforcement:'none' as const,reason:'unqualified' as const,ownerEvidence:observed.evidence});
    entries.push(entry);membershipMeanings.push(Object.freeze({assertion:entry,ownerProfile:collection.membersProfile!,ownerState:expected.state as 'known'|'partial',originalMeaning,uninterpretedPaths,meaningCorrespondence:true as const,interpretationQualified:false as const,scope:'original_record_member_owner_meaning_only' as const}));
   };
   addMemberEntry(path,'core.members',meaning);
   (element.members as any[]).forEach((member,index)=>addMemberEntry(path+'/'+index,'core.members.member',member));
   continue;
  }
  if(observed.operation==='scalarType'){
   const document=prepared.documents.find(d=>d.documentId===observed.documentId),requested=observed.identity as any;
   if(!document||!['0.7.0','0.8.0'].includes(document.umfVersion)||!collection.scalarProfile)throw Error('Original scalarType owner context correspondence required');
   const source=document.interpretation.source,mi=source.modules.findIndex((m:any)=>m.id===requested.module),ei=mi<0?-1:source.modules[mi]!.elements.findIndex((e:any)=>e.id===requested.element);
   if(mi<0||ei<0)throw Error('Original scalarType owner context correspondence required');
   const element=source.modules[mi]!.elements[ei]!,present=Object.hasOwn(element,'scalarType'),value=element.scalarType;
   const known=['boolean','integer','decimal','float','string','binary','date','time','timestamp'];
   const expected=element.kind!=='field'?{state:'inapplicable',...(present?{authoredScalarType:value}:{})}:!present?{state:'missing'}:known.includes(value!)?{state:'known',scalarType:value}:{state:'unknown',value};
   if(!sameOriginalMeaning(original,{operation:'inspect-core-scalar-type',version:document.umfVersion==='0.8.0'?'0.2.0':'0.1.0',source,identity:requested,path:'/modules/'+mi+'/elements/'+ei+'/scalarType',meaning:expected,provenance:'unverified'}))throw Error('Original scalarType full result correspondence required');
  }
  // Validate selected original 0.7 Field families before state filtering.
  // Opaque item-type qualifiers and optional-member presence remain significant.
  if(['kind','nullability','cardinality','facets'].includes(observed.operation)){
   const document=prepared.documents.find(d=>d.documentId===observed.documentId),requested=observed.identity as any;
   if(document&&['0.7.0','0.8.0'].includes(document.umfVersion)){
    const family=observed.operation as 'kind'|'nullability'|'cardinality'|'facets';
    const versions=document.umfVersion==='0.8.0'?{kind:'7.0.0',nullability:'6.0.0',cardinality:'5.0.0',facets:'4.0.0'}:{kind:'6.0.0',nullability:'5.0.0',cardinality:'4.0.0',facets:'3.0.0'};
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
     if(facets.length&&['unicode-scalar','byte'].includes(facets.length.unit))interpreted.length={...(facets.length.max!==undefined?{max:facets.length.max}:{}),...(document.umfVersion==='0.8.0'&&facets.length.min!==undefined?{min:facets.length.min}:{}),unit:facets.length.unit};
     if(facets.integerWidth)interpreted.integerWidth={bits:facets.integerWidth.bits,signed:facets.integerWidth.signed};
     if(facets.precision!==undefined){interpreted.precision=facets.precision;interpreted.scale=facets.scale}
     if(document.umfVersion==='0.8.0')for(const group of ['collectionSize','range'])if(facets[group]){const selected:any={};for(const key of group==='range'?['min','max','minInclusive','maxInclusive']:['min','max'])if(Object.hasOwn(facets[group],key))selected[key]=facets[group][key];interpreted[group]=selected;}
     // Derive unknown paths from the separately captured original document
     // validator, not from this Field observation's own claimed classification.
     const path='/modules/'+mi+'/elements/'+ei+'/facets';
     const uninterpretedPaths=document.interpretation.sourceValidation.diagnostics.filter((d:any)=>
      d.severity==='warning'&&(document.umfVersion==='0.8.0'||['UNKNOWN_FACET','UNKNOWN_FACET_UNIT'].includes(d.code))&&(d.path===path||d.path.startsWith(path+'/'))).map((d:any)=>d.path);
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
  const source=catalogSourceArtifact(prepared,di),owner=Object.freeze({documentId:document.documentId,moduleId:identity.module});
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
   if(['kind','nullability','cardinality','facets','scalarType'].includes(observed.operation)&&['0.7.0','0.8.0'].includes(original.source.umf))fieldMeanings.push(Object.freeze({assertion:entry,
    ownerProfile:(observed.operation==='scalarType'?collection.scalarProfile:collection.fieldProfile)!,ownerState:meaning.state as 'known'|'partial',originalMeaning:meaning,
    meaningCorrespondence:true as const,interpretationQualified:false as const,scope:`original_${observed.operation}_owner_meaning_only` as const}));
   if(declaration)declarationMeanings.push(Object.freeze({assertion:entry,ownerProfile:collection.profile,
    ownerState:meaning.state as 'known'|'partial',originalMeaning:ownerNodes[index],
    // Keep whole-owner unknown-path diagnostics; never infer local completeness.
    uninterpretedPaths:meaning.uninterpretedPaths,meaningCorrespondence:true as const,
    interpretationQualified:false as const,scope:'original_declaration_owner_meaning_only' as const}));
  }
 }
 return Object.freeze({profile,manifest,entries:Object.freeze(entries),referenceLinks:Object.freeze(referenceLinks),referenceLinkDeclarations:Object.freeze(referenceLinkDeclarations),declarationMeanings:Object.freeze(declarationMeanings),fieldMeanings:Object.freeze(fieldMeanings),membershipMeanings:Object.freeze(membershipMeanings),absent:Object.freeze(absent),deferred:Object.freeze(deferred),complete:false as const,scope:'original_inspected_core_source_identity_subset_only' as const});
}
