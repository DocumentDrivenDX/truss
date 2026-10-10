/** Host-only complete wire inspection, not semantic/native acceptance authority. */
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {decodeAcceptanceJson} from '../../postgresql/src/acceptance-json';
import type {AcceptanceInput,ExactArtifact} from '../../../docs/helix/02-design/contracts/bindings/truss-acceptance-input-v0.1';
const SCHEMA_SHA='0278cbbbde843091c005b688fd9c081a2fdff843b9adda006ba80fb87828d7cd';
const digest=(bytes:Uint8Array)=>createHash('sha256').update(bytes).digest('hex');
export class AcceptanceInputInspectionError extends Error {
 constructor(readonly reason:'schema'|'artifact_integrity'|'document_identity'|'resource'|'document_encoding'|'source_custody'){super(reason)}
}
/** dependenciesPackage is trusted host startup configuration, never document input. */
export async function createAcceptanceInputInspector(dependenciesPackage:string){
 const schemaBytes=await readFile(new URL('../../../docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json',import.meta.url));
 if(digest(schemaBytes)!==SCHEMA_SHA)throw Error('Original acceptance schema pin mismatch');
 const require=createRequire(dependenciesPackage);const Ajv=require('ajv/dist/2020').default;
 const validate=new Ajv({strict:true}).compile(JSON.parse(schemaBytes.toString('utf8')));
 return Object.freeze({schemaSha256:SCHEMA_SHA,inspect(original:Uint8Array){
  if(!(original.buffer instanceof ArrayBuffer))throw new AcceptanceInputInspectionError('source_custody');
  if(original.length>1048576)throw new AcceptanceInputInspectionError('resource');
  const owned=original.slice();const input=decodeAcceptanceJson(owned);if(!validate(input))throw new AcceptanceInputInspectionError('schema');
  const wire=input as unknown as AcceptanceInput;
  if(wire.documents.length>512)throw new AcceptanceInputInspectionError('resource');
  let totalArtifacts=0;const documents:{documentId:string;documentRevision:string;originalText:string;sha256:string}[]=[];const identities=new Set<string>();
  function artifact(value:ExactArtifact):Buffer{
   const bytes=Buffer.from(value.bytesBase64,'base64');
   if(bytes.toString('base64')!==value.bytesBase64||digest(bytes)!==value.sha256)throw new AcceptanceInputInspectionError('artifact_integrity');
   totalArtifacts+=bytes.length;if(bytes.length>1048576||totalArtifacts>4194304)throw new AcceptanceInputInspectionError('resource');return bytes;
  }
  for(const document of wire.documents){
   if(identities.has(document.documentId))throw new AcceptanceInputInspectionError('document_identity');identities.add(document.documentId);
   const bytes=artifact(document.artifact);let text:string;
   try{text=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes)}catch{throw new AcceptanceInputInspectionError('document_encoding')}
   documents.push(Object.freeze({documentId:document.documentId,documentRevision:document.documentRevision,originalText:text,sha256:document.artifact.sha256}));
   if(document.ingress.kind==='converted'){artifact(document.ingress.source);artifact(document.ingress.lossReport)}
  }
  if(wire.binding.state==='present')artifact(wire.binding.artifact);
  function freeze(value:unknown):void{if(value&&typeof value==='object'){for(const child of Object.values(value))freeze(child);Object.freeze(value)}}freeze(wire);
  return Object.freeze({input:wire,documents:Object.freeze(documents),originalUtf8Hex:Buffer.from(owned).toString('hex'),schemaSha256:SCHEMA_SHA,scope:'wire_and_artifact_inspection_only' as const});
 }});
}
