/** Extract closed prerequisite statement units through the UMF owner AST API. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {getPostgresqlNode,proposePostgresqlNodeEdit,exportPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const hash=(raw:string)=>new Bun.CryptoHasher('sha256').update(raw).digest('hex');
const root='/private/tmp/truss-main-integration-20261010';
const output='/private/tmp/truss-catalog-custody-registration-draft/statements';
const mappings=[
 ['feed-transaction-create', ['create'], 'InsertStmt'],
 ['feed-member-counter-reservation', ['reserve'], 'UpdateStmt'],
 ['feed-member-insert', ['insert'], 'InsertStmt']
] as const;
const artifacts=[];
for(const [base,names,kind] of mappings){
 const source=`${root}/docs/helix/02-design/contracts/${base}-v0.1.proposal.umf.json`;
 const originalBytes=await Bun.file(source).text();
 const document=readDocument(originalBytes,'json');
 const nodes=JSON.parse(renderTree(getPostgresqlNode(document,'/stmts')));
 if(nodes.length!==1||nodes.some((node:any)=>!node.stmt?.[kind]))throw Error('Exact one original statement required');
 for(const [ordinal,name] of names.entries()){
  const selected=proposePostgresqlNodeEdit(document,'/stmts',JSON.stringify([nodes[ordinal]])).document;
  const saved=JSON.stringify(selected)+'\n';
  const sql=await exportPostgresqlSql(selected,backend);
  const reloaded=readDocument(saved,'json');
  if(await exportPostgresqlSql(reloaded,backend)!==sql)throw Error('Saved statement export correspondence required');
  const replay=JSON.parse(renderTree(getPostgresqlNode(reloaded,'/stmts')));
  if(replay.length!==1||JSON.stringify(replay[0].stmt)!==JSON.stringify(nodes[ordinal].stmt))throw Error('Original statement meaning correspondence required');
  const modelPath=`${output}/${name}.umf.json`,sqlPath=`${output}/${name}.sql`;
  await Bun.write(modelPath,saved);await Bun.write(sqlPath,sql);
  artifacts.push({name,source,sourceSha256:hash(originalBytes),ordinal,modelPath,modelSha256:hash(saved),sqlPath,sqlSha256:hash(sql)});
 }
}
const owner='/Users/erik/Projects/umf';
const revision=Bun.spawnSync(['git','-C',owner,'rev-parse','HEAD']);
const status=Bun.spawnSync(['git','-C',owner,'status','--porcelain']);
if(revision.exitCode||status.exitCode||new TextDecoder().decode(status.stdout).trim())throw Error('Committed clean UMF owner source required');
const files=['native/postgresql/runtime.ts','src/adapters/postgresql/index.ts','src/model/document.ts','src/model/native-json.ts','bun.lock'];
const ownerFiles=await Promise.all(files.map(async path=>({path,sha256:hash(await Bun.file(`${owner}/${path}`).text())})));
await Bun.write(`${output}/manifest.json`,JSON.stringify({scope:'UMF owner single-statement AST extraction and reload/export; no native execution or installed authority',ownerCommit:new TextDecoder().decode(revision.stdout).trim(),ownerFiles,artifacts},null,2)+'\n');
console.log(JSON.stringify({statements:artifacts.length,ownerCommit:new TextDecoder().decode(revision.stdout).trim()}));
