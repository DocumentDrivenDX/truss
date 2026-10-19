// SPDX-License-Identifier: MIT OR Apache-2.0
/** Pinned UMF 0.10 source validation and Truss key-body producer. */
import {resolve} from 'node:path';

export const UMF_CORE10_CATALOG_SOURCE='d187bfa7d7de5f3cd94dea314eed003a35bb6c82';

/** Load the sole current UMF producer and validate an original 0.10 document. */
export async function loadCore10CatalogOwner(directory:string){
 const revision=UMF_CORE10_CATALOG_SOURCE;
 const {hash,captured}=await loadPinnedFunctions(directory,revision,'core10-catalog',[
  'readJsonValue','validateSemanticTypesDocument','encodeCoreKeyTupleBody']);
 return Object.freeze({sourceRevision:revision,bundleSha256:hash,
  inspect(originalText:string){
   if(typeof originalText!=='string'||Buffer.byteLength(originalText)>4194304)throw Error('Original document bound');
   const source=captured.readJsonValue(originalText,'json');
   if(source?.umf!=='0.10.0')throw Error('Unsupported original UMF version');
   const sourceValidation=captured.validateSemanticTypesDocument(source);
   return {originalText,source,sourceValidation,transition:null,targetValidation:sourceValidation,target:source};
  }});
}

/** Context-free exact-number conveniences from the current owner source. */
export async function loadCurrentNumericOwner(directory:string){
 const {hash,captured}=await loadPinnedFunctions(directory,UMF_CORE10_CATALOG_SOURCE,'numeric-current',[
  'exactDecimal','integerFromBigInt','integerToBigInt','admitJavascriptNumber','numericToNumberLossless',
  'readJsonValue','validateSemanticTypesDocument','encodeCoreKeyTupleBody']);
 return Object.freeze({sourceRevision:UMF_CORE10_CATALOG_SOURCE,bundleSha256:hash,...captured});
}

async function loadPinnedFunctions<const Names extends readonly string[]>(directory:string,revision:string,mode:string,names:Names){
 const root=resolve(directory);const manifest=await Bun.file(root+'/producer-manifest.json').json();
 const bytes=await Bun.file(root+'/producer.js').arrayBuffer();
 const hash=new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
 if(manifest.revision!==revision||manifest.producerMode!==mode||manifest.bundleSha256!==hash)throw Error('Original UMF producer pin mismatch');
 const owner=await import(root+'/producer.js');
 const captured=Object.fromEntries(names.map(name=>{if(typeof owner[name]!=='function')throw Error('Missing original producer');return [name,owner[name].bind(owner)]})) as {[Name in Names[number]]:(...args:any[])=>any};
 return {hash,captured};
}
