/** Trusted host startup pin custody. Resolution alone is not semantic admission. */
import {createHash} from 'node:crypto';
import type {AcceptanceInput,ProfilePin,ExactArtifact} from '../../../docs/helix/02-design/contracts/bindings/truss-acceptance-input-v0.1';
export type AcceptanceProfileRole='layout'|'acceptance'|'validator'|'support'|'policy'|'umf'|'adapter'|'binding'|'transform'|'report';
export interface AcceptanceProfileRegistration {
 readonly role:AcceptanceProfileRole;
 readonly profile:ProfilePin;
 readonly artifactIdentity:string;
 readonly bytes:Uint8Array;
}
const originalResolvers=new WeakSet<object>();
/** Startup byte-custody recognition only; not registered semantic authority. */
export function requireOriginalAcceptanceProfileResolver(resolver:object):void{
 if(!originalResolvers.has(resolver))throw Error('Original profile byte-custody resolver required');
}
export function createAcceptanceProfileResolver(registrations:readonly AcceptanceProfileRegistration[]){
 if(registrations.length>4096)throw Error('Registered profile capacity exceeded');
 let total=0;
 const entries=registrations.map(registration=>{
  const {role}=registration;const profile={...registration.profile};
  if(!['layout','acceptance','validator','support','policy','umf','adapter','binding','transform','report'].includes(role))throw Error('Unknown registered profile role');
  if(!profile.identity||!profile.version||!registration.artifactIdentity||!(/^[0-9a-f]{64}$/).test(profile.sha256))throw Error('Invalid original profile pin');
  if(!(registration.bytes.buffer instanceof ArrayBuffer))throw Error('Original profile byte custody required');
  if(registration.bytes.length>1048576||(total+=registration.bytes.length)>4194304)throw Error('Registered profile bytes exceeded');
  const owned=Buffer.from(registration.bytes);
  if(createHash('sha256').update(owned).digest('hex')!==profile.sha256)throw Error('Original profile artifact hash mismatch');
  const artifact:ExactArtifact=Object.freeze({identity:registration.artifactIdentity,bytesBase64:owned.toString('base64'),sha256:profile.sha256});
  return Object.freeze({role,profile:Object.freeze(profile),artifact});
 });
 for(let i=0;i<entries.length;i++)for(let j=0;j<i;j++)if(entries[i].role===entries[j].role&&entries[i].profile.identity===entries[j].profile.identity&&entries[i].profile.version===entries[j].profile.version)throw Error('Duplicate original profile registration');
 const resolver=Object.freeze({resolveReport(pin:ProfilePin){
  const entry=entries.find(entry=>entry.role==='report'&&entry.profile.identity===pin.identity&&entry.profile.version===pin.version&&entry.profile.sha256===pin.sha256);
  if(!entry)throw Error('Original registered report profile unavailable');
  return Object.freeze({profile:entry.profile,artifact:entry.artifact,scope:'original_registered_report_bytes_only' as const});
 },resolve(input:AcceptanceInput){
  const resolved:{pointer:string;role:AcceptanceProfileRole;profile:ProfilePin;artifact:ExactArtifact}[]=[];
  function require(role:AcceptanceProfileRole,pin:ProfilePin,pointer:string){
   const entry=entries.find(entry=>entry.role===role&&entry.profile.identity===pin.identity&&entry.profile.version===pin.version&&entry.profile.sha256===pin.sha256);
   if(!entry)throw Error('Original registered profile unavailable: '+pointer);
   resolved.push(Object.freeze({pointer,...entry}));
  }
  require('layout',input.layoutProfile,'/layoutProfile');require('acceptance',input.acceptanceProfile,'/acceptanceProfile');
  require('validator',input.validatorProfile,'/validatorProfile');require('support',input.supportProfile,'/supportProfile');require('policy',input.policy.profile,'/policy/profile');
  input.documents.forEach((document,index)=>{require('umf',document.umfProfile,`/documents/${index}/umfProfile`);if(document.ingress.kind==='converted')require('adapter',document.ingress.adapterProfile,`/documents/${index}/ingress/adapterProfile`)});
  if(input.binding.state==='present')require('binding',input.binding.vocabulary,'/binding/vocabulary');
  input.transforms.forEach((transform,index)=>require('transform',transform.registration,`/transforms/${index}/registration`));
  return Object.freeze({profiles:Object.freeze(resolved),scope:'original_registered_pin_resolution_only' as const});
 }});
 originalResolvers.add(resolver);return resolver;
}
