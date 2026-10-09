/** Synthetic admitted-surface projections only; no native namespace or result authority. */
type Pin={identity:string;version:string;sha256:string};
type Artifact={identity:string;bytesBase64:string;sha256:string};
type Namespace={identity:string;entityKind:string;identityProfile:Pin;originalBasis:Artifact};
type Path={operation:string;surface:string;surfaceProfile:Pin;pointer:string;namespaceIdentity:string;identityProfile:Pin;entityKind:string};
type Alias={symbol:string;namespaceIdentity:string;bind:{kind:'setup';pointer:string}|{kind:'operation_result';operationIndex:string;pointer:string}};
type Surface={operation:string;profile:Pin;eligible:boolean;value:unknown;namespaceBasis:Record<string,Artifact>};
const same=(a:Pin,b:Pin)=>a.identity===b.identity&&a.version===b.version&&a.sha256===b.sha256;
const sameArtifact=(a:Artifact,b:Artifact)=>a.identity===b.identity&&a.bytesBase64===b.bytesBase64&&a.sha256===b.sha256;
function resolve(value:unknown,pointer:string):unknown{
 if(!/^(?:\/(?:[^~\/]|~[01])*)*$/.test(pointer))return undefined;
 if(pointer==='')return value;
 let node:any=value;
 for(const token of pointer.slice(1).split('/')){
  const key=token.replace(/~1/g,'/').replace(/~0/g,'~');
  if(node===null||typeof node!=='object')return undefined;
  if(Array.isArray(node)&&(!/^(0|[1-9][0-9]*)$/.test(key)||BigInt(key)>=BigInt(node.length)))return undefined;
  if(!Object.hasOwn(node,key))return undefined;node=node[key];
 }
 return node;
}
function admit(namespaces:Namespace[],paths:Path[],aliases:Alias[],setup:Surface,results:Surface[]):boolean{
 const domains=new Map<string,Namespace>();
 for(const n of namespaces){if(domains.has(n.identity))return false;domains.set(n.identity,n);}
 const occurrences=new Set<string>();
 for(const p of paths){
  const n=domains.get(p.namespaceIdentity);if(!n||n.entityKind!==p.entityKind||!same(n.identityProfile,p.identityProfile))return false;
  const key=JSON.stringify([p.operation,p.surface,p.surfaceProfile.identity,p.surfaceProfile.version,p.surfaceProfile.sha256,p.pointer]);
  if(occurrences.has(key))return false;occurrences.add(key);
 }
 const symbols=new Set<string>();
 for(const a of aliases){
  const n=domains.get(a.namespaceIdentity);if(!n||symbols.has(a.symbol))return false;symbols.add(a.symbol);
  let surface:Surface,kind:string;
  if(a.bind.kind==='setup'){surface=setup;kind='setup_result';}
  else{
   if(!/^(0|[1-9][0-9]{0,11})$/.test(a.bind.operationIndex)||BigInt(a.bind.operationIndex)>=BigInt(results.length))return false;
   surface=results[Number(a.bind.operationIndex)];kind='result';
  }
  if(!surface.eligible)return false;
  const selected=paths.filter(p=>p.operation===surface.operation&&p.surface===kind&&same(p.surfaceProfile,surface.profile)&&p.pointer===a.bind.pointer&&p.namespaceIdentity===n.identity);
  if(selected.length!==1||!surface.namespaceBasis[n.identity]||!sameArtifact(n.originalBasis,surface.namespaceBasis[n.identity]))return false;
  if(typeof resolve(surface.value,a.bind.pointer)!=='string')return false;
 }
 return true;
}
const pin={identity:'fixture',version:'0.1',sha256:'a'.repeat(64)},basis={identity:'fixture',bytesBase64:'',sha256:pin.sha256};
const namespace:Namespace={identity:'objects',entityKind:'object',identityProfile:pin,originalBasis:basis};
const path:Path={operation:'create',surface:'result',surfaceProfile:pin,pointer:'/value/id',namespaceIdentity:'objects',identityProfile:pin,entityKind:'object'};
const alias:Alias={symbol:'$a',namespaceIdentity:'objects',bind:{kind:'operation_result',operationIndex:'0',pointer:'/value/id'}};
const surface:Surface={operation:'create',profile:pin,eligible:true,value:{value:{id:'9007199254740993'}},namespaceBasis:{objects:basis}};
let count=0;
function witness(name:string,wanted:boolean,change:(n:Namespace[],p:Path[],a:Alias[],s:Surface,r:Surface[])=>void){const n=structuredClone([namespace]),p=structuredClone([path]),a=structuredClone([alias]),s=structuredClone(surface),r=structuredClone([surface]);change(n,p,a,s,r);if(admit(n,p,a,s,r)!==wanted)throw Error(name);count++;}
witness('exact admitted binding projection',true,()=>{});
witness('duplicate namespace',false,n=>n.push(structuredClone(n[0])));
witness('unknown alias namespace',false,(_n,_p,a)=>a[0].namespaceIdentity='foreign');
witness('duplicate alias symbol',false,(_n,_p,a)=>a.push(structuredClone(a[0])));
witness('wrong identity kind',false,(_n,p)=>p[0].entityKind='edge');
witness('changed identity profile',false,(_n,p)=>p[0].identityProfile={...p[0].identityProfile,sha256:'b'.repeat(64)});
witness('duplicate occurrence',false,(_n,p)=>p.push(structuredClone(p[0])));
witness('profile member order cannot hide duplicate',false,(_n,p)=>p.push({...p[0],surfaceProfile:{sha256:pin.sha256,version:pin.version,identity:pin.identity}}));
witness('unknown result index',false,(_n,_p,a)=>{if(a[0].bind.kind==='operation_result')a[0].bind.operationIndex='999999999999';});
witness('ineligible result',false,(_n,_p,_a,_s,r)=>r[0].eligible=false);
witness('missing result member',false,(_n,_p,_a,_s,r)=>r[0].value={value:{}});
witness('host number identity',false,(_n,_p,_a,_s,r)=>r[0].value={value:{id:42}});
witness('changed result profile',false,(_n,_p,_a,_s,r)=>r[0].profile={...r[0].profile,sha256:'c'.repeat(64)});
witness('substituted original namespace basis',false,(_n,_p,_a,_s,r)=>r[0].namespaceBasis.objects={...r[0].namespaceBasis.objects,bytesBase64:'AA=='});
witness('setup binding',true,(_n,p,a)=>{p[0].surface='setup_result';a[0].bind={kind:'setup',pointer:'/value/id'};});
witness('escaped member binding',true,(_n,p,a,_s,r)=>{p[0].pointer='/a~1b/~0';a[0].bind.pointer=p[0].pointer;r[0].value={'a/b':{'~':'1'}};});
witness('object numeric member',true,(_n,p,a,_s,r)=>{p[0].pointer='/0';a[0].bind.pointer='/0';r[0].value={'0':'1'};});
witness('noncanonical array index',false,(_n,p,a,_s,r)=>{p[0].pointer='/00';a[0].bind.pointer='/00';r[0].value=['1'];});
witness('literal star is not wildcard',false,(_n,p,a,_s,r)=>{p[0].pointer='/*';a[0].bind.pointer='/*';r[0].value={id:'1'};});
console.log(count+' synthetic identity-link controls passed. Assumes original shape/admitted surfaces; native identity, scope liveness and issuer authority remain unqualified.');
