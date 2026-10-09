import {createRequire} from 'node:module';
const require=createRequire('/Users/erik/Projects/umf/package.json');
const Ajv=require('ajv/dist/2020').default;
const fixture=await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json();
const schema=await Bun.file('docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json').json();
const validate=new Ajv({strict:true}).compile(schema);if(!validate(fixture.input))throw Error(JSON.stringify(validate.errors));
function canonical(v:any):string{if(v===null||typeof v==='boolean'||typeof v==='string')return JSON.stringify(v);if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}'}
let source=0,encoded=0;function visit(v:any){if(!v||typeof v!=='object')return;if('bytesBase64'in v){const raw=Buffer.from(v.bytesBase64,'base64');if(raw.toString('base64')!==v.bytesBase64||new Bun.CryptoHasher('sha256').update(raw).digest('hex')!==v.sha256)throw Error('Artifact mismatch');source+=raw.length;encoded+=v.bytesBase64.length;}else for(const x of Object.values(v))visit(x)}visit(fixture.input);
const raw=new TextEncoder().encode(canonical(fixture.input));const prefix='truss-canonical/0.1.0\ntruss-acceptance-input/0.1.0\n';const framed=new TextEncoder().encode(prefix+canonical(fixture.input));const expected=fixture.expected;
if(raw.length!==expected.canonicalTreeBytes||framed.length!==expected.framedPreimageBytes||new Bun.CryptoHasher('sha256').update(framed).digest('hex')!==expected.framedSha256||source!==expected.artifactRawBytes||encoded!==expected.artifactBase64Bytes)throw Error('Independent capacity vector mismatch');
if(fixture.input.documents.reduce((n:number,d:any)=>n+Buffer.from(d.artifact.bytesBase64,'base64').length,0)!==expected.archivedDocumentBytes)throw Error('Archive sizing mismatch');
const bounds=fixture.boundaryExpectations;if(4*Math.ceil(bounds.sourceBytes/3)!==bounds.base64Bytes||bounds.base64Bytes<=1048576||bounds.sixIndividuallyValidArtifactBytes.some((n:number)=>n>1048576)||bounds.sixIndividuallyValidArtifactBytes.reduce((a:number,b:number)=>a+b,0)!==bounds.aggregateBytes||bounds.aggregateBytes<=bounds.aggregateLimit)throw Error('Boundary mismatch');
const controls:string[]=[];
function shapeRefusal(name:string,change:(input:any)=>void){const input=structuredClone(fixture.input);change(input);if(validate(input))throw Error('Corruption accepted: '+name);controls.push(name)}
shapeRefusal('documents-only replacement',input=>{for(const key of Object.keys(input))if(key!=='documents')delete input[key]});
shapeRefusal('converted ingress missing original source',input=>delete input.documents[1].ingress.source);
shapeRefusal('converted ingress missing loss custody',input=>delete input.documents[1].ingress.lossReport);
shapeRefusal('native ingress with fabricated conversion',input=>input.documents[0].ingress.adapterProfile=input.acceptanceProfile);
shapeRefusal('present binding without artifact',input=>delete input.binding.artifact);
shapeRefusal('hash-only document artifact',input=>delete input.documents[0].artifact.bytesBase64);
shapeRefusal('unknown effect-relevant root member',input=>input.extraPolicy='ignore');
shapeRefusal('host number in transform parameters',input=>input.transforms[0].parameters.value=1.25);
for(const [name,change] of [
 ['source digest substitution',(input:any)=>input.documents[1].ingress.source.sha256='0'.repeat(64)],
 ['noncanonical equal-byte base64 pad bits',(input:any)=>input.documents[0].artifact.bytesBase64='e31='],
] as const){const input=structuredClone(fixture.input);change(input);if(!validate(input))throw Error('Expected shape-valid integrity control: '+name);let refused=false;try{visit(input)}catch{refused=true}if(!refused)throw Error('Integrity corruption accepted: '+name);controls.push(name)}
// A changed original converted source remains part of complete semantic identity,
// even when both accepted UMF document artifacts remain byte-identical.
const changed=structuredClone(fixture.input);const alternate=Buffer.from('alternate source\n');changed.documents[1].ingress.source.bytesBase64=alternate.toString('base64');changed.documents[1].ingress.source.sha256=new Bun.CryptoHasher('sha256').update(alternate).digest('hex');
if(!validate(changed)||canonical(changed)===canonical(fixture.input)||JSON.stringify(changed.documents.map((d:any)=>d.artifact))!==JSON.stringify(fixture.input.documents.map((d:any)=>d.artifact)))throw Error('Original converted-source identity control failed');controls.push('changed conversion source changes complete input with identical accepted UMF bytes');
console.log(JSON.stringify({controls,shapeValid:true,...expected,boundaryArithmeticVerified:true,scope:'Planning fixture shape, exact artifact bytes/hash and independent canonical sizing only; no UMF semantic admission or native execution'}));
