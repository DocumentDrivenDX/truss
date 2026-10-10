/** Decode complete context0.3 bytes only; native collector authority is separate. */
import {decodeAcceptanceJson} from './acceptance-json';
import {mapAssertedOrigin} from './asserted-origin-map';
const fields=['interfaceVersion','xid','ordinal','sessionUser','actingUser','database','backendPid','actorRoleOid','sessionRoleOid','assertedOriginUtf8Hex','assertedOriginCaptureProfileHex'].sort();
const fromHex=(hex:string,max:number)=>{
 if(!/^(?:[0-9a-f]{2})+$/.test(hex)||hex.length>max*2)throw Error('Original bounded capture hexadecimal bytes required');
 const bytes=new Uint8Array(hex.length/2);for(let i=0;i<bytes.length;i++)bytes[i]=parseInt(hex.slice(i*2,i*2+2),16);return bytes;
};
export function decodeCapturedOriginContext(originalContext:Uint8Array,version:'0.3'|'0.4'='0.3'){
 const expectedFields=version==='0.3'?fields:[...fields,'installationId','sourceEpoch','targetIncarnation','sourceEpochProfileHex','sourceEpochEvidenceHex'].sort();
 if(!(originalContext.buffer instanceof ArrayBuffer)||originalContext.length>1048576)throw Error('Original bounded context bytes required');
 const owned=Uint8Array.prototype.slice.call(originalContext) as Uint8Array;
 const context=decodeAcceptanceJson(owned);
 if(context===null||Array.isArray(context)||typeof context!=='object'||JSON.stringify(Object.keys(context).sort())!==JSON.stringify(expectedFields)||Object.values(context).some(v=>typeof v!=='string')||context.interfaceVersion!=='truss-native-operation-context/'+version)throw Error('Complete original context'+version+' capture required');
 const c=context as Record<string,string>;
 if(!/^[1-9][0-9]{0,19}$/.test(c.xid)||!/^(0|[1-9][0-9]{0,18})$/.test(c.ordinal)||BigInt(c.xid)>18446744073709551615n||BigInt(c.ordinal)>9223372036854775807n)throw Error('Original native context identity grammar required');
 for(const key of ['actorRoleOid','sessionRoleOid'])if(!/^[1-9][0-9]{0,9}$/.test(c[key])||BigInt(c[key])>4294967295n)throw Error('Original role OID grammar required');
 if(!c.sessionUser||!c.database||!/^[1-9][0-9]{0,9}$/.test(c.backendPid))throw Error('Original native actor context fields required');
 const asserted=fromHex(c.assertedOriginUtf8Hex,131072),profile=fromHex(c.assertedOriginCaptureProfileHex,65536);
 let epoch:Readonly<{installationId:string;sourceEpoch:string;targetIncarnation:string;profileHex:string;evidenceHex:string}>|undefined;
 if(version==='0.4'){
  for(const [key,max] of [['installationId',1024],['sourceEpoch',256],['targetIncarnation',1024]] as const)if(!c[key]||c[key].includes('\0')||new TextEncoder().encode(c[key]).length>max)throw Error('Original epoch identity text required');
  fromHex(c.sourceEpochProfileHex,65536);fromHex(c.sourceEpochEvidenceHex,1048576);
  epoch=Object.freeze({installationId:c.installationId,sourceEpoch:c.sourceEpoch,targetIncarnation:c.targetIncarnation,profileHex:c.sourceEpochProfileHex,evidenceHex:c.sourceEpochEvidenceHex});
 }
 const mapped=mapAssertedOrigin(asserted,c.actingUser);
 return Object.freeze({epoch,origin:mapped.origin,journalOrigin:mapped.journalOrigin,assertedUtf8Hex:c.assertedOriginUtf8Hex,captureProfileHex:c.assertedOriginCaptureProfileHex,originalContextUtf8Hex:Array.from(owned,b=>b.toString(16).padStart(2,'0')).join(''),captureProfileByteCount:String(profile.length),scope:version==='0.3'?'original_context3_wire_decode_and_origin_mapping_only' as const:'original_context4_wire_decode_and_origin_mapping_only' as const});
}
