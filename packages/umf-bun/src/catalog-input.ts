// SPDX-License-Identifier: MIT OR Apache-2.0
/** Original owner interpretation before native catalog effects. No acceptance authority. */
import {createAcceptanceInputInspector} from './acceptance-input';
import {loadCore10CatalogOwner} from './index';
import {collectCatalogDeclarations} from './catalog-declarations';
import type {ProfilePin} from '../../../docs/helix/02-design/contracts/bindings/truss-acceptance-input-v0.1';
export class CatalogDocumentRejected extends Error {
 constructor(readonly documentId:string,readonly documentRevision:string,readonly originalError:unknown,readonly observation?:unknown){super('invalid_document');}
}
const originalPreparations=new WeakSet<object>();
/** Private validated preparation recognition, not operation or acceptance authority. */
export function requireOriginalCatalogPreparation(prepared:object):void{
 if(!originalPreparations.has(prepared))throw Error('Original validated catalog preparation required');
}
export async function createCatalogInputPreparation(directory:string,dependenciesPackage:string,schemaUrl?:URL){
 return createPreparation(directory,dependenciesPackage,schemaUrl);
}
async function createPreparation(directory:string,dependenciesPackage:string,schemaUrl?:URL){
 const inspector=await createAcceptanceInputInspector(dependenciesPackage,schemaUrl);const owner=await loadCore10CatalogOwner(directory);
 const umfProfile=Object.freeze({identity:'umf-core-document-validation',version:owner.sourceRevision,sha256:owner.bundleSha256});
 const equal=(a:ProfilePin,b:ProfilePin)=>a.identity===b.identity&&a.version===b.version&&a.sha256===b.sha256;
 return Object.freeze({umfProfile,prepare(original:Uint8Array){
   const inspected=inspector.inspect(original);
  const documents:{documentId:string;revision:string;umfVersion:string;originalText:string;
   validation:{sourceValidation:ReturnType<typeof owner.inspect>['sourceValidation']};
   interpretation:ReturnType<typeof owner.inspect>}[]=[];
  for(let i=0;i<inspected.input.documents.length;i++){
   const declaration=inspected.input.documents[i]!;const source=inspected.documents[i]!;
   if(!equal(declaration.umfProfile,umfProfile))throw Error('Unsupported original UMF profile');
   if(declaration.ingress.kind!=='native')throw Error('Original converted adapter registration unavailable');
   let observation;
   try {observation=owner.inspect(source.originalText);}
   catch(error){throw new CatalogDocumentRejected(source.documentId,source.documentRevision,error);}

   if(!observation.sourceValidation.valid)throw new CatalogDocumentRejected(source.documentId,source.documentRevision,null,observation);
   if(observation.source.id!==source.documentId)throw Error('Original document identity mismatch');
   // Preserve the actual current source and its original validation result.
   documents.push(Object.freeze({documentId:source.documentId,revision:source.documentRevision,umfVersion:observation.source.umf,
    originalText:source.originalText,validation:{sourceValidation:observation.sourceValidation},
    interpretation:observation}));
  }
  const declarations=()=>documents.map(document=>collectCatalogDeclarations(document.documentId,document.interpretation.source));
  const archiveDocuments=documents.map(({interpretation,...archive})=>Object.freeze(archive));
  const frozen=new WeakSet<object>();
  function freeze(value:unknown):void{if(value&&typeof value==='object'&&!frozen.has(value)){frozen.add(value);for(const child of Object.values(value))freeze(child);Object.freeze(value)}}
  freeze(documents);freeze(archiveDocuments);
  const prepared=Object.freeze({original:inspected,documents:Object.freeze(documents),get declarations(){return Object.freeze(declarations())},archiveDocuments:Object.freeze(archiveDocuments),umfProfile,scope:'original_umf_preparation_only' as const});
  originalPreparations.add(prepared);return prepared;
 }});
}
