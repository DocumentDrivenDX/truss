// SPDX-License-Identifier: MIT OR Apache-2.0
/** Package an isolated committed UMF key producer without changing preparation. */
import {mkdir,readFile,writeFile,copyFile,readdir} from 'node:fs/promises';
const repository=process.argv[2];if(!repository)throw Error('UMF repository required');
const current=process.argv[3]==='core08';
const build=Bun.spawnSync([process.execPath,'scripts/build-umf-runtime.ts',repository,current?'key-tuples-current':'key-tuples']);
if(build.exitCode!==0)throw Error('Original UMF key producer build failed');
const source=Buffer.from(build.stdout).toString().trim();
const root=current?'packages/python/src/truss/_umf_keys08':'packages/python/src/truss/_umf_keys';
await mkdir(root+'/licenses',{recursive:true});
await copyFile(source+'/producer.js',root+'/producer.js');
await copyFile(source+'/producer-manifest.json',root+'/producer-manifest.json');
await copyFile('packages/umf-bun/src/python-keys.mjs',root+'/bridge.mjs');
const notices=await readdir('packages/python/src/truss/_umf/licenses');
for(const name of notices)await copyFile('packages/python/src/truss/_umf/licenses/'+name,root+'/licenses/'+name);
const hash=(raw:Uint8Array)=>new Bun.CryptoHasher('sha256').update(raw).digest('hex');
const paths=['producer.js','producer-manifest.json','bridge.mjs',...notices.map(name=>'licenses/'+name)];
const manifest={interfaceVersion:'truss-python-umf-key-producer/0.1',runtime:'Bun',runtimeVersion:Bun.version,
 owner:JSON.parse(await readFile(root+'/producer-manifest.json','utf8')),
 files:Object.fromEntries(await Promise.all(paths.map(async name=>[name,hash(await readFile(root+'/'+name))])))};
await writeFile(root+'/manifest.json',JSON.stringify(manifest,null,2)+'\n');
await writeFile(current?'packages/python/src/truss/_umf_keys08_release.py':'packages/python/src/truss/_umf_keys_release.py',
 '"""Generated original UMF key producer pin; no database authority."""\nMANIFEST_SHA256 = '+JSON.stringify(hash(await readFile(root+'/manifest.json')))+'\n');
console.log(JSON.stringify({root,revision:manifest.owner.revision,manifestSha256:hash(await readFile(root+'/manifest.json'))}));
