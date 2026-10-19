// SPDX-License-Identifier: MIT OR Apache-2.0
/** Trusted host-only original producer registration. No alternate UMF validation. */
import {resolve} from 'node:path';
import {requireUnchangedCatalogTransition} from './catalog-transition-correspondence';
const assertionOwners=new WeakMap<object,'declarations'|'assertion-fields'|'scalar-types'|'record-members'|'reference-links'|'record-type-receipts'|'record-type-journals'>();
function registerAssertionOwner<T extends object>(owner:T,mode:'declarations'|'assertion-fields'|'scalar-types'|'record-members'|'reference-links'|'record-type-receipts'|'record-type-journals'):T{assertionOwners.set(owner,mode);return owner;}
/** Private loaded-instance recognition; no external issuer or native qualification. */
export function requireLoadedUmfAssertionOwner(owner:object,mode:'declarations'|'assertion-fields'|'scalar-types'|'record-members'|'reference-links'|'record-type-receipts'|'record-type-journals'):void{
 if(assertionOwners.get(owner)!==mode)throw Error('Original loaded assertion owner required');
}
export const UMF_RUNTIME_SOURCE='c45c72a2a8a3c4fba61c40c5927dd9091acf8cc3';
export const UMF_RECORD_SOURCE='aa944733fc45c090853ca051fd79c26bd3681307';
/** One canonical original-source validator for both admitted core versions. */
export async function loadCatalogSourceOwner(directory:string){
 const {hash,captured}=await loadPinnedFunctions(directory,UMF_RECORD_SOURCE,'catalog-record',['withCatalogResourceProfile','readJsonValue','validateDocument']);
 return Object.freeze({sourceRevision:UMF_RECORD_SOURCE,bundleSha256:hash,
  inspect(originalText:string){return captured.withCatalogResourceProfile(()=>{
   if(typeof originalText!=='string'||Buffer.byteLength(originalText)>4194304)throw Error('Original document bound');
   const source=captured.readJsonValue(originalText,'json');
   const sourceValidation=captured.validateDocument(source);
   if(sourceValidation.valid&&!['0.7.0','0.8.0'].includes(source.umf))throw Error('Unsupported original UMF version');
   return {originalText,source,sourceValidation,transition:null,targetValidation:sourceValidation,target:source};
  });}});
}
export async function loadUmfProducer(directory:string){
 const {hash,captured}=await loadPinnedFunctions(directory,UMF_RECORD_SOURCE,'record',['withCatalogResourceProfile','readDocument','validateDocument','validateCoreRecordValues','upgradeSchemaPropertiesEnvelope','verifySchemaPropertiesUpgrade','rollbackSchemaPropertiesEnvelope']);
 return Object.freeze({sourceRevision:UMF_RECORD_SOURCE,bundleSha256:hash,
  inspect(originalText:string){return captured.withCatalogResourceProfile(()=>{
   if(typeof originalText!=='string'||Buffer.byteLength(originalText)>4194304)throw Error('Original document bound');
   const source=captured.readDocument(originalText,'json');const sourceValidation=captured.validateDocument(source);
   if(!sourceValidation.valid) return {originalText,source,sourceValidation,transition:null,targetValidation:null};
   let transition=null,target=source;
   if(source.umf==='0.7.0'){
    const originalSourceJson=JSON.stringify(source);
    transition=captured.upgradeSchemaPropertiesEnvelope(source);
    const verified=captured.verifySchemaPropertiesUpgrade(transition);
    const restored=captured.rollbackSchemaPropertiesEnvelope(transition,transition.target);
    requireUnchangedCatalogTransition(originalSourceJson,source,transition,verified,restored);
    target=transition.target;
   }else if(source.umf!=='0.8.0')throw Error('Unsupported original UMF version');
   return {originalText,source,sourceValidation,transition,targetValidation:captured.validateDocument(target),target};
  });},
  inspectCatalog(originalText:string){return captured.withCatalogResourceProfile(()=>{
   if(typeof originalText!=='string'||Buffer.byteLength(originalText)>4194304)throw Error('Original document bound');
   const source=captured.readDocument(originalText,'json');
   if(!['0.7.0','0.8.0'].includes(source.umf))throw Error('Unsupported original UMF version');
   const sourceValidation=captured.validateDocument(source);
   return {originalText,source,sourceValidation,transition:null,targetValidation:sourceValidation,target:source};
  });},
  checkRecord(target:unknown,identity:unknown,values:unknown){return captured.validateCoreRecordValues(target,identity,values)}
 });
}


