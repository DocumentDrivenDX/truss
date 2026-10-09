/** Existing UMF DDD registration against original consumer sources. */
import {createHash} from 'node:crypto';
import {dddRegistry} from '/Users/erik/Projects/umf/src/extensions/ddd/index';
import {validateDocument} from '/Users/erik/Projects/umf/src/validation/document';
const packet=await Bun.file(import.meta.dir+'/../../../03-test/consumer-explicit-names.proposal.json').json();
const observations=[];
for(const row of packet.sources){
 const bytes=new Uint8Array(await Bun.file(row.sourcePath).arrayBuffer());
 if(createHash('sha256').update(bytes).digest('hex')!==row.sourceSha256)throw Error('Original consumer bytes changed');
 const source=JSON.parse(new TextDecoder('utf8',{fatal:true}).decode(bytes));
 const validation=validateDocument(source,dddRegistry());
 if(!validation.valid||validation.complete||validation.diagnostics.some(d=>d.code==='UNKNOWN_EXTENSION'&&d.path==='/vocabularies/umf.ddd'))throw Error('DDD registration correspondence');
 for(const [code,path] of [['UNKNOWN_EXTENSION','/vocabularies/hohfeld.placement'],['UNKNOWN_CORE_FIELD','/modules/0/actions']])if(!validation.diagnostics.some(d=>d.code===code&&d.path===path))throw Error('Uninterpreted content disappeared');
 const changed=structuredClone(source);
 changed.modules[0].elements[0].extensions['umf.ddd'].identity.fields=['missing'];
 const negative=validateDocument(changed,dddRegistry());
 if(negative.valid||!negative.diagnostics.some(d=>d.code==='DDD_IDENTITY'&&d.severity==='error'))throw Error('Malformed DDD identity not refused');
 observations.push({sourcePath:row.sourcePath,sourceSha256:row.sourceSha256,validation,invalidIdentityRefused:true});
}
const sources=[];for(const path of ['/Users/erik/Projects/umf/src/extensions/ddd/index.ts','/Users/erik/Projects/umf/spec/extensions/ddd/package.json','/Users/erik/Projects/umf/src/registry/registry.ts'])sources.push({path,sha256:createHash('sha256').update(new Uint8Array(await Bun.file(path).arrayBuffer())).digest('hex')});
await Bun.write(import.meta.dir+'/consumer-ddd-registry.json',JSON.stringify({scope:'actual existing UMF DDD registry on original consumer models; no complete semantics/compiler/native adoption',sources,observations,nativeImplementationQualified:false},null,2)+'\n');
console.log('Both original models pass registered DDD validation; malformed identities refuse; remaining unknown content retained');
