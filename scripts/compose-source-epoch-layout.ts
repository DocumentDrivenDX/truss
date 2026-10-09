/** Candidate source composition through the existing UMF owner adapter. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {getPostgresqlNode,proposePostgresqlNodeEdit,exportPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const source='docs/helix/02-design/models/truss-layout-qualified-property-0.15.proposal.umf.json';
const original=readDocument(await Bun.file(source).text(),'json');
const nodes=JSON.parse(renderTree(getPostgresqlNode(original,'/stmts')));
const fragment=readDocument(await Bun.file('docs/helix/02-design/contracts/source-epoch-storage-v0.1.proposal.umf.json').text(),'json');
nodes.push(...JSON.parse(renderTree(getPostgresqlNode(fragment,'/stmts'))));
const comment=nodes.find((n:any)=>n.stmt?.CommentStmt?.objtype==='OBJECT_SCHEMA');
if(!comment)throw Error('Missing review-only label');
comment.stmt.CommentStmt.comment='truss-layout source-epoch-0.16 REVIEW ONLY - unqualified';
const result=proposePostgresqlNodeEdit(original,'/stmts',JSON.stringify(nodes)).document;
result.id='truss-layout-source-epoch-0.16-review';
const modelPath='docs/helix/02-design/models/truss-layout-source-epoch-0.16.proposal.umf.json';
const ddlPath='docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql';

const tables=nodes.filter((n:any)=>n.stmt?.CreateStmt).map((n:any)=>({name:n.stmt.CreateStmt.relation.relname,columns:(n.stmt.CreateStmt.tableElts??[]).filter((e:any)=>e.ColumnDef).length}));
if(new Set(tables.map((t:any)=>t.name)).size!==tables.length)throw Error('Duplicate table declaration');
if(!tables.some((t:any)=>t.name==='source_epoch_registry')||!tables.some((t:any)=>t.name==='source_epoch_current'))throw Error('Missing epoch declarations');
const serialized=JSON.stringify(result)+'\n';const ddl=await exportPostgresqlSql(result,backend);
if(await exportPostgresqlSql(readDocument(serialized,'json'),backend)!==ddl)throw Error('Reload/export mismatch');
await Bun.write(modelPath,serialized);await Bun.write(ddlPath,ddl);
console.log(JSON.stringify({modelPath,ddlPath,reloadedExportExact:true,qualified:false}));
const ownerRoot='/Users/erik/Projects/umf';const observed=Bun.spawnSync(['git','-C',ownerRoot,'rev-parse','HEAD']);if(observed.exitCode)throw Error('Owner revision unavailable');
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
await Bun.write('docs/helix/04-build/evidence/design-audit/source-epoch-layout-source.json',JSON.stringify({scope:'UMF owner AST composition and saved reload/export only; no conversion or installed runtime qualification',ownerRoot,ownerCommit:new TextDecoder().decode(observed.stdout).trim(),source,sourceSha256:hash(await Bun.file(source).text()),fragmentPath:'docs/helix/02-design/contracts/source-epoch-storage-v0.1.proposal.umf.json',fragmentSha256:hash(await Bun.file('docs/helix/02-design/contracts/source-epoch-storage-v0.1.proposal.umf.json').text()),tableCount:tables.length,declaredCreateColumnCount:tables.reduce((n:number,t:any)=>n+t.columns,0),tables,modelPath,modelSha256:hash(serialized),ddlPath,ddlSha256:hash(ddl),reloadedExportExact:true},null,2)+'\n');
