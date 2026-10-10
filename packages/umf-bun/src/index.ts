/** Trusted host-only original producer registration. No alternate UMF validation. */
import {resolve} from 'node:path';
import {requireUnchangedCatalogTransition} from './catalog-transition-correspondence';
const assertionOwners=new WeakMap<object,'declarations'|'assertion-fields'>();
function registerAssertionOwner<T extends object>(owner:T,mode:'declarations'|'assertion-fields'):T{assertionOwners.set(owner,mode);return owner;}
/** Private loaded-instance recognition; no external issuer or native qualification. */
export function requireLoadedUmfAssertionOwner(owner:object,mode:'declarations'|'assertion-fields'):void{
 if(assertionOwners.get(owner)!==mode)throw Error('Original loaded assertion owner required');
}
export const UMF_RUNTIME_SOURCE='c45c72a2a8a3c4fba61c40c5927dd9091acf8cc3';
export async function loadUmfProducer(directory:string){
 const {hash,captured}=await loadPinnedFunctions(directory,UMF_RUNTIME_SOURCE,'record',['readDocument','validateDocument','validateCoreRecordValues','upgradeSchemaPropertiesEnvelope','verifySchemaPropertiesUpgrade','rollbackSchemaPropertiesEnvelope']);
 return Object.freeze({sourceRevision:UMF_RUNTIME_SOURCE,bundleSha256:hash,
  inspect(originalText:string){
   if(typeof originalText!=='string'||Buffer.byteLength(originalText)>1048576)throw Error('Original document bound');
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
  },
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