/** Independently pinned current-core numeric conveniences; no Record-source substitution. */
export const UMF_NUMERIC_SOURCE='9e4bed3efe922c11e4b5a888ba6854de14f1b29f';
export async function loadUmfNumericProducer(directory:string){
 const {hash,captured}=await loadPinnedFunctions(directory,UMF_NUMERIC_SOURCE,'numeric',['exactDecimal','integerFromBigInt','integerToBigInt','admitJavascriptNumber','numericToNumberLossless']);
 return Object.freeze({sourceRevision:UMF_NUMERIC_SOURCE,bundleSha256:hash,
  exactDecimal:captured.exactDecimal,integerFromBigInt:captured.integerFromBigInt,
  integerToBigInt:captured.integerToBigInt,admitJavascriptNumber:captured.admitJavascriptNumber,
  numericToNumberLossless:captured.numericToNumberLossless,
 });
}


export const UMF_VALUE_SOURCE=UMF_NUMERIC_SOURCE;
/** Original current-core Field and tuple semantics, separate from native persistence. */
export async function loadUmfValueProducer(directory:string){
 const {hash,captured}=await loadPinnedFunctions(directory,UMF_VALUE_SOURCE,'values',['validateCoreFieldValue','encodeCoreKeyTuple','verifyCoreKeyTuple']);
 return Object.freeze({sourceRevision:UMF_VALUE_SOURCE,bundleSha256:hash,
  validateCoreFieldValue:captured.validateCoreFieldValue,
  encodeCoreKeyTuple:captured.encodeCoreKeyTuple,verifyCoreKeyTuple:captured.verifyCoreKeyTuple,
 });
}
/** Owner-defined metadata meaning; separate bundle from value checks and native claims. */
export async function loadUmfDeclarationProducer(directory:string){
 const {hash,captured}=await loadPinnedFunctions(directory,UMF_RUNTIME_SOURCE,'declarations',['inspectCoreSchemaProperties','inspectCoreKeys','inspectCoreRelationships']);
 return registerAssertionOwner(Object.freeze({sourceRevision:UMF_RUNTIME_SOURCE,bundleSha256:hash,
  inspectSchemaProperties:captured.inspectCoreSchemaProperties,
  inspectKeys:captured.inspectCoreKeys,inspectRelationships:captured.inspectCoreRelationships}),'declarations');
}
async function loadPinnedFunctions(directory:string,revision:string,mode:string,names:readonly string[]){
 const root=resolve(directory);const manifest=await Bun.file(root+'/producer-manifest.json').json();
 const bytes=await Bun.file(root+'/producer.js').arrayBuffer();
 const hash=new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
 if(manifest.revision!==revision||(manifest.producerMode??'record')!==mode||manifest.bundleSha256!==hash)throw Error('Original UMF producer pin mismatch');
 const owner=await import(root+'/producer.js');
 const captured=Object.fromEntries(names.map(name=>{if(typeof owner[name]!=='function')throw Error('Missing original producer');return [name,owner[name].bind(owner)]}));
 return {hash,captured};
}

/** Original Field assertion meaning, not installation or enforcement evidence. */
export async function loadUmfFieldAssertionProducer(directory:string){
 const {hash,captured}=await loadPinnedFunctions(directory,UMF_RUNTIME_SOURCE,'assertion-fields',['inspectCoreElementKind','inspectCoreNullability','inspectCoreCardinality','inspectCoreFacets']);
 return registerAssertionOwner(Object.freeze({sourceRevision:UMF_RUNTIME_SOURCE,bundleSha256:hash,
  inspectKind:captured.inspectCoreElementKind,inspectNullability:captured.inspectCoreNullability,
  inspectCardinality:captured.inspectCoreCardinality,inspectFacets:captured.inspectCoreFacets}),'assertion-fields');
}

/** Separate current scalar owner; historical Record preparation remains independently pinned. */
export const UMF_SCALAR_TYPE_SOURCE='94d0a99e4d1e9eb39278f38d6cd6bcba51e46db8';
export async function loadUmfScalarTypeProducer(directory:string){
 const {hash,captured}=await loadPinnedFunctions(directory,UMF_SCALAR_TYPE_SOURCE,'scalar-types',['inspectCoreScalarType']);
 return registerAssertionOwner(Object.freeze({sourceRevision:UMF_SCALAR_TYPE_SOURCE,bundleSha256:hash,
  inspectScalarType:captured.inspectCoreScalarType}),'scalar-types');
}

/** Independent original Record membership owner; no native/issuer qualification. */
export const UMF_RECORD_MEMBERS_SOURCE='5ddc656273e1965efa0187f3090d165d45225dcd';
export async function loadUmfRecordMembersProducer(directory:string){
 const {hash,captured}=await loadPinnedFunctions(directory,UMF_RECORD_MEMBERS_SOURCE,'record-members',['inspectCoreRecordMembers']);
 return registerAssertionOwner(Object.freeze({sourceRevision:UMF_RECORD_MEMBERS_SOURCE,bundleSha256:hash,
  inspectRecordMembers:captured.inspectCoreRecordMembers}),'record-members');
}

