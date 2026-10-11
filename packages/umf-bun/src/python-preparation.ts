/** Installed Python ingress for the existing original catalog preparation route. */
import {resolve} from 'node:path';
import {createCatalogInputPreparation} from './catalog-input';
import {loadUmfProducer} from './index';
import {collectCatalogValidationEvidence} from './catalog-validation-evidence';
import {collectCatalogExtensionArtifacts} from './catalog-extension-artifacts';
import {collectCatalogIngressReportBasis} from './catalog-ingress-report-basis';
import {decodeAcceptanceJson,preflightSourceJson} from '../../postgresql/src/acceptance-json';
const root=resolve(import.meta.dir,'../../..');
const MAX_OUTPUT=16777216;
const emit=(value:unknown)=>{
 const text=JSON.stringify(value);
 console.log(Buffer.byteLength(text)+1<=MAX_OUTPUT?text:JSON.stringify({status:'refused',reason:'resource',diagnostics:[]}));
};
let diagnostics:unknown[]=[];
try{
 const bytes=new Uint8Array(await Bun.stdin.arrayBuffer());
 if(bytes.length>1048576)throw Error('resource');
 const request=decodeAcceptanceJson(bytes) as any;
 if(Object.keys(request).sort().join(',')!=='configurationHex,documents'||typeof request.configurationHex!=='string'
   ||!/^(?:[0-9a-f]{2})+$/.test(request.configurationHex)||!Array.isArray(request.documents)||request.documents.length<1||request.documents.length>512)throw Error('invalid_input');
 const configuration=decodeAcceptanceJson(Buffer.from(request.configurationHex,'hex')) as any;
 if(!configuration||typeof configuration!=='object'||Array.isArray(configuration)
   ||Object.hasOwn(configuration,'documents')||Object.hasOwn(configuration,'interfaceVersion'))throw Error('invalid_input');
 const preparation=await createCatalogInputPreparation(root+'/owner',root+'/runtime/package.json');
 const owner=await loadUmfProducer(root+'/owner');
 const documents=request.documents.map((d:any)=>{
  if(!d||Object.keys(d).sort().join(',')!=='artifact,documentId,documentRevision')throw Error('invalid_input');
  return {...d,umfProfile:preparation.umfProfile,ingress:{kind:'native'}};
 });
 const input={interfaceVersion:'truss-acceptance-input/0.1.0',...configuration,documents};
 const original=new TextEncoder().encode(JSON.stringify(input));
 // Original inspector verifies carriers before the extra diagnostics observation.
 const {createAcceptanceInputInspector}=await import('./acceptance-input');
 const inspected=(await createAcceptanceInputInspector(root+'/runtime/package.json')).inspect(original);
 for(const source of inspected.documents){
  try{
   preflightSourceJson(new TextEncoder().encode(source.originalText));
   const observation=owner.inspect(source.originalText);
   diagnostics.push({documentId:source.documentId,documentRevision:source.documentRevision,observation});
  }catch(error){
   const message=error instanceof Error?error.message:'Original document refused';
   diagnostics.push({documentId:source.documentId,documentRevision:source.documentRevision,
    originalError:{message:message.slice(0,8192),truncated:message.length>8192
      ||(typeof (error as any)?.code==='string'&&(error as any).code.length>256)
      ||(typeof (error as any)?.path==='string'&&(error as any).path.length>8192),
     ...(typeof (error as any)?.code==='string'?{code:(error as any).code.slice(0,256)}:{}),
     ...(typeof (error as any)?.path==='string'?{path:(error as any).path.slice(0,8192)}:{})}});
  }
 }
 if(diagnostics.some((d:any)=>d.originalError||!d.observation.sourceValidation.valid||!d.observation.targetValidation?.valid)){
  emit({status:'refused',reason:'invalid_document',diagnostics});
 }else{
  const prepared=preparation.prepare(original);
  let reportEvidence:unknown;
  try { reportEvidence={validation:collectCatalogValidationEvidence(prepared),
    retainedExtensions:collectCatalogExtensionArtifacts(prepared),
    ingress:prepared.original.input.binding.state==='absent'&&!prepared.original.input.transforms.length
     ?{state:'available',basis:collectCatalogIngressReportBasis(prepared)}
     :{state:'unavailable',reason:'registered_binding_or_transform_report_producer_required'},
    scope:'original_owner_report_preparation_only'};
  } catch { reportEvidence={scope:'original_owner_report_preparation_only',ingress:{state:'unavailable',reason:'report_evidence_unavailable'}}; }
  const response:any={status:'prepared',inputHex:prepared.original.originalUtf8Hex,documents:prepared.documents,
   declarations:prepared.declarations,archiveDocuments:prepared.archiveDocuments,
   reportEvidence,
   provenance:{umfProfile:prepared.umfProfile,schemaSha256:prepared.original.schemaSha256,scope:prepared.scope}};
  if(Buffer.byteLength(JSON.stringify(response))+1>MAX_OUTPUT)response.reportEvidence={scope:'original_owner_report_preparation_only',ingress:{state:'unavailable',reason:'report_evidence_resource'}};
  emit(response);
 }
}catch(error){
 const message=error instanceof Error?error.message:'';
 const reason=message==='resource'?'resource':message.includes('Unsupported')?'unsupported_profile':message.includes('pin mismatch')||message.includes('Missing original producer')?'producer_unavailable':'invalid_input';
 emit({status:'refused',reason,diagnostics});
}
