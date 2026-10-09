/** Exact original producer validation observations; no accepted report or support claim. */
import {createHash} from 'node:crypto';
import {requireOriginalCatalogPreparation,type createCatalogInputPreparation} from './catalog-input';
type Prepared=ReturnType<Awaited<ReturnType<typeof createCatalogInputPreparation>>['prepare']>;
export function collectCatalogValidationEvidence(prepared:Prepared){
 requireOriginalCatalogPreparation(prepared);let retained=0,diagnosticCount=0;
 const artifact=(identity:string,value:unknown)=>{const bytes=Buffer.from(JSON.stringify(value),'utf8');retained+=bytes.length;if(retained>4194304)throw Error('Validation evidence component output capacity exceeded');return Object.freeze({identity,bytesBase64:bytes.toString('base64'),sha256:createHash('sha256').update(bytes).digest('hex')})};
 const manifest=artifact('truss.umf-validation-evidence-profile/0.1.0',{interfaceVersion:'truss-umf-validation-evidence/0.1.0',producer:prepared.umfProfile,encoding:'UTF-8 JSON native diagnostic wrapper; no code/path/severity remapping',basis:['original','reversible_target'],sourcePointer:'whole original document',completeness:'both source and interpretation-target owner validation complete'});
 const profile=Object.freeze({identity:'truss-umf-validation-evidence',version:'0.1.0',sha256:manifest.sha256});
 const diagnostics:{classification:'upstream_validation';source:{kind:'document';artifact:Prepared['original']['input']['documents'][number]['artifact'];sourcePointer:''};diagnosticProfile:typeof profile;diagnostic:ReturnType<typeof artifact>}[]=[];
 const interpretations=prepared.documents.map((document,index)=>{
  const observation=document.interpretation,source=prepared.original.input.documents[index].artifact;
  const validations=[{basis:'original',validation:observation.sourceValidation}];
  if(observation.transition)validations.push({basis:'reversible_target',validation:observation.targetValidation});
  for(const {basis,validation} of validations){
   if(!validation||typeof validation.complete!=='boolean'||!Array.isArray(validation.diagnostics))throw Error('Original validation observation required');
   for(let di=0;di<validation.diagnostics.length;di++){
    if(++diagnosticCount>4096)throw Error('Validation diagnostic component capacity exceeded');
    const diagnostic=artifact(`truss.original-umf-diagnostic/${index}/${basis}/${di}`,{profile,producer:prepared.umfProfile,documentId:document.documentId,contentSha256:source.sha256,basis,diagnostic:validation.diagnostics[di]});
    // Target paths stay inside their target-basis artifact, never relabeled as
    // an authored source node. The carrier source references the whole original.
    diagnostics.push(Object.freeze({classification:'upstream_validation',source:Object.freeze({kind:'document',artifact:source,sourcePointer:''}),diagnosticProfile:profile,diagnostic}));
   }
  }
  if(typeof observation.targetValidation?.complete!=='boolean')throw Error('Original target validation required');
  const evidence=artifact('truss.original-umf-observation/'+document.documentId,{producer:prepared.umfProfile,observation});
  return Object.freeze({documentId:document.documentId,contentSha256:source.sha256,interpretationProfile:prepared.umfProfile,
   completeness:observation.sourceValidation.complete&&observation.targetValidation.complete?'complete' as const:'partial' as const,evidence});
 });
 return Object.freeze({profile,manifest,diagnostics:Object.freeze(diagnostics),documentInterpretations:Object.freeze(interpretations),scope:'original_producer_validation_evidence_only' as const});
}
