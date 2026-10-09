/** Independent design witnesses; no production runner or native admission. */
type Pin={identity:string;version:string;sha256:string};
type Step={label:string;operation:string;operationProfile:Pin;scope:{kind:string;label?:string}};
type Inputs={caseId:string;steps:Step[]};
type Expected={caseId:string}&Record<'result'|'state'|'journal'|'report',{observations:{step:string;boundary:string}[]}>;
type Entry={operation:string;profile:Pin;scopeKinds:readonly string[]};
function equalPin(a:Pin,b:Pin){return a.identity===b.identity&&a.version===b.version&&a.sha256===b.sha256;}
function admitLinks(caseId:string,inputs:Inputs,expected:Expected,registry:readonly Entry[],knownScopeLabels:ReadonlySet<string>):boolean {
 if(inputs.caseId!==caseId||expected.caseId!==caseId)return false;
 const entries=new Map<string,Entry>();
 for(const entry of registry){if(entries.has(entry.operation))return false;entries.set(entry.operation,entry);}
 const labels=new Set<string>();
 for(const step of inputs.steps){
  if(labels.has(step.label))return false;labels.add(step.label);
  const entry=entries.get(step.operation);
  if(!entry||!equalPin(entry.profile,step.operationProfile)||!entry.scopeKinds.includes(step.scope.kind))return false;
  if(step.scope.kind!=='none'&&(!step.scope.label||!knownScopeLabels.has(step.scope.label)))return false;
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
const inputs:Inputs={caseId:'case',steps:[{label:'read',operation:'observeFreshness',operationProfile:pin,scope:{kind:'adopted',label:'host'}}]};
const expected:Expected={caseId:'case',result:{observations:[{step:'read',boundary:'pending'}]},state:{observations:[]},journal:{observations:[]},report:{observations:[]}};
const registry:Entry[]=[{operation:'observeFreshness',profile:pin,scopeKinds:['adopted']}];
const scope=new Set(['host']);
let count=0;
function witness(name:string,wanted:boolean,change:(i:Inputs,e:Expected,r:Entry[],s:Set<string>)=>void){const i=structuredClone(inputs),e=structuredClone(expected),r=structuredClone(registry),s=new Set(scope);change(i,e,r,s);if(admitLinks('case',i,e,r,s)!==wanted)throw new Error(name);count++;}
witness('coherent authored links',true,()=>{});
witness('different expected case',false,(_i,e)=>e.caseId='other');
witness('duplicate step label',false,i=>i.steps.push(structuredClone(i.steps[0])));
witness('unknown registered operation',false,i=>i.steps[0].operation='invented');
witness('old feed profile cannot become new',false,i=>i.steps[0].operationProfile.version='0.1.0');
witness('changed operation hash',false,i=>i.steps[0].operationProfile.sha256='1'.repeat(64));
witness('unknown scope label',false,i=>i.steps[0].scope.label='ended-or-unknown');
witness('wrong scope kind',false,i=>i.steps[0].scope.kind='none');
witness('unknown observation step',false,(_i,e)=>e.result.observations[0].step='missing');
witness('duplicate observation boundary',false,(_i,e)=>e.result.observations.push(structuredClone(e.result.observations[0])));
witness('duplicate registry operation',false,(_i,_e,r)=>r.push(structuredClone(r[0])));
console.log(count+' independent cross-artifact controls passed. Assumes shape-admitted inputs; scope liveness, artifact authenticity and complete semantic observations remain unqualified.');
