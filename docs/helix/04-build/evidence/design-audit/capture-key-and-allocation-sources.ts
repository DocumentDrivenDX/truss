/** Truss design-source capture; never database mutation or complete installation. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {importPostgresqlSql,exportPostgresqlSql,getPostgresqlSource} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {readDocument,writeDocument} from '/Users/erik/Projects/umf/src/model/document';
const paths=['docs/helix/02-design/contracts/key-bucket-layout-v0.1.draft.sql','docs/helix/02-design/contracts/catalog-id-high-water-v0.1.draft.sql'];
const root='/Users/erik/Projects/umf';const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
async function owner(){const r=Bun.spawnSync(['git','-C',root,'rev-parse','HEAD']);if(r.exitCode)throw Error('owner unavailable');return {commit:new TextDecoder().decode(r.stdout).trim(),files:await Promise.all(['src/adapters/postgresql/index.ts','src/model/document.ts','native/postgresql/runtime.ts'].map(async path=>({path,sha256:hash(await Bun.file(root+'/'+path).text())})))};}
const before=await owner(),results=[];
for(const path of paths){
 const source=await Bun.file(path).text();const d=await importPostgresqlSql(source,backend,{id:'truss-'+path.split('/').at(-1)!.replace('.sql','')});
 const bytes=writeDocument(d,'json'),sql=await exportPostgresqlSql(d,backend),reload=readDocument(bytes,'json');
 if(getPostgresqlSource(reload)!==source||await exportPostgresqlSql(reload,backend)!==sql)throw Error('capture mismatch');
 const modelPath=path.replace('.sql','.umf.json');await Bun.write(modelPath,bytes);
 if(await Bun.file(path).text()!==source)throw Error('source changed');
 results.push({path,sha256:hash(source),modelPath,modelSha256:hash(bytes),sourceArchiveExact:true,reloadedExportExact:true});
}
if(JSON.stringify(before)!==JSON.stringify(await owner()))throw Error('owner changed');
await Bun.write('docs/helix/04-build/evidence/design-audit/key-and-allocation-source-capture.json',JSON.stringify({scope:'Exact UMF source capture/reload/export only; no native uniqueness, allocator visibility/grants or installed body qualification',ownerSource:before,backend:backend.identity,results},null,2)+'\n');
console.log(JSON.stringify({sources:results.length,sourceArchiveExact:true,reloadedExportExact:true}));