/** Direct core-link owner; bare role labels never gain authored type authority. */
export const UMF_REFERENCE_LINKS_SOURCE='9545b7119ceaa29ca7523e4722ec52412084d835';
export async function loadUmfReferenceLinksProducer(directory:string){
 const {hash,captured}=await loadPinnedFunctions(directory,UMF_REFERENCE_LINKS_SOURCE,'reference-links',['inspectCoreReferenceLinks']);
 return registerAssertionOwner(Object.freeze({sourceRevision:UMF_REFERENCE_LINKS_SOURCE,bundleSha256:hash,
  inspectReferenceLinks:captured.inspectCoreReferenceLinks}),'reference-links');
}

/** Exact-current type receipt consistency owner; no authenticated issuer or native enforcement. */
export const UMF_RECORD_TYPE_RECEIPT_SOURCE='ec3fae2bdb93bdbaff30c38ee370030da7db1760';
export async function loadUmfRecordTypeReceiptProducer(directory:string){
 const {hash,captured}=await loadPinnedFunctions(directory,UMF_RECORD_TYPE_RECEIPT_SOURCE,'record-type-receipts',['inspectCoreRecordTypeReceipt']);
 return registerAssertionOwner(Object.freeze({sourceRevision:UMF_RECORD_TYPE_RECEIPT_SOURCE,bundleSha256:hash,
  inspectRecordTypeReceipt:captured.inspectCoreRecordTypeReceipt}),'record-type-receipts');
}

/** Explicit transition journal owner; no authenticated issuer or native authority. */
export const UMF_RECORD_TYPE_JOURNAL_SOURCE='e71613d9c76bf7a4bf5476bf72ab4fd99059ff17';
export async function loadUmfRecordTypeJournalProducer(directory:string){
 const {hash,captured}=await loadPinnedFunctions(directory,UMF_RECORD_TYPE_JOURNAL_SOURCE,'record-type-journals',['inspectCoreRecordTypeJournal']);
 return registerAssertionOwner(Object.freeze({sourceRevision:UMF_RECORD_TYPE_JOURNAL_SOURCE,bundleSha256:hash,inspectRecordTypeJournal:captured.inspectCoreRecordTypeJournal}),'record-type-journals');
}

/** Separate current original0.8 catalog owner; no legacy profile replacement. */
export const UMF_CORE08_CATALOG_SOURCE='aa944733fc45c090853ca051fd79c26bd3681307';
export async function loadCore08CatalogOwners(directory:string){
 const revision=UMF_CORE08_CATALOG_SOURCE;
 const {hash,captured}=await loadPinnedFunctions(directory,revision,'core08-catalog',[
  'withCatalogResourceProfile','readDocument','validateDocument','inspectCoreSchemaProperties','inspectCoreKeys','inspectCoreRelationships',
  'inspectCoreElementKind','inspectCoreNullability','inspectCoreCardinality','inspectCoreFacets',
  'inspectCoreScalarType','inspectCoreRecordMembers','inspectCoreReferenceLinks']);
 const pin={sourceRevision:revision,bundleSha256:hash};
 const record=Object.freeze({...pin,inspect(originalText:string){return captured.withCatalogResourceProfile(()=>{
  if(typeof originalText!=='string'||Buffer.byteLength(originalText)>4194304)throw Error('Original document bound');
  const source=captured.readDocument(originalText,'json');if(source.umf!=='0.8.0')throw Error('Unsupported original UMF version');
  const sourceValidation=captured.validateDocument(source);
  return {originalText,source,sourceValidation,transition:null,targetValidation:sourceValidation,target:source};
 });}});
 return Object.freeze({record,
  declarations:registerAssertionOwner(Object.freeze({...pin,inspectSchemaProperties:captured.inspectCoreSchemaProperties,inspectKeys:captured.inspectCoreKeys,inspectRelationships:captured.inspectCoreRelationships}),'declarations'),
  fields:registerAssertionOwner(Object.freeze({...pin,inspectKind:captured.inspectCoreElementKind,inspectNullability:captured.inspectCoreNullability,inspectCardinality:captured.inspectCoreCardinality,inspectFacets:captured.inspectCoreFacets}),'assertion-fields'),
  scalars:registerAssertionOwner(Object.freeze({...pin,inspectScalarType:captured.inspectCoreScalarType}),'scalar-types'),
  members:registerAssertionOwner(Object.freeze({...pin,inspectRecordMembers:captured.inspectCoreRecordMembers}),'record-members'),
  links:registerAssertionOwner(Object.freeze({...pin,inspectReferenceLinks:captured.inspectCoreReferenceLinks}),'reference-links')});
}
