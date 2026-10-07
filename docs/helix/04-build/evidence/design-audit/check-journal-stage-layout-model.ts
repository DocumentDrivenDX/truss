/** Edited UMF model generation experiment; never an installation-ready bundle. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {getPostgresqlNode,proposePostgresqlNodeEdit,exportPostgresqlSql,getPostgresqlSource} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
import {readDocument,writeDocument} from '/Users/erik/Projects/umf/src/model/document';
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const ownerRoot='/Users/erik/Projects/umf';
const ownerPaths=['src/adapters/postgresql/index.ts','src/model/native-json.ts','src/model/document.ts','native/postgresql/runtime.ts','bun.lock'];
async function owner(){const git=Bun.spawnSync(['git','-C',ownerRoot,'rev-parse','HEAD']);if(git.exitCode)throw Error('owner unavailable');return {root:ownerRoot,commit:new TextDecoder().decode(git.stdout).trim(),files:await Promise.all(ownerPaths.map(async path=>({path,sha256:hash(await Bun.file(ownerRoot+'/'+path).text())})))};}
const before=await owner();
const paths=['docs/helix/02-design/models/truss-layout-complete-history.proposal.umf.json','docs/helix/02-design/contracts/row-home-operation-v0.1.proposal.umf.json','docs/helix/02-design/contracts/row-home-journal-stage-v0.2.proposal.umf.json'];
const bytes=await Promise.all(paths.map(p=>Bun.file(p).text()));
const documents=bytes.map(b=>readDocument(b,'json'));
const arrays=documents.map(d=>getPostgresqlNode(d,'/stmts'));
if(arrays.some(a=>a.kind!=='array'))throw Error('statement arrays absent');
const groups=arrays.map(a=>a.kind==='array'?a.items.map(n=>JSON.parse(renderTree(n))):[]);
if(groups[0].length!==41||groups[1].length!==1||groups[2].length!==1)throw Error('exact input inventory');
for(const [index,name] of [[1,'row_home_operation'],[2,'row_home_journal_stage']] as const){
 const r=groups[index][0].stmt?.CreateStmt?.relation;
 if(r?.schemaname!=='truss'||r.relname!==name)throw Error('parent/child creation mismatch');
}
const nodes=groups.flat();
const comments=nodes.filter(n=>n.stmt?.CommentStmt?.objtype==='OBJECT_SCHEMA');
if(comments.length!==1||comments[0].stmt.CommentStmt.comment!=='truss-layout complete-history REVIEW ONLY - unqualified')throw Error('marker mismatch');
comments[0].stmt.CommentStmt.comment='truss-layout journal-stage REVIEW ONLY - unqualified';
const candidate=proposePostgresqlNodeEdit(documents[0],'/stmts',JSON.stringify(nodes)).document;
candidate.id='truss-layout-journal-stage-review';
if(getPostgresqlSource(candidate)!==getPostgresqlSource(documents[0]))throw Error('original archive lost');
const output=await exportPostgresqlSql(candidate,backend);
const modelPath='docs/helix/02-design/models/truss-layout-journal-stage.proposal.umf.json';
const exportPath='docs/helix/04-build/evidence/design-audit/truss-layout-journal-stage.owner-export.sql';
const modelBytes=writeDocument(candidate,'json');
await Bun.write(modelPath,modelBytes);await Bun.write(exportPath,output);
if(await exportPostgresqlSql(readDocument(modelBytes,'json'),backend)!==output)throw Error('reload export mismatch');
const after=await owner();if(JSON.stringify(before)!==JSON.stringify(after))throw Error('UMF source changed');
for(let i=0;i<paths.length;i++)if(await Bun.file(paths[i]).text()!==bytes[i])throw Error('input changed');
const receipt={scope:'Existing UMF composition/export/reload of complete-history review plus parent registry then journal child-store declarations only; no native dependency/grant/body/install qualification',ownerSource:before,bunVersion:Bun.version,backend:backend.identity,inputs:paths.map((path,i)=>({path,sha256:hash(bytes[i])})),modelPath,modelSha256:hash(modelBytes),exportPath,exportSha256:hash(output),statements:43,parentBeforeChild:true,baselineArchivePreserved:true,reloadedExportExact:true,installationReady:false};
await Bun.write('docs/helix/04-build/evidence/design-audit/journal-stage-layout-model-source.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({statements:43,parentBeforeChild:true,reloadedExportExact:true,installationReady:false}));
