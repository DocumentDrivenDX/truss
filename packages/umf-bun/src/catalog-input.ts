/** Original owner interpretation before native catalog effects. No acceptance authority. */
import {createAcceptanceInputInspector} from './acceptance-input';
import {loadUmfProducer} from './index';
import {collectCatalogDeclarations} from './catalog-declarations';
import type {ProfilePin} from '../../../docs/helix/02-design/contracts/bindings/truss-acceptance-input-v0.1';
export async function createCatalogInputPreparation(directory:string,dependenciesPackage:string){
 const inspector=await createAcceptanceInputInspector(dependenciesPackage);const owner=await loadUmfProducer(directory);
 const umfProfile=Object.freeze({identity:'umf-record-interpretation',version:owner.sourceRevision,sha256:owner.bundleSha256});
 const equal=(a:ProfilePin,b:ProfilePin)=>a.identity===b.identity&&a.version===b.version&&a.sha256===b.sha256;
 return Object.freeze({umfProfile,prepare(original:Uint8Array){
  const inspected=inspector.inspect(original);const documents=[];
  for(let i=0;i<inspected.input.documents.length;i++){
   const declaration=inspected.input.documents[i]!;const source=inspected.documents[i]!;
   if(!equal(declaration.umfProfile,umfProfile))throw Error('Unsupported original UMF profile');
   if(declaration.ingress.kind!=='native')throw Error('Original converted adapter registration unavailable');
   const observation=owner.inspect(source.originalText);
   if(!observation.sourceValidation.valid||!observation.targetValidation?.valid)throw Error('Original UMF validation refused');
   if(observation.source.id!==source.documentId)throw Error('Original document identity mismatch');
   // Original source remains archival authority; the explicit reversible transition
   // is interpretation evidence, never a replacement source artifact.
   documents.push(Object.freeze({documentId:source.documentId,revision:source.documentRevision,umfVersion:observation.source.umf,
    originalText:source.originalText,validation:{sourceValidation:observation.sourceValidation,transition:observation.transition},
    interpretation:observation}));
  }
  const declarations=documents.map(document=>collectCatalogDeclarations(document.documentId,document.interpretation.source));
  const archiveDocuments=documents.map(({interpretation,...archive})=>Object.freeze(archive));
  function freeze(value:unknown):void{if(value&&typeof value==='object'){for(const child of Object.values(value))freeze(child);Object.freeze(value)}}
  freeze(documents);freeze(archiveDocuments);freeze(declarations);
  return Object.freeze({original:inspected,documents:Object.freeze(documents),declarations:Object.freeze(declarations),archiveDocuments:Object.freeze(archiveDocuments),umfProfile,scope:'original_umf_preparation_only' as const});
 }});
}
