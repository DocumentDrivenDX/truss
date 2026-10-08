/** Build an isolated owner producer from committed source, never sibling working edits. */
import {mkdtemp,writeFile,readFile,symlink} from 'node:fs/promises';
const repository=process.argv[2];if(!repository)throw Error('UMF Git repository required');
const revision='c45c72a2a8a3c4fba61c40c5927dd9091acf8cc3';
const output=await mkdtemp('/private/tmp/truss-umf-runtime-');
const archive=Bun.spawnSync(['git','archive',revision],{cwd:repository});if(archive.exitCode)throw Error('Pinned source archive unavailable');
await writeFile(output+'/source.tar',archive.stdout);
await symlink(repository+'/node_modules',output+'/node_modules');
const extract=Bun.spawnSync(['tar','-xf',output+'/source.tar','-C',output]);if(extract.exitCode)throw Error('Source extraction failed');
await writeFile(output+'/producer.ts',`export {readDocument} from './src/model/document';\nexport {validateDocument} from './src/validation/document';\nexport {validateCoreRecordValues} from './src/model/record-values';\nexport {upgradeSchemaPropertiesEnvelope,verifySchemaPropertiesUpgrade,rollbackSchemaPropertiesEnvelope} from './src/model/schema-properties-transition';\n`);
const build=await Bun.build({entrypoints:[output+'/producer.ts'],outdir:output,target:'browser',format:'esm',naming:'producer.js'});if(!build.success)throw Error('Owner producer build failed');
const buildDependencies=Object.fromEntries(await Promise.all(['yaml','ajv'].map(async name=>{const bytes=await readFile(repository+'/node_modules/'+name+'/package.json');return [name,{version:JSON.parse(bytes.toString()).version,packageSha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')}] as const})));
const hash=(b:Uint8Array)=>new Bun.CryptoHasher('sha256').update(b).digest('hex');
await writeFile(output+'/producer-manifest.json',JSON.stringify({revision,buildDependencies,archiveSha256:hash(archive.stdout),bundleSha256:hash(await readFile(output+'/producer.js')),operations:['readDocument','validateDocument','validateCoreRecordValues','upgradeSchemaPropertiesEnvelope','verifySchemaPropertiesUpgrade','rollbackSchemaPropertiesEnvelope'],scope:'Original logical UMF producers only; no native acceptance/containment qualification.'},null,2)+'\n');
console.log(output);
