/** Independent WebCrypto byte mapping, not native advisory-lock qualification. */
const fixture=await Bun.file('docs/helix/02-design/contracts/bindings/truss-bootstrap-namespace-lock-v0.1.vectors.json').json();
const encoder=new TextEncoder(), failures:string[]=[];
const hex=(a:Uint8Array)=>Array.from(a,x=>x.toString(16).padStart(2,'0')).join('');
for(const v of fixture.vectors){
 const d=encoder.encode(v.databaseIdentity),s=encoder.encode(v.schemaName),prefix=encoder.encode(fixture.profile+'\0');
 const bytes=new Uint8Array(prefix.length+8+d.length+s.length);bytes.set(prefix);
 const view=new DataView(bytes.buffer);let at=prefix.length;view.setUint32(at,d.length,false);at+=4;bytes.set(d,at);at+=d.length;view.setUint32(at,s.length,false);at+=4;bytes.set(s,at);
 const digest=new Uint8Array(await crypto.subtle.digest('SHA-256',bytes));
 const key=new DataView(digest.buffer).getBigInt64(0,false).toString();
 if(hex(bytes)!==v.preimageHex||hex(digest)!==v.sha256||key!==v.signedLockKey)failures.push(v.schemaName);
}
const receipt={scope:'Four independent WebCrypto/BigInt byte mappings; no native locking/current namespace/identity qualification',cases:fixture.vectors.length,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/bootstrap-namespace-lock.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
