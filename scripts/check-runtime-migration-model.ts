// SPDX-License-Identifier: MIT OR Apache-2.0
/** Native UMF authoring/DDL parity for the selected runtime migration storage. */
const root=process.env.UMF_NATIVE_ROOT;
if(!root)throw Error('Set UMF_NATIVE_ROOT to the qualified UMF source checkout');
const {backend}=await import(root+'/native/postgresql/runtime.ts');
const owner=await import(root+'/src/adapters/postgresql/index.ts');
const sourcePath='packages/python/src/truss/_catalog_runtime/migrations.sql';
const modelPath='docs/helix/02-design/models/truss-runtime-migrations-0.1.umf.json';
const source=await Bun.file(sourcePath).text();
let model:any;
if(process.argv.includes('--capture')){
 if(await Bun.file(modelPath).exists())throw Error('Existing model must be edited in place');
 model=await owner.importPostgresqlSql(source,backend,{id:'truss-runtime-migrations-storage-0.1'});
 await Bun.write(modelPath,JSON.stringify(model)+'\n');
}else model=JSON.parse(await Bun.file(modelPath).text());
if(model.umf!=='0.10.0')throw Error('Exact UMF0.10 migration model required');
const exported=await owner.exportPostgresqlSql(model,backend);
function normalized(value:any):any{
 if(Array.isArray(value))return value.map(normalized);
 if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().filter(k=>!['location','stmt_location','stmt_len'].includes(k)).map(k=>[k,normalized(value[k])]));
 return value;
}
const before=await backend.parse(source),after=await backend.parse(exported);
if(JSON.stringify(normalized(before))!==JSON.stringify(normalized(after)))throw Error('UMF migration native AST correspondence failed');
const hash=(raw:string|Uint8Array)=>new Bun.CryptoHasher('sha256').update(raw).digest('hex');
const modelBytes=await Bun.file(modelPath).arrayBuffer();
const receipt={scope:'UMF0.10 PostgreSQL native AST import/export; source locations excluded from semantic comparison; native PG18.6 execution is qualified separately',
 backend:backend.identity,sourceSha256:hash(source),originalSourceSha256:hash(owner.getPostgresqlSource(model)),modelSha256:hash(new Uint8Array(modelBytes)),ownerExportSha256:hash(exported),
 ownerFiles:Object.fromEntries(await Promise.all(['src/adapters/postgresql/index.ts','native/postgresql/runtime.ts','spec/extensions/postgresql/native-ast.schema.json','bun.lock'].map(async p=>[p,hash(new Uint8Array(await Bun.file(root+'/'+p).arrayBuffer()))]))),
 passed:true};
const out='docs/helix/04-build/evidence/runtime-migrations-20261021/receipt-model.json';
await Bun.write(out,JSON.stringify(receipt,null,2)+'\n');
await Bun.write('docs/helix/04-build/evidence/runtime-migrations-20261021/migrations.owner-export.sql',exported);
console.log(JSON.stringify(receipt));
