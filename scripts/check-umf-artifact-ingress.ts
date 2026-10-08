/** Original Ashlar UMF bytes through public Truss integrity ingress, not catalog acceptance. */
import {verifyExactArtifacts} from '@documentdrivendx/truss-postgresql';
import {readFile,writeFile} from 'node:fs/promises';
const root=process.argv[2];if(!root)throw Error('Ashlar example directory required');
const files=['schema-v1.umf.json','schema-v2.umf.json','schema-v3.umf.json','schema-unknown.umf.json'];
const originals=await Promise.all(files.map(async identity=>{const bytes=await readFile(root+'/'+identity);return {identity,bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')};}));
const verified=await verifyExactArtifacts(originals,{maxArtifacts:4,maxSingleBytes:65536,maxTotalBytes:262144});
if(JSON.stringify(verified)!==JSON.stringify(originals))throw Error('Original UMF bytes changed');
await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/umf-artifact-ingress.json',import.meta.url),JSON.stringify({loader:'bun/'+Bun.version,artifacts:verified.map(artifact=>({identity:artifact.identity,sha256:artifact.sha256,bytes:Buffer.from(artifact.bytesBase64,'base64').length})),qualification:'Actual original Ashlar v1/v2/v3/unknown UMF fixture bytes through built public Truss exact-artifact verifier, Web Crypto SHA-256 compared with Bun CryptoHasher. No JSON parsing, unknown semantic loss, database submission, native catalog acceptance, accepted IDs or full required-check validity/completeness claim.'},null,2)+'\n');
console.log('Four original UMF example artifacts verified without conversion or semantic interpretation.');
