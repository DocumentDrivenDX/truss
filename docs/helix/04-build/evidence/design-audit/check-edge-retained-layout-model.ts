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
const baselinePath='docs/helix/02-design/models/truss-layout-0.2.umf.json';
const fragmentPath='docs/helix/02-design/contracts/edge-retained-home-v0.1.proposal.umf.json';
const baselineBytes=await Bun.file(baselinePath).text(),fragmentBytes=await Bun.file(fragmentPath).text();
const baseline=readDocument(baselineBytes,'json'),fragment=readDocument(fragmentBytes,'json');
const original=getPostgresqlNode(baseline,'/stmts'),addition=getPostgresqlNode(fragment,'/stmts');
if(original.kind!=='array'||addition.kind!=='array'||addition.items.length!==2)throw Error('source statement inventory');
const nodes=original.items.map(node=>JSON.parse(renderTree(node)));
const comments=nodes.filter(node=>node.stmt?.CommentStmt?.objtype==='OBJECT_SCHEMA');
if(comments.length!==1||comments[0].stmt.CommentStmt.comment!=='truss-layout 0.2')throw Error('baseline marker mismatch');
comments[0].stmt.CommentStmt.comment='truss-layout edge-retained REVIEW ONLY - unqualified';
nodes.push(...addition.items.map(node=>JSON.parse(renderTree(node))));
const candidate=proposePostgresqlNodeEdit(baseline,'/stmts',JSON.stringify(nodes)).document;
// Identity labels this experiment, not an adopted runtime layout version.
candidate.id='truss-layout-edge-retained-review';
if(getPostgresqlSource(candidate)!==getPostgresqlSource(baseline))throw Error('archived baseline source lost');
const output=await exportPostgresqlSql(candidate,backend);
if(output===await exportPostgresqlSql(baseline,backend)||!output.includes('REVIEW ONLY'))throw Error('edited AST ignored');
const modelPath='docs/helix/02-design/models/truss-layout-edge-retained.proposal.umf.json';
const exportPath='docs/helix/04-build/evidence/design-audit/truss-layout-edge-retained.owner-export.sql';
const modelBytes=writeDocument(candidate,'json');
await Bun.write(modelPath,modelBytes);await Bun.write(exportPath,output);
const reloaded=readDocument(await Bun.file(modelPath).text(),'json');
if(await exportPostgresqlSql(reloaded,backend)!==output)throw Error('edited model reload mismatch');
const after=await owner();if(JSON.stringify(before)!==JSON.stringify(after))throw Error('owner changed');
if(await Bun.file(baselinePath).text()!==baselineBytes||await Bun.file(fragmentPath).text()!==fragmentBytes)throw Error('input changed');
const receipt={scope:'existing UMF edited native statement-array export and JSON reload only; no complete required physical inventory, catalog resolution, native execution, migration or runtime adoption',ownerSource:before,bunVersion:Bun.version,backend:backend.identity,inputs:[{path:baselinePath,sha256:hash(baselineBytes)},{path:fragmentPath,sha256:hash(fragmentBytes)}],modelPath,modelSha256:hash(modelBytes),exportPath,exportSha256:hash(output),originalStatements:original.items.length,addedStatements:2,reviewMarker:true,baselineArchivePreserved:true,editedAstExport:true,reloadedExportExact:true,installationReady:false};
await Bun.write('docs/helix/04-build/evidence/design-audit/edge-retained-layout-model-source.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({originalStatements:original.items.length,addedStatements:2,editedAstExport:true,reloadedExportExact:true,installationReady:false}));
