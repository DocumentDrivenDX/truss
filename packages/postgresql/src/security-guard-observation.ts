/** Local candidate decoding only; no native exclusion, original issuer, caller,
 * current-authority, completion or lease authenticity is established here. */
export interface CandidateGuardObservation {readonly singleton:'1';readonly installationIdentityHex:string;readonly policyProfileHex:string;readonly generation:string}
const names=['singleton','installation_identity_bytes_hex','policy_profile_bytes_hex','generation'] as const;
const fail=():never=>{throw Error('TRUSS_SECURITY_GUARD_OBSERVATION_UNSUPPORTED');};
function data(value:unknown,keys:readonly string[]):Record<string,unknown>{
 if(!value||typeof value!=='object'||Array.isArray(value)||![Object.prototype,null].includes(Object.getPrototypeOf(value)))return fail();
 const ds=Object.getOwnPropertyDescriptors(value);if(Reflect.ownKeys(ds).length!==keys.length)return fail();
 return Object.fromEntries(keys.map(key=>{const d=ds[key];if(!d||!Object.hasOwn(d,'value')||!d.enumerable)return fail();return [key,d.value];}));
}
function array(value:unknown,length:number):unknown[]{
 if(!Array.isArray(value)||Object.getPrototypeOf(value)!==Array.prototype)return fail();const ds=Object.getOwnPropertyDescriptors(value) as Record<string,PropertyDescriptor>;
 if(ds.length?.value!==length||Reflect.ownKeys(ds).length!==length+1)return fail();
 return Array.from({length},(_,i)=>{const d=ds[String(i)];if(!d||!Object.hasOwn(d,'value')||!d.enumerable)return fail();return d.value;});
}
function hex(value:unknown):string{if(typeof value!=='string'||!value.length||value.length>65536||value.length%2||/[^0-9a-f]/.test(value))return fail();return value;}
/** TEXT OID25 descriptors and one four-cell row from the original acquisition
 * SELECT. Expected carriers are host-supplied assertions, not trusted issuers.
 * Local bounds: 32KiB each identity/profile; no native bigint Number conversion. */
export function decodeCandidateAuthorityGuard(input:unknown):Readonly<CandidateGuardObservation>{
 const p=data(input,['columns','rows','expected']),expected=data(p.expected,['installationIdentityHex','policyProfileHex']);
 const installationIdentityHex=hex(expected.installationIdentityHex),policyProfileHex=hex(expected.policyProfileHex);
 const columns=array(p.columns,4);for(let i=0;i<4;i++){const d=data(columns[i],['name','typeOid']);if(d.name!==names[i]||d.typeOid!=='25')return fail();}
 const cells=array(array(p.rows,1)[0],4);
 if(cells[0]!=='1'||hex(cells[1])!==installationIdentityHex||hex(cells[2])!==policyProfileHex)return fail();
 const generation=cells[3];if(typeof generation!=='string'||generation.length>19||!/^[1-9][0-9]*$/.test(generation)||BigInt(generation)>9223372036854775807n)return fail();
 return Object.freeze({singleton:'1',installationIdentityHex,policyProfileHex,generation});
}
