/** Pure candidate path planning. Metadata is not installed state or execution authority. */
import {decodeAcceptanceJson} from '../../postgresql/src/acceptance-json';

export interface LayoutPin {
 readonly version:string;
 readonly bundleSha256:string;
 readonly inventorySha256:string;
}
export interface MigrationStep {
 readonly id:string;
 readonly from:string;
 readonly to:string;
 readonly recipe:Readonly<{identity:string;sha256:string}>;
 readonly procedure:Readonly<{identity:string;version:string;sha256:string}>;
 readonly transactional:boolean;
}
export type MigrationPlanResult = {
 readonly outcome:'plan';readonly scope:'declared_metadata_only';readonly family:string;
 readonly source:Readonly<LayoutPin>;readonly target:Readonly<LayoutPin>;
 readonly route:string;readonly direction:'upgrade'|'downgrade';readonly steps:readonly Readonly<MigrationStep>[];
} | {
 readonly outcome:'no_steps';readonly scope:'declared_metadata_only';readonly family:string;
 readonly source:Readonly<LayoutPin>;readonly target:Readonly<LayoutPin>;
} | {
 readonly outcome:'refused';readonly scope:'declared_metadata_only';
 readonly reason:'invalid_input'|'family'|'source_pin'|'target'|'route'|'nontransactional_profile';
};
const fail=():never=>{throw Error('Invalid migration metadata')};
function object(value:unknown,keys:readonly string[]):Record<string,unknown>{
 if(!value||typeof value!=='object'||Array.isArray(value))return fail();
 const actual=Object.keys(value);if(actual.length!==keys.length||actual.some(k=>!keys.includes(k)))return fail();
 return value as Record<string,unknown>;
}
function text(value:unknown):string{
 if(typeof value!=='string'||!value||new TextEncoder().encode(value).length>256||value.includes('\0'))return fail();
 return value;
}
function sha(value:unknown):string{if(typeof value!=='string'||!(/^[a-f0-9]{64}$/).test(value))return fail();return value;}
function version(value:unknown):string{
 const s=text(value);if(!(/^(0|[1-9][0-9]{0,19})\.(0|[1-9][0-9]{0,19})\.(0|[1-9][0-9]{0,19})$/).test(s))return fail();return s;
}
function compare(a:string,b:string):number{
 const left=a.split('.').map(BigInt),right=b.split('.').map(BigInt);
 for(let i=0;i<3;i++)if(left[i]!==right[i])return left[i]!<right[i]!?-1:1;
 return 0;
}
function list(value:unknown):unknown[]{if(!Array.isArray(value)||value.length<1||value.length>1024)return fail();return value;}
function pin(value:unknown):Readonly<LayoutPin>{
 const o=object(value,['version','bundleSha256','inventorySha256']);
 return Object.freeze({version:version(o.version),bundleSha256:sha(o.bundleSha256),inventorySha256:sha(o.inventorySha256)});
}
function artifact(value:unknown){const o=object(value,['identity','sha256']);return Object.freeze({identity:text(o.identity),sha256:sha(o.sha256)});}
function profile(value:unknown){const o=object(value,['identity','version','sha256']);return Object.freeze({identity:text(o.identity),version:text(o.version),sha256:sha(o.sha256)});}
function unique<T>(values:T[],key:(value:T)=>string):Map<string,T>{
 const result=new Map<string,T>();for(const v of values){const k=key(v);if(result.has(k))return fail();result.set(k,v)}return result;
}
/** Copies/decodes closed numeric-free metadata under the existing 1-MiB wire bounds.
 * Only explicitly declared routes are selected: no guessed upgrade, SQL or IO.
 * Apply must independently admit originals, native parity, authority and settlement. */
export function planLayoutMigration(manifestBytes:Uint8Array,observationBytes:Uint8Array,targetVersion:string):MigrationPlanResult{
 const refuse=(reason:Extract<MigrationPlanResult,{outcome:'refused'}>['reason']):MigrationPlanResult=>Object.freeze({outcome:'refused',scope:'declared_metadata_only',reason});
 try{
  if(!(manifestBytes.buffer instanceof ArrayBuffer)||!(observationBytes.buffer instanceof ArrayBuffer))return refuse('invalid_input');
  const m=object(decodeAcceptanceJson(manifestBytes),['interfaceVersion','family','layouts','steps','routes']);
  if(m.interfaceVersion!=='truss-layout-migrations/0.1.0')return refuse('invalid_input');
  const family=text(m.family),layouts=unique(list(m.layouts).map(pin),p=>p.version);
  if(!Array.isArray(m.steps)||m.steps.length>1024||!Array.isArray(m.routes)||m.routes.length>1024)return refuse('invalid_input');
  const steps=unique(m.steps.map(value=>{
   const s=object(value,['id','from','to','recipe','procedure','transactional']);
   const from=version(s.from),to=version(s.to);
   if(from===to||!layouts.has(from)||!layouts.has(to)||typeof s.transactional!=='boolean')return fail();
   return Object.freeze({id:text(s.id),from,to,recipe:artifact(s.recipe),procedure:profile(s.procedure),transactional:s.transactional});
  }),s=>s.id);
  const routes=unique(m.routes.map(value=>{
   const o=object(value,['id','from','to','direction','steps']);
   const from=version(o.from),to=version(o.to),direction=o.direction;
   if(!layouts.has(from)||!layouts.has(to)||!['upgrade','downgrade'].includes(String(direction)))return fail();
   const ids=list(o.steps).map(text);if(new Set(ids).size!==ids.length)return fail();
   let at=from;
   const ordered=ids.map(id=>{const step=steps.get(id);if(!step||step.from!==at||compare(step.from,step.to)!==(direction==='upgrade'?-1:1))return fail();at=step.to;return step});
   if(at!==to)return fail();
   return Object.freeze({id:text(o.id),from,to,direction:direction as 'upgrade'|'downgrade',steps:Object.freeze(ordered)});
  }),r=>r.from+'>'+r.to);
  unique([...routes.values()],r=>r.id);
  const o=object(decodeAcceptanceJson(observationBytes),['interfaceVersion','family','layout']);
  if(o.interfaceVersion!=='truss-layout-observation/0.1.0')return refuse('invalid_input');
  if(text(o.family)!==family)return refuse('family');
  const source=pin(o.layout),registered=layouts.get(source.version);
  if(!registered||registered.bundleSha256!==source.bundleSha256||registered.inventorySha256!==source.inventorySha256)return refuse('source_pin');
  const target=layouts.get(version(targetVersion));if(!target)return refuse('target');
  if(source.version===target.version)return Object.freeze({outcome:'no_steps',scope:'declared_metadata_only',family,source,target});
  const route=routes.get(source.version+'>'+target.version);if(!route)return refuse('route');
  if(route.steps.some(s=>!s.transactional))return refuse('nontransactional_profile');
  return Object.freeze({outcome:'plan',scope:'declared_metadata_only',family,source,target,route:route.id,direction:route.direction,steps:route.steps});
 }catch{return refuse('invalid_input')}
}
