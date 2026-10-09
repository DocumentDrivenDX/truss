/** Synthetic admitted binding/scope projections only; no native issuer or transport authority. */
type Binding={namespace:string;identity:string;state:'pending'|'committed'|'rolled_back'|'unknown';scope:string;generation:string;visible:boolean;boundAt:{kind:'setup'}|{kind:'result';stepIndex:string}};
type Slot={pointer:string;namespace:string};
type Scope={identity:string;generation:string;live:boolean};
function substitute(input:any,slots:Slot[],bindings:ReadonlyMap<string,Binding>,stepIndex:string,scope:Scope):any|null{
 if(!/^(0|[1-9][0-9]*)$/.test(stepIndex)||!scope.live)return null;
 const copy=structuredClone(input),seen=new Set<string>();
 for(const slot of slots){
  if(seen.has(slot.pointer)||!/^\/(?:[^~\/]|~[01])*(?:\/(?:[^~\/]|~[01])*)*$/.test(slot.pointer))return null;seen.add(slot.pointer);
  const parts=slot.pointer.slice(1).split('/').map(x=>x.replace(/~1/g,'/').replace(/~0/g,'~'));
  let parent=copy;
  for(let i=0;i<parts.length;i++){
   const key=parts[i];
   if(parent===null||typeof parent!=='object'||!Object.hasOwn(parent,key))return null;
   if(Array.isArray(parent)&&(!/^(0|[1-9][0-9]*)$/.test(key)||BigInt(key)>=BigInt(parent.length)))return null;
   if(i!==parts.length-1){parent=parent[key];continue;}
   const value=parent[key];
   if(typeof value==='string')continue; // Exact public literal; no string replacement.
   if(value===null||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==1||!Object.hasOwn(value,'identityAlias')||typeof value.identityAlias!=='string')return null;
   const binding=bindings.get(value.identityAlias);
   if(!binding||binding.namespace!==slot.namespace||!binding.visible||!['pending','committed'].includes(binding.state))return null;
   if(binding.boundAt.kind==='result'&&(!/^(0|[1-9][0-9]*)$/.test(binding.boundAt.stepIndex)||BigInt(binding.boundAt.stepIndex)>=BigInt(stepIndex)))return null;
   if(binding.state==='pending'&&(binding.scope!==scope.identity||binding.generation!==scope.generation))return null;
   parent[key]=binding.identity;
  }
 }
 return copy;
}
const input={selection:{id:{identityAlias:'$a'}},properties:{text:'$a',json:{identityAlias:'$a'}}};
const slots:Slot[]=[{pointer:'/selection/id',namespace:'objects'}];
const binding:Binding={namespace:'objects',identity:'9007199254740993',state:'pending',scope:'original',generation:'1',visible:true,boundAt:{kind:'result',stepIndex:'0'}};
const scope:Scope={identity:'original',generation:'1',live:true};
let count=0;
function witness(name:string,wanted:boolean,change:(i:any,s:Slot[],b:Binding,c:Scope)=>void){const i=structuredClone(input),s=structuredClone(slots),b=structuredClone(binding),c=structuredClone(scope);change(i,s,b,c);const original=JSON.stringify(i);const result=substitute(i,s,new Map([['$a',b]]),'1',c);if((result!==null)!==wanted||JSON.stringify(i)!==original)throw Error(name);if(result&&JSON.stringify(result.properties)!==JSON.stringify(i.properties))throw Error(name+' literal property changed');count++;}
witness('original live pending binding',true,()=>{});
witness('literal ID is not alias substitution',true,i=>i.selection.id='$a');
witness('unknown alias',false,i=>i.selection.id={identityAlias:'$missing'});
witness('reference is closed',false,i=>i.selection.id={identityAlias:'$a',authority:'caller'});
witness('wrong namespace',false,(_i,_s,b)=>b.namespace='edges');
witness('forward reference',false,(_i,_s,b)=>b.boundAt={kind:'result',stepIndex:'1'});
witness('later reference',false,(_i,_s,b)=>b.boundAt={kind:'result',stepIndex:'2'});
witness('rolled back allocation',false,(_i,_s,b)=>b.state='rolled_back');
witness('unknown transaction outcome',false,(_i,_s,b)=>b.state='unknown');
witness('different pending scope',false,(_i,_s,_b,c)=>c.identity='other');
witness('reused label with new generation',false,(_i,_s,_b,c)=>c.generation='2');
witness('ended invocation scope',false,(_i,_s,_b,c)=>c.live=false);
witness('committed visibility can cross scopes',true,(_i,_s,b,c)=>{b.state='committed';c.identity='other';});
witness('committed but not visible',false,(_i,_s,b)=>{b.state='committed';b.visible=false;});
witness('duplicate slot',false,(_i,s)=>s.push({...s[0]}));
witness('missing registered member',false,i=>delete i.selection.id);
const result=substitute(input,slots,new Map([['$a',binding]]),'1',scope);
if(result?.selection.id!==binding.identity||input.selection.id.identityAlias!=='$a')throw Error('Exact identity substitution or original custody');count++;
console.log(count+' synthetic slot-substitution controls passed. Native namespace/visibility, original issuer/scope admission and complete public-wire validation remain unqualified.');
