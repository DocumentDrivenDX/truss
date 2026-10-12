/** Candidate values only. No fresh cut, native exclusion, issuer, completion or lease proof. */
export type CandidateClaimObservation = Readonly<{state:'not-observed'} | {state:'observed';operationIdentityHex:string;installationIdentityHex:string;policyProfileHex:string;generation:string;settled:boolean}>;
const fail=():never=>{throw Error('TRUSS_SECURITY_CLAIM_OBSERVATION_UNSUPPORTED');};
const names=['operation_identity_bytes_hex','installation_identity_bytes_hex','policy_profile_bytes_hex','generation','settled'] as const;
function data(value:unknown,keys:readonly string[]):Record<string,unknown>{
 if(!value||typeof value!=='object'||Array.isArray(value)||![Object.prototype,null].includes(Object.getPrototypeOf(value)))return fail();
 if(Reflect.ownKeys(value).length!==keys.length)return fail();
 return Object.fromEntries(keys.map(key=>{const d=Object.getOwnPropertyDescriptor(value,key);if(!d||!Object.hasOwn(d,'value')||!d.enumerable)return fail();return [key,d.value];}));
}
function array(value:unknown,length:number):unknown[]{
 if(!Array.isArray(value)||Object.getPrototypeOf(value)!==Array.prototype)return fail();const size=Object.getOwnPropertyDescriptor(value,'length');
 if(size?.value!==length||Reflect.ownKeys(value).length!==length+1)return fail();
 return Array.from({length},(_,i)=>{const d=Object.getOwnPropertyDescriptor(value,String(i));if(!d||!Object.hasOwn(d,'value')||!d.enumerable)return fail();return d.value;});
}
function hex(value:unknown):string{if(typeof value!=='string'||!value.length||value.length>65536||value.length%2||/[^0-9a-f]/.test(value))return fail();return value;}

function generation(value:unknown):string{if(typeof value!=='string'||value.length>19||!/^[1-9][0-9]*$/.test(value)||BigInt(value)>9223372036854775807n)return fail();return value;}
/** Original five TEXT/OID25 descriptors, zero or one row. Absence means only
 * not observed, never known abort/noncommit. Expected bytes are assertions.
 * Bounds: operation2KiB, installation/profile32KiB each. */
export function decodeCandidatePublicationClaim(input:unknown):CandidateClaimObservation{
 const p=data(input,['columns','rows','expected']),e=data(p.expected,['operationIdentityHex','installationIdentityHex','policyProfileHex','generation']);
 const operationIdentityHex=hex(e.operationIdentityHex);if(operationIdentityHex.length>4096)return fail();
 const installationIdentityHex=hex(e.installationIdentityHex),policyProfileHex=hex(e.policyProfileHex),originalGeneration=generation(e.generation);
 const columns=array(p.columns,5);for(let i=0;i<5;i++){const d=data(columns[i],['name','typeOid']);if(d.name!==names[i]||d.typeOid!=='25')return fail();}
 if(!Array.isArray(p.rows))return fail();const size=Object.getOwnPropertyDescriptor(p.rows,'length')?.value;if(size!==0&&size!==1)return fail();const rows=array(p.rows,size);
 if(rows.length===0)return Object.freeze({state:'not-observed'});
 const cells=array(rows[0],5);if(hex(cells[0])!==operationIdentityHex||hex(cells[1])!==installationIdentityHex||hex(cells[2])!==policyProfileHex||generation(cells[3])!==originalGeneration||!['true','false'].includes(cells[4] as string))return fail();
 return Object.freeze({state:'observed',operationIdentityHex,installationIdentityHex,policyProfileHex,generation:originalGeneration,settled:cells[4]==='true'});
}
