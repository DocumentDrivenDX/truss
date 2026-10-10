/** Independent JS check against Python-specified exact wire vectors; no issuer. */
import {decodeAcceptanceJson} from '../packages/postgresql/src/acceptance-json';
const data=await Bun.file('docs/helix/04-build/evidence/receipt-position-locator-vectors.json').json();
const fields=['interfaceVersion','positionProfile','installationId','sourceEpoch','receiptStorageRowId','writerXid'];
for(const vector of data.vectors){
 const d=vector.locator;
 const ordered={interfaceVersion:d.interfaceVersion,positionProfile:{identity:d.positionProfile.identity,version:d.positionProfile.version,sha256:d.positionProfile.sha256},installationId:d.installationId,sourceEpoch:d.sourceEpoch,receiptStorageRowId:d.receiptStorageRowId,writerXid:d.writerXid};
 if(Object.keys(d).join(',')!==fields.join(','))throw Error('Incomplete original vector');
 const bytes=new TextEncoder().encode(JSON.stringify(ordered));
 const hex=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
 const token=btoa(Array.from(bytes,b=>String.fromCharCode(b)).join('')).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
 if(hex!==vector.utf8Hex||token!==vector.token)throw Error('Cross-language exact bytes differ: '+vector.id);
 const decoded=decodeAcceptanceJson(bytes);
 if(JSON.stringify(decoded)!==JSON.stringify(ordered))throw Error('Exact numeric-free decode changed vector');
 if(BigInt(d.receiptStorageRowId)<1n||BigInt(d.receiptStorageRowId)>9223372036854775807n||BigInt(d.writerXid)>18446744073709551615n)throw Error('Vector domain mismatch');
}
console.log(JSON.stringify({vectors:data.vectors.length,scope:'Python/JS exact locator serialization and existing numeric-free decode only; no token resolver, commit, authority or visibility qualification'}));
