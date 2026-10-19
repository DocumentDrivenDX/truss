// SPDX-License-Identifier: MIT OR Apache-2.0
/** Build an isolated owner producer from committed source, never sibling working edits. */
import {mkdtemp,writeFile,readFile,symlink} from 'node:fs/promises';
const repository=process.argv[2];if(!repository)throw Error('UMF Git repository required');
const mode=process.argv[3]??'core10-catalog';
if(!['core10-catalog','numeric-current'].includes(mode))throw Error('Only current core10-catalog or context-free numeric-current producers are supported');
const revision='b24e07abae445414c41d2f122deae596915c6bd5';
const coreOperations=['readJsonValue','validateSemanticTypesDocument','encodeCoreKeyTupleBody','withCatalogResourceProfile'];
const numericOperations=['exactDecimal','integerFromBigInt','integerToBigInt','admitJavascriptNumber','numericToNumberLossless'];
const operations=mode==='core10-catalog'?coreOperations:[...numericOperations,...coreOperations];
const output=await mkdtemp('/private/tmp/truss-umf-runtime-');
const archive=Bun.spawnSync(['git','archive',revision,'src','spec','package.json'],{cwd:repository});if(archive.exitCode)throw Error('Pinned source archive unavailable');
await writeFile(output+'/source.tar',archive.stdout);
await symlink(repository+'/node_modules',output+'/node_modules');
const extract=Bun.spawnSync(['tar','-xf',output+'/source.tar','-C',output]);if(extract.exitCode)throw Error('Source extraction failed');
await writeFile(output+'/producer.ts',`export {readJsonValue} from './src/model/serialization';
export {validateSemanticTypesDocument} from './src/validation/semantic-types';
export {encodeCoreKeyTupleBody} from './src/model/key-tuple';
export {withCatalogResourceProfile} from './src/model/json';
`+(mode==='numeric-current'?`export {${numericOperations.join(',')}} from './src/adapters/javascript-numeric';\n`:''));
const build=await Bun.build({entrypoints:[output+'/producer.ts'],outdir:output,target:'browser',format:'esm',naming:'producer.js'});if(!build.success)throw Error('Owner producer build failed');
// Bun includes the temporary archive directory in source comments. Normalize
// that generated-only path so identical pinned inputs have identical bytes.
const producerBytes=await readFile(output+'/producer.js','utf8');
await writeFile(output+'/producer.js',producerBytes.replace(/truss-umf-runtime-[A-Za-z0-9]+/g,'truss-umf-runtime'));
const buildDependencies=Object.fromEntries(await Promise.all(['yaml','ajv'].map(async name=>{const bytes=await readFile(repository+'/node_modules/'+name+'/package.json');return [name,{version:JSON.parse(bytes.toString()).version,packageSha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')}] as const})));
const hash=(b:Uint8Array)=>new Bun.CryptoHasher('sha256').update(b).digest('hex');
await writeFile(output+'/producer-manifest.json',JSON.stringify({revision,producerMode:mode,buildDependencies,archiveSha256:hash(archive.stdout),bundleSha256:hash(await readFile(output+'/producer.js')),operations,scope:'Original logical UMF producers only; no native acceptance/containment qualification.'},null,2)+'\n');
console.log(output);
