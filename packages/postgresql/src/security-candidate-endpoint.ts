/** Draft endpoint/column correspondence only. Caller mappings are not native
 * inventory, complete fact custody, source authentication or authorization. */
type Ref={documentId:string;moduleId:string;elementId:string};
type Association=Ref|{documentId:string;moduleId:string;relationshipId:string};
export interface CandidateEndpointColumns {
 association:Association;role:string;target:Ref;keyId:string;
 /** Ordered original target Key fields, supplied by the compiler dependency boundary. */
 targetKeyFields:readonly Ref[];
 carrier:{members:{fields:readonly Ref[]}}|{incidence:{side:'source'|'target'}};
 columns:readonly string[];
}
export interface BoundCandidateEndpoint {
 readonly binding:{readonly variable:number};
 readonly association:Association;readonly role:string;readonly target:Ref;
 readonly keyId:string;readonly targetKeyFields:readonly Ref[];
 readonly carrier:CandidateEndpointColumns['carrier'];readonly columns:readonly string[];
}
const fail=():never=>{throw Error('TRUSS_SECURITY_CANDIDATE_ENDPOINT_UNSUPPORTED');};
function object(v:unknown,names:readonly string[]):Record<string,unknown>{
 if(!v||typeof v!=='object'||Array.isArray(v)||![Object.prototype,null].includes(Object.getPrototypeOf(v)))return fail();
 const d=Object.getOwnPropertyDescriptors(v);
 if(Reflect.ownKeys(d).length!==names.length||names.some(n=>!Object.hasOwn(d,n)||!Object.hasOwn(d[n]!,'value')||!d[n]!.enumerable))return fail();
 return Object.fromEntries(names.map(n=>[n,d[n]!.value]));
}
function text(v:unknown):string{
 if(typeof v!=='string'||!v||v.length>8192)return fail();let count=0;
 for(const c of v){const cp=c.codePointAt(0)!;if(++count>4096||cp===0||(cp>=0xd800&&cp<=0xdfff))return fail();}
 return v;
}
function reference(v:unknown,relationship=false):Ref|Association{
 const names=['documentId','moduleId',relationship?'relationshipId':'elementId'];const r=object(v,names);
 return Object.fromEntries(names.map(n=>[n,text(r[n])])) as Ref|Association;
}
function association(v:unknown):Association{
 if(!v||typeof v!=='object')return fail();return reference(v,Object.hasOwn(v,'relationshipId'));
}
function array(v:unknown):unknown[]{
 if(!Array.isArray(v)||Object.getPrototypeOf(v)!==Array.prototype)return fail();const length=Object.getOwnPropertyDescriptor(v,'length')?.value;
 if(!Number.isSafeInteger(length)||length<1||length>256||Reflect.ownKeys(v).length!==length+1)return fail();
 return Array.from({length},(_,i)=>{const d=Object.getOwnPropertyDescriptor(v,String(i));if(!d||!Object.hasOwn(d,'value')||!d.enumerable)return fail();return d.value;});
}
function same(a:unknown,b:unknown):boolean{return JSON.stringify(a)===JSON.stringify(b);}
function refs(v:unknown):Ref[]{const r=array(v).map(x=>reference(x) as Ref);if(new Set(r.map(x=>JSON.stringify(x))).size!==r.length)return fail();return r;}
function carrier(v:unknown,graph:boolean):CandidateEndpointColumns['carrier']{
 if(graph){const r=object(object(v,['incidence']).incidence,['side']);if(!['source','target'].includes(r.side as string))return fail();return {incidence:{side:r.side as 'source'|'target'}};}
 return {members:{fields:refs(object(object(v,['members']).members,['fields']).fields)}};
}
function column(v:unknown):string{const s=text(v);if(new TextEncoder().encode(s).length>63)return fail();return s;}
function freeze<T>(v:T):T{if(v&&typeof v==='object'){for(const x of Object.values(v))freeze(x);Object.freeze(v);}return v;}
/** Match one actual emitted endpoint term to an explicit host projection.
 * The caller must independently bind targetKeyFields to the original selected
 * Key, columns to native domains and inventory, and graph tuples to exact codecs.
 * No Record is invented for an opaque Relationship. */
export function bindCandidateSecurityEndpoint(term:unknown,mapping:CandidateEndpointColumns):BoundCandidateEndpoint{
 const t=object(object(term,['endpoint']).endpoint,['binding','association','role','target','keyId','carrier']);
 const slot=object(t.binding,['variable']).variable;if(!Number.isSafeInteger(slot)||(slot as number)<0)return fail();
 const a=association(t.association),graph=Object.hasOwn(a,'relationshipId');
 const target=reference(t.target) as Ref,role=text(t.role),keyId=text(t.keyId),c=carrier(t.carrier,graph);
 const m=object(mapping,['association','role','target','keyId','targetKeyFields','carrier','columns']);
 const ma=association(m.association),mt=reference(m.target) as Ref,mc=carrier(m.carrier,graph),keys=refs(m.targetKeyFields),columns=array(m.columns).map(column);
 if(!same(a,ma)||!same(target,mt)||role!==text(m.role)||keyId!==text(m.keyId)||!same(c,mc)||keys.length!==columns.length||new Set(columns).size!==columns.length)return fail();
 if('members' in c&&c.members.fields.length!==keys.length)return fail();
 return freeze({binding:{variable:slot as number},association:a,role,target,keyId,targetKeyFields:keys,carrier:c,columns});
}
