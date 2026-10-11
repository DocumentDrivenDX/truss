/** Private original facet duties; never complete assertion or enforcement admission. */
import {createHash} from 'node:crypto';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
import {collectCatalogCoreAssertionIdentities} from './catalog-core-assertion-identities';
import type {collectCatalogAssertionObservations} from './catalog-assertion-observations';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
type Collection=ReturnType<typeof collectCatalogAssertionObservations>;
const issued=new WeakMap<object,Prepared>();
export function collectCatalogFacetRuleFamilies(prepared:Prepared,collection:Collection){
 requireOriginalCatalogPreparation(prepared);
 const core=collectCatalogCoreAssertionIdentities(prepared,collection);
 const bytes=Buffer.from(JSON.stringify({interfaceVersion:'truss-facet-rule-family-candidate/0.1.0',
  owner:collection.fieldProfile,basis:'original 0.7 compared facet interpretation',
  families:{length:'max count in explicit unit',integer_width:'bits and signedness bound',decimal_precision:'absolute scaled coefficient less than 10^precision',decimal_fixed_scale:'exact integer coefficient at declared scale; no rounding'},
  identity:'candidate profile, semantic owner profile, exact original occurrence and family',scope:'partial original facet duties only; no registration or enforcement'}));
 const manifest=Object.freeze({identity:'truss.facet-rule-family-candidate/0.1.0',bytesBase64:bytes.toString('base64'),sha256:createHash('sha256').update(bytes).digest('hex')});
 const profile=Object.freeze({identity:'truss-facet-rule-family-candidate',version:'0.1.0',sha256:manifest.sha256});
 const carriers=core.fieldMeanings.filter(m=>m.assertion.ruleName==='core.facets');
 const rules=[];const identities=new Set<string>();
 for(const carrier of carriers){
  const interpreted=carrier.originalMeaning.interpreted;
  const families:{family:string;parameters:unknown}[]=[];
  if(Object.hasOwn(interpreted,'length'))families.push({family:'length',parameters:interpreted.length});
  if(Object.hasOwn(interpreted,'integerWidth'))families.push({family:'integer_width',parameters:interpreted.integerWidth});
  if(Object.hasOwn(interpreted,'precision')){
   if(!Object.hasOwn(interpreted,'scale'))throw Error('Original paired decimal facet context required');
   const parameters=Object.freeze({precision:interpreted.precision,scale:interpreted.scale});
   families.push({family:'decimal_precision',parameters},{family:'decimal_fixed_scale',parameters});
  }
  for(const {family,parameters} of families){
   const occurrence=carrier.assertion.assertion;
   const identity=Object.freeze({profile,semanticOwnerProfile:carrier.ownerProfile,occurrence,family});
   const key=JSON.stringify(identity);if(identities.has(key))throw Error('Duplicate original facet rule-family identity');identities.add(key);
   rules.push(Object.freeze({identity,source:carrier.assertion.source,carrier,parameters,
    enforcement:'none' as const,reason:'unqualified' as const,interpretationQualified:false as const}));
  }
 }
 const result=Object.freeze({profile,manifest,core,carriers:Object.freeze(carriers),rules:Object.freeze(rules),
  complete:false as const,semanticFamilyCoverageComplete:false as const,interpretationQualified:false as const,
  scope:'original_compared_facet_rule_family_candidate_only' as const});
 issued.set(result,prepared);return result;
}
export function requireOriginalCatalogFacetRuleFamilies(prepared:Prepared,candidate:object):void{
 requireOriginalCatalogPreparation(prepared);
 if(issued.get(candidate)!==prepared)throw Error('Original facet rule-family candidate custody required');
}
