/** Private C5 candidate helper over already admitted, bounded JSON projections.
 * Does not establish native issuer, namespace, scope or visibility authority.
 * The original runner must validate the complete substituted public wire. */
export type ConformanceAliasBinding={namespace:string;identity:string;state:'pending'|'committed'|'rolled_back'|'unknown';scope:string;generation:string;visible:boolean;boundAt:{kind:'setup'}|{kind:'result';stepIndex:string}};
export type ConformanceIdentitySlot={pointer:string;namespace:string};
export type ConformanceInvocationScope={identity:string;generation:string;live:boolean};
export function substituteAdmittedConformanceAliases(input:unknown,slots:readonly ConformanceIdentitySlot[],bindings:ReadonlyMap<string,ConformanceAliasBinding>,stepIndex:string,scope:ConformanceInvocationScope):unknown|null{
 if(!/^(0|[1-9][0-9]*)$/.test(stepIndex)||!scope.live)return null;
 const copy=structuredClone(input),seen=new Set<string>();
 for(const slot of slots){
  if(seen.has(slot.pointer)||!/^\/(?:[^~\/]|~[01])*(?:\/(?:[^~\/]|~[01])*)*$/.test(slot.pointer))return null;seen.add(slot.pointer);
  const parts=slot.pointer.slice(1).split('/').map(x=>x.replace(/~1/g,'/').replace(/~0/g,'~'));
  let parent:any=copy;
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
