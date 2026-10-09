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
console.log(JSON.stringify({shapeValid:true,...expected,boundaryArithmeticVerified:true,scope:'Planning fixture shape, exact artifact bytes/hash and independent canonical sizing only; no UMF semantic admission or native execution'}));
