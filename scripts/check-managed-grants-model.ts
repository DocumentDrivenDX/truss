// SPDX-License-Identifier: MIT OR Apache-2.0
/** Current UMF import/export correspondence for the managed-grants source fragment. */
import { mkdir } from 'node:fs/promises';
import { dirname } from 'node:path';
const root=process.env.UMF_NATIVE_ROOT;
if(!root)throw Error('Set UMF_NATIVE_ROOT to the qualified UMF source checkout');
const {backend}=await import(root+'/native/postgresql/runtime.ts');
const owner=await import(root+'/src/adapters/postgresql/index.ts');
const sourcePath='packages/python/src/truss/_catalog_runtime/managed-grants.sql';
const modelPath='docs/helix/02-design/models/truss-managed-grants-0.1.umf.json';
const evidencePath='docs/helix/04-build/evidence/design-audit/managed-grants-20261022/managed-grants-model.json';
await mkdir(dirname(evidencePath),{recursive:true});
const source=await Bun.file(sourcePath).text();
let model:any;
if(process.argv.includes('--capture')){
 if(await Bun.file(modelPath).exists())throw Error('Existing model must be updated in place');
 model=await owner.importPostgresqlSql(source,backend,{id:'truss-managed-grants-storage-0.1'});
 await Bun.write(modelPath,JSON.stringify(model)+'\n');
}else model=JSON.parse(await Bun.file(modelPath).text());
// Export the persisted bytes, not the importer’s in-memory return value.
model=JSON.parse(await Bun.file(modelPath).text());
if(model.umf!=='0.10.0')throw Error('Exact UMF0.10 model required');
const exported=await owner.exportPostgresqlSql(model,backend);
function normalized(value:any):any{
 if(Array.isArray(value))return value.map(normalized);
 if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().filter(k=>!['location','stmt_location','stmt_len'].includes(k)).map(k=>[k,normalized(value[k])]));
 return value;
}
const before=await backend.parse(source),after=await backend.parse(exported);
if(JSON.stringify(normalized(before))!==JSON.stringify(normalized(after)))throw Error('Managed-grants UMF native AST correspondence failed');
const hash=(raw:string|Uint8Array)=>new Bun.CryptoHasher('sha256').update(raw).digest('hex');
const modelBytes=new Uint8Array(await Bun.file(modelPath).arrayBuffer());
const receipt={scope:'Current managed-grants SQL fragment imported and reloaded/exported through UMF 0.10; source and exported PostgreSQL native ASTs match after source-location removal. Native installation/migration qualification is separate.',
 backend:backend.identity,sourcePath,sourceSha256:hash(source),ownerExportSha256:hash(exported),modelPath,modelSha256:hash(modelBytes),
 ownerFiles:Object.fromEntries(await Promise.all(
  ['src/adapters/postgresql/index.ts','native/postgresql/runtime.ts','spec/extensions/postgresql/native-ast.schema.json','bun.lock']
   .map(async p=>[p,hash(new Uint8Array(await Bun.file(root+'/'+p).arrayBuffer()))]))),
 passed:true};
await Bun.write(evidencePath,JSON.stringify(receipt,null,2)+'\n');
await Bun.write('docs/helix/04-build/evidence/design-audit/managed-grants-20261022/managed-grants.owner-export.sql',exported);
console.log(JSON.stringify(receipt));
