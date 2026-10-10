/** Synthetic controls of the private C5 helper; no native qualification. */
import {substituteAdmittedConformanceAliases as substitute,
 type ConformanceAliasBinding as Binding,type ConformanceIdentitySlot as Slot,
 type ConformanceInvocationScope as Scope} from '../../../../../packages/tooling/src/conformance-alias-substitution';
const input={selection:{id:{identityAlias:'$a'}},properties:{text:'$a',json:{identityAlias:'$a'}}};
const slots:Slot[]=[{pointer:'/selection/id',namespace:'objects'}];
const binding:Binding={namespace:'objects',identity:'9007199254740993',state:'pending',scope:'original',generation:'1',visible:true,boundAt:{kind:'result',stepIndex:'0'}};
const scope:Scope={identity:'original',generation:'1',live:true};
let count=0;
function witness(name:string,wanted:boolean,change:(i:any,s:Slot[],b:Binding,c:Scope)=>void){const i=structuredClone(input),s=structuredClone(slots),b=structuredClone(binding),c=structuredClone(scope);change(i,s,b,c);const original=JSON.stringify(i);const result=substitute(i,s,new Map([['$a',b]]),'1',c) as any;if((result!==null)!==wanted||JSON.stringify(i)!==original)throw Error(name);if(result&&JSON.stringify(result.properties)!==JSON.stringify(i.properties))throw Error(name+' literal property changed');count++;}
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
const result=substitute(input,slots,new Map([['$a',binding]]),'1',scope) as any;
if(result?.selection.id!==binding.identity||input.selection.id.identityAlias!=='$a')throw Error('Exact identity substitution or original custody');count++;
console.log(count+' synthetic slot-substitution controls passed. Native namespace/visibility, original issuer/scope admission and complete public-wire validation remain unqualified.');
