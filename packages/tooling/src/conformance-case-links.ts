/** Private C2 structural link check over shape-admitted, bounded projections.
 * Does not establish artifact authenticity, native scope or observer completeness. */
export type ConformanceLinkPin={identity:string;version:string;sha256:string};
export type ConformanceLinkStep={label:string;operation:string;operationProfile:ConformanceLinkPin;observationProfile:ConformanceLinkPin;scope:{kind:string;label?:string}};
export type ConformanceLinkArtifact={identity:string;bytesBase64:string;sha256:string};
export type ConformanceLinkInputs={caseId:string;registry:ConformanceLinkArtifact;grammarProfile:ConformanceLinkPin;steps:ConformanceLinkStep[]};
export type ConformanceLinkFixtures=ConformanceLinkInputs;
export type ConformanceLinkExpected={caseId:string;grammarProfile:ConformanceLinkPin}&Record<'result'|'state'|'journal'|'report',{observations:{step:string;boundary:string}[]}> & {performance?:{observations:{step:string;boundary:string}[]}};
export type ConformanceLinkEntry={operation:string;operationProfile:ConformanceLinkPin;observationProfile:ConformanceLinkPin;scopeKinds:readonly string[]};
function equalPin(a:ConformanceLinkPin,b:ConformanceLinkPin){return a.identity===b.identity&&a.version===b.version&&a.sha256===b.sha256;}
export function checkAdmittedConformanceCaseLinks(caseId:string,inputs:ConformanceLinkInputs,expected:ConformanceLinkExpected,registry:readonly ConformanceLinkEntry[],knownScopeLabels:ReadonlySet<string>,fixtures:ConformanceLinkFixtures):boolean {
 if(inputs.caseId!==caseId||expected.caseId!==caseId||fixtures.caseId!==caseId)return false;
 if(!equalPin(inputs.grammarProfile,fixtures.grammarProfile)||!equalPin(inputs.grammarProfile,expected.grammarProfile))return false;
 if(inputs.registry.identity!==fixtures.registry.identity||inputs.registry.sha256!==fixtures.registry.sha256||inputs.registry.bytesBase64!==fixtures.registry.bytesBase64)return false;
 const entries=new Map<string,ConformanceLinkEntry>();
 for(const entry of registry){if(entries.has(entry.operation))return false;entries.set(entry.operation,entry);}
 const labels=new Set<string>();
 for(const steps of [fixtures.steps,inputs.steps]){
 const localLabels=new Set<string>();
 for(const step of steps){
  if(localLabels.has(step.label))return false;localLabels.add(step.label);
  if(steps===inputs.steps)labels.add(step.label);
  const entry=entries.get(step.operation);
  if(!entry||!equalPin(entry.operationProfile,step.operationProfile)||!equalPin(entry.observationProfile,step.observationProfile)||!entry.scopeKinds.includes(step.scope.kind))return false;
  if(step.scope.kind!=='none'&&(!step.scope.label||!knownScopeLabels.has(step.scope.label)))return false;
 }
 }
 for(const surface of ['result','state','journal','report','performance'] as const){
  const observations=new Set<string>();
  for(const observation of expected[surface]?.observations ?? []){
   if(!labels.has(observation.step))return false;
   const key=JSON.stringify([observation.step,observation.boundary]);
   if(observations.has(key))return false;observations.add(key);
  }
 }
 return true;
}
