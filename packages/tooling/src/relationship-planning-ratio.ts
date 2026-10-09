/** Candidate benchmark arithmetic only; does not admit timing/profile/native evidence. */
export function checkRelationshipPlanningRatio(baseline:readonly string[],candidate:readonly string[],resolution:string):'within_target'|'above_target'|'invalid_samples' {
 const parse=(value:string)=> typeof value==='string'&&/^(0|[1-9][0-9]*)$/.test(value)&&value.length<=30?BigInt(value):null;
 const unit=parse(resolution);
 if(unit===null||unit<=0n||baseline.length!==1000||candidate.length!==1000)return 'invalid_samples';
 const a=Array.from(baseline,parse),b=Array.from(candidate,parse);
 if(a.some(x=>x===null)||b.some(x=>x===null))return 'invalid_samples';
 const sorted=(values:(bigint|null)[]) => (values as bigint[]).sort((x,y)=>x<y?-1:x>y?1:0);
 const low=sorted(a)[949],high=sorted(b)[949];
 if(low<=unit)return 'invalid_samples';
 return high<=2n*low?'within_target':'above_target';
}
