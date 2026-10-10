/** Selected dependency behavior only; no Truss resource/heap/native qualification. */
import {copyJson} from '/Users/erik/Projects/umf/src/model/json';
const owner='/Users/erik/Projects/umf/src/model/json.ts';
const hash=async()=>new Bun.CryptoHasher('sha256').update(await Bun.file(owner).arrayBuffer()).digest('hex');
const before=await hash();
const cases:{id:string;expected:string;observed:string}[]=[];
function check(id:string,input:unknown,expected:string){
 let observed='accepted';
 try{const output=copyJson(input);if(typeof input==='string'&&output!==input)throw Error('text changed');}catch(e){observed=(e as {code?:string}).code??'unknown_error';}
 if(observed!==expected)throw Error(`${id}: expected ${expected}, got ${observed}`);
 cases.push({id,expected,observed});
}
check('100000_values_including_array_root',Array(99999).fill(null),'accepted');
check('100001_values_including_array_root',Array(100000).fill(null),'LIMIT');
function nested(depth:number){let result:unknown=null;for(let i=0;i<depth;i++)result=[result];return result;}
check('depth_128',nested(128),'accepted');
check('depth_129',nested(129),'LIMIT');
let getterCalls=0;const accessor={};Object.defineProperty(accessor,'value',{enumerable:true,get(){getterCalls++;return null;}});
check('getter_refused_without_execution',accessor,'NON_JSON');
if(getterCalls!==0)throw Error('getter executed');
check('custom_prototype_refused',Object.create({inherited:true}),'NON_JSON');
check('unsafe_numeric_identity_refused',9007199254740992,'NUMBER');
check('exact_numeric_identity_text_retained','9007199254740993','accepted');
if(await hash()!==before)throw Error('original source changed during check');
const receipt={scope:'Observed selected UMF copyJson boundary/input behavior only; not selector full-receipt feasibility, Truss admission, heap/preallocation accounting or native support',bunVersion:Bun.version,source:{path:owner,sha256:before},cases,getterCalls,trussExecutionQualified:false,nativeExecution:false};
await Bun.write('docs/helix/04-build/evidence/design-audit/umf-copy-boundaries.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({cases:cases.length,getterCalls,trussExecutionQualified:false}));
