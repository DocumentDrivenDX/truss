/** Independent design witnesses; no production runner or native admission. */
type Pin={identity:string;version:string;sha256:string};
type Step={label:string;operation:string;operationProfile:Pin;observationProfile:Pin;scope:{kind:string;label?:string}};
type Artifact={identity:string;bytesBase64:string;sha256:string};
type Inputs={caseId:string;registry:Artifact;grammarProfile:Pin;steps:Step[]};
type Fixtures=Inputs;
type Expected={caseId:string;grammarProfile:Pin}&Record<'result'|'state'|'journal'|'report',{observations:{step:string;boundary:string}[]}>;
type Entry={operation:string;operationProfile:Pin;observationProfile:Pin;scopeKinds:readonly string[]};
function equalPin(a:Pin,b:Pin){return a.identity===b.identity&&a.version===b.version&&a.sha256===b.sha256;}
function admitLinks(caseId:string,inputs:Inputs,expected:Expected,registry:readonly Entry[],knownScopeLabels:ReadonlySet<string>,fixtures:Fixtures):boolean {
 if(inputs.caseId!==caseId||expected.caseId!==caseId||fixtures.caseId!==caseId)return false;
 if(!equalPin(inputs.grammarProfile,fixtures.grammarProfile)||!equalPin(inputs.grammarProfile,expected.grammarProfile))return false;
 if(inputs.registry.identity!==fixtures.registry.identity||inputs.registry.sha256!==fixtures.registry.sha256||inputs.registry.bytesBase64!==fixtures.registry.bytesBase64)return false;
 const entries=new Map<string,Entry>();
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
 for(const surface of ['result','state','journal','report'] as const){
  const observations=new Set<string>();
  for(const observation of expected[surface].observations){
   if(!labels.has(observation.step))return false;
   const key=JSON.stringify([observation.step,observation.boundary]);
   if(observations.has(key))return false;observations.add(key);
  }
 }
 return true;
}
const pin={identity:'registered-test-operation',version:'0.2.0',sha256:'0'.repeat(64)};
const artifact={identity:'test-registry',bytesBase64:'',sha256:'0'.repeat(64)};
const inputs:Inputs={caseId:'case',registry:artifact,grammarProfile:pin,steps:[{label:'read',operation:'observeFreshness',operationProfile:pin,observationProfile:pin,scope:{kind:'adopted',label:'host'}}]};
const expected:Expected={caseId:'case',grammarProfile:pin,result:{observations:[{step:'read',boundary:'pending'}]},state:{observations:[]},journal:{observations:[]},report:{observations:[]}};
const registry:Entry[]=[{operation:'observeFreshness',operationProfile:pin,observationProfile:pin,scopeKinds:['adopted']}];
const fixtures:Fixtures={caseId:'case',registry:artifact,grammarProfile:pin,steps:[{label:'setup',operation:'observeFreshness',operationProfile:pin,observationProfile:pin,scope:{kind:'adopted',label:'host'}}]};
const scope=new Set(['host']);
let count=0;
function witness(name:string,wanted:boolean,change:(i:Inputs,e:Expected,r:Entry[],s:Set<string>,f:Fixtures)=>void){const i=structuredClone(inputs),e=structuredClone(expected),r=structuredClone(registry),s=new Set(scope),f=structuredClone(fixtures);change(i,e,r,s,f);if(admitLinks('case',i,e,r,s,f)!==wanted)throw new Error(name);count++;}
witness('coherent authored links',true,()=>{});
witness('different expected case',false,(_i,e)=>e.caseId='other');
witness('duplicate step label',false,i=>i.steps.push(structuredClone(i.steps[0])));
witness('unknown registered operation',false,i=>i.steps[0].operation='invented');
witness('old feed profile cannot become new',false,i=>i.steps[0].operationProfile={...i.steps[0].operationProfile,version:'0.1.0'});
witness('changed operation hash',false,i=>i.steps[0].operationProfile={...i.steps[0].operationProfile,sha256:'1'.repeat(64)});
witness('unknown scope label',false,i=>i.steps[0].scope.label='ended-or-unknown');
witness('wrong scope kind',false,i=>i.steps[0].scope.kind='none');
witness('unknown observation step',false,(_i,e)=>e.result.observations[0].step='missing');
witness('duplicate observation boundary',false,(_i,e)=>e.result.observations.push(structuredClone(e.result.observations[0])));
witness('duplicate registry operation',false,(_i,_e,r)=>r.push(structuredClone(r[0])));
witness('different fixture case',false,(_i,_e,_r,_s,f)=>f.caseId='other');
witness('changed fixture grammar',false,(_i,_e,_r,_s,f)=>f.grammarProfile.sha256='2'.repeat(64));
witness('changed fixture registry bytes',false,(_i,_e,_r,_s,f)=>f.registry.bytesBase64='AA==');
witness('duplicate setup labels',false,(_i,_e,_r,_s,f)=>f.steps.push(structuredClone(f.steps[0])));
witness('unknown setup operation',false,(_i,_e,_r,_s,f)=>f.steps[0].operation='invented');
witness('setup labels do not bind input observations',false,(_i,e)=>e.result.observations[0].step='setup');
witness('same label in distinct inventories',true,(_i,_e,_r,_s,f)=>f.steps[0].label='read');
witness('changed expected grammar',false,(_i,e)=>e.grammarProfile.sha256='3'.repeat(64));
witness('changed observation procedure',false,i=>i.steps[0].observationProfile={...i.steps[0].observationProfile,sha256:'4'.repeat(64)});
console.log(count+' independent cross-artifact controls passed. Assumes shape-admitted inputs; scope liveness, artifact authenticity and complete semantic observations remain unqualified.');
