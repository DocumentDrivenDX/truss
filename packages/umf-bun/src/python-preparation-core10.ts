// SPDX-License-Identifier: MIT OR Apache-2.0
/** Installed Python ingress for the existing original catalog preparation route. */
import {resolve} from 'node:path';
import {createCatalogInputPreparation} from './catalog-input';
import {CatalogDocumentRejected} from './catalog-input';
import {decodeAcceptanceJson,decodeCatalogPreparationJson} from '../../postgresql/src/acceptance-json';
const root=resolve(import.meta.dir);
const dependencies=resolve(root,'../_umf/runtime/package.json');
const schemaUrl=new URL('./acceptance-input-v0.1.schema.json',import.meta.url);
const MAX_OUTPUT=67108864;
const emit=(value:unknown)=>{
 const text=JSON.stringify(value);
 console.log(Buffer.byteLength(text)+1<=MAX_OUTPUT?text:JSON.stringify({status:'refused',reason:'resource',diagnostics:[]}));
};
let diagnostics:unknown[]=[];
try{
 const bytes=new Uint8Array(await Bun.stdin.arrayBuffer());
 if(bytes.length>16777216)throw Error('resource');
 const request=decodeCatalogPreparationJson(bytes) as any;
 if(!['configurationHex,documents','configurationHex,documents,registration'].includes(Object.keys(request).sort().join(','))||(Object.hasOwn(request,'registration')&&request.registration!==true)||typeof request.configurationHex!=='string'
   ||!/^(?:[0-9a-f]{2})+$/.test(request.configurationHex)||!Array.isArray(request.documents)||request.documents.length<1||request.documents.length>512)throw Error('invalid_input');
 const configuration=decodeAcceptanceJson(Buffer.from(request.configurationHex,'hex')) as any;
 if(!configuration||typeof configuration!=='object'||Array.isArray(configuration)
   ||Object.hasOwn(configuration,'documents')||Object.hasOwn(configuration,'interfaceVersion'))throw Error('invalid_input');
 const preparation=await createCatalogInputPreparation(root,dependencies,schemaUrl);
 const documents=request.documents.map((d:any)=>{
  if(!d||Object.keys(d).sort().join(',')!=='artifact,documentId,documentRevision')throw Error('invalid_input');
  return {...d,umfProfile:preparation.umfProfile,ingress:{kind:'native'}};
 });
 const input={interfaceVersion:'truss-acceptance-input/0.1.0',...configuration,documents};
 const original=new TextEncoder().encode(JSON.stringify(input));
  const prepared=preparation.prepare(original);
  // Every preparation entrypoint uses the validator result already obtained.
  // Inspector transcripts are not a prerequisite for preparing a schema.
  const reportEvidence={interfaceVersion:'truss-registration-preparation/2.0',
    documents:prepared.documents.map((document,index)=>({documentId:document.documentId,
      contentSha256:prepared.original.documents[index]!.sha256,
      validation:document.interpretation.sourceValidation,
      ...(document.interpretation.dddProfile?{dddProfile:document.interpretation.dddProfile}:{}),
      ...(document.interpretation.dddValidation?{dddValidation:document.interpretation.dddValidation}:{})}))};
  const descriptor={...prepared.original.input,interfaceVersion:'truss-acceptance-input/0.2.0',
    documents:prepared.original.input.documents.map(document=>({...document,
      artifact:{identity:document.artifact.identity,sha256:document.artifact.sha256}}))};
  const response:any={status:'prepared',input:descriptor,
   documents:prepared.documents.map(document=>({documentId:document.documentId,revision:document.revision,
     umfVersion:document.umfVersion,validation:document.interpretation.sourceValidation,
     ...(document.interpretation.dddProfile?{dddProfile:document.interpretation.dddProfile}:{}),
     ...(document.interpretation.dddValidation?{dddValidation:document.interpretation.dddValidation}:{})})),
   reportEvidence,
   provenance:{umfProfile:prepared.umfProfile,schemaSha256:prepared.original.schemaSha256,scope:prepared.scope}};
  emit(response);

}catch(error){
 if(error instanceof CatalogDocumentRejected){
  const cause=error.originalError as any;const message=cause instanceof Error?cause.message:'Original document refused';
  diagnostics=[{documentId:error.documentId,documentRevision:error.documentRevision,
   ...(error.observation?{validation:(error.observation as any).sourceValidation,
    ...((error.observation as any).dddProfile?{dddProfile:(error.observation as any).dddProfile}:{}),
    ...((error.observation as any).dddValidation?{dddValidation:(error.observation as any).dddValidation}:{})}:{originalError:{message:message.slice(0,8192),truncated:message.length>8192,
    ...(typeof cause?.code==='string'?{code:cause.code.slice(0,256)}:{}),...(typeof cause?.path==='string'?{path:cause.path.slice(0,8192)}:{})}})}];
 }
 const message=error instanceof Error?error.message:'';
 const reason=message==='invalid_document'?'invalid_document':message==='resource'?'resource':message.includes('Unsupported')?'unsupported_profile':message.includes('pin mismatch')||message.includes('Missing original producer')?'producer_unavailable':'invalid_input';
 emit({status:'refused',reason,diagnostics});
}
