/** Edited UMF model generation experiment; never an installation-ready bundle. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {getPostgresqlNode,proposePostgresqlNodeEdit,exportPostgresqlSql,getPostgresqlSource,importPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
const checkOnly=Bun.argv.includes('--check');
const producerPath='docs/helix/04-build/evidence/design-audit/compose-reference-history-layout.ts';
const producerBytes=await Bun.file(producerPath).text();
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const ownerRoot='/Users/erik/Projects/umf';
const ownerPaths=['src/adapters/postgresql/index.ts','src/model/native-json.ts','src/model/document.ts','native/postgresql/runtime.ts','bun.lock'];
async function owner(){const git=Bun.spawnSync(['git','-C',ownerRoot,'rev-parse','HEAD']);if(git.exitCode)throw Error('owner unavailable');return {root:ownerRoot,commit:new TextDecoder().decode(git.stdout).trim(),files:await Promise.all(ownerPaths.map(async path=>({path,sha256:hash(await Bun.file(ownerRoot+'/'+path).text())})))};}
const before=await owner();
const recipePath='docs/helix/02-design/contracts/reference-history-composition-v0.1.proposal.json';
const recipeBytes=await Bun.file(recipePath).text(),recipe=JSON.parse(recipeBytes);
for(const input of recipe.inputs)if(hash(await Bun.file('docs/helix/'+input.path).text())!==input.sha256)throw Error('recipe input drift');
const baselinePath='docs/helix/02-design/models/truss-layout-weft-review-0.11.proposal.umf.json';
const fragmentPath='docs/helix/02-design/contracts/journal-complete-carrier-v0.2.proposal.umf.json';
const baselineBytes=await Bun.file(baselinePath).text(),fragmentBytes=await Bun.file(fragmentPath).text();
const baseline=readDocument(baselineBytes,'json'),fragment=readDocument(fragmentBytes,'json');
const original=getPostgresqlNode(baseline,'/stmts'),addition=getPostgresqlNode(fragment,'/stmts');
if(original.kind!=='array'||addition.kind!=='array'||addition.items.length!==4)throw Error('source statement inventory');
if(original.items.length!==106)throw Error('foundation count');
const nodes=original.items.map(node=>JSON.parse(renderTree(node)));
const journals=nodes.filter(node=>node.stmt?.CreateStmt?.relation?.schemaname==='truss'&&node.stmt.CreateStmt.relation.relname==='journal');
if(journals.length!==1)throw Error('journal creation inventory');
const column=journals[0].stmt.CreateStmt.tableElts.find((n:any)=>n.ColumnDef?.colname==='op')?.ColumnDef;
const checks=column?.constraints?.filter((n:any)=>n.Constraint?.contype==='CONSTR_CHECK');
if(checks?.length!==1)throw Error('operation constraint inventory');
const list=checks[0].Constraint.raw_expr?.A_Expr?.rexpr?.List?.items;
if(JSON.stringify(list?.map((n:any)=>n.A_Const?.sval?.sval))!==JSON.stringify(['create','update','delete','retain','rebind','transform','metadata']))throw Error('original operation set');
// Foundation already includes metadata; preserve the exact original constraint.
const comments=nodes.filter(node=>node.stmt?.CommentStmt?.objtype==='OBJECT_SCHEMA');
if(comments.length!==1||comments[0].stmt.CommentStmt.comment!=='truss-layout weft-review-0.11 REVIEW ONLY - unqualified')throw Error('baseline marker mismatch');
comments[0].stmt.CommentStmt.comment='truss-layout reference-history-0.12 REVIEW ONLY - unqualified';
for(const item of addition.items){const expected=renderTree(item);if(original.items.filter(n=>renderTree(n)===expected).length!==1)throw Error('carrier fragment correspondence');}
const stagePath='docs/helix/02-design/contracts/row-home-journal-stage-v0.2.proposal.umf.json';
const stageBytes=await Bun.file(stagePath).text(),stage=getPostgresqlNode(readDocument(stageBytes,'json'),'/stmts');
if(stage.kind!=='array'||stage.items.length!==1)throw Error('stage statement inventory');
const tables=nodes.filter(n=>n.stmt?.CreateStmt).map(n=>n.stmt.CreateStmt.relation.relname);
if(tables.filter(n=>n==='row_home_operation').length!==1||tables.filter(n=>n==='row_home_journal_stage').length!==1)throw Error('stage parent identity');
const stageNode=JSON.parse(renderTree(stage.items[0]));
if(stageNode.stmt?.CreateStmt?.relation?.relname!=='row_home_journal_stage'||stageNode.stmt.CreateStmt.tableElts.filter((n:any)=>n.ColumnDef).length!==6)throw Error('child inventory');
if(original.items.filter(n=>renderTree(n)===renderTree(stage.items[0])).length!==1)throw Error('stage fragment correspondence');
const parentIndex=nodes.findIndex(n=>n.stmt?.CreateStmt?.relation?.relname==='row_home_operation');
const stageIndex=nodes.findIndex(n=>n.stmt?.CreateStmt?.relation?.relname==='row_home_journal_stage');
if(parentIndex<0||stageIndex<=parentIndex)throw Error('parent declaration order');
const sequences=nodes.filter(n=>n.stmt?.CreateSeqStmt?.sequence?.schemaname==='truss'&&n.stmt.CreateSeqStmt.sequence.relname==='journal_seq');
if(sequences.length!==1||sequences[0].stmt.CreateSeqStmt.options)throw Error('original sequence declaration drift');
const selected=await importPostgresqlSql('CREATE SEQUENCE truss.journal_seq AS bigint INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START WITH 1 NO CYCLE CACHE 1;',backend,{id:'selected-journal-sequence-review'});
const selectedNodes=getPostgresqlNode(selected,'/stmts');
if(selectedNodes.kind!=='array'||selectedNodes.items.length!==1)throw Error('selected sequence inventory');
sequences[0].stmt.CreateSeqStmt.options=JSON.parse(renderTree(selectedNodes.items[0])).stmt.CreateSeqStmt.options;
const comparison=structuredClone(nodes);
comparison.find((n:any)=>n.stmt?.CommentStmt?.objtype==='OBJECT_SCHEMA').stmt.CommentStmt.comment='truss-layout weft-review-0.11 REVIEW ONLY - unqualified';
delete comparison.find((n:any)=>n.stmt?.CreateSeqStmt?.sequence?.relname==='journal_seq').stmt.CreateSeqStmt.options;
if(JSON.stringify(comparison)!==JSON.stringify(original.items.map(n=>JSON.parse(renderTree(n)))))throw Error('unexpected foundation delta');
const candidate=proposePostgresqlNodeEdit(baseline,'/stmts',JSON.stringify(nodes)).document;
// Identity labels this experiment, not an adopted runtime layout version.
candidate.id='truss-layout-reference-history-0.12-review';
if(getPostgresqlSource(candidate)!==getPostgresqlSource(baseline))throw Error('archived baseline source lost');
const output=await exportPostgresqlSql(candidate,backend);
if(output===await exportPostgresqlSql(baseline,backend)||!output.includes('REVIEW ONLY'))throw Error('edited AST ignored');
const modelPath='docs/helix/02-design/models/truss-layout-reference-history-0.12.proposal.umf.json';
const exportPath='docs/helix/04-build/evidence/design-audit/truss-layout-reference-history-0.12.owner-export.sql';
// Compact JSON remains within the existing UMF input bound; reload validates it.
const modelBytes=JSON.stringify(candidate)+'\n';
if(checkOnly){if(await Bun.file(modelPath).text()!==modelBytes||await Bun.file(exportPath).text()!==output)throw Error('generated output drift');}
else{await Bun.write(modelPath,modelBytes);await Bun.write(exportPath,output);}
const reloaded=readDocument(await Bun.file(modelPath).text(),'json');
if(await exportPostgresqlSql(reloaded,backend)!==output)throw Error('edited model reload mismatch');
const after=await owner();if(JSON.stringify(before)!==JSON.stringify(after))throw Error('owner changed');
if(await Bun.file(baselinePath).text()!==baselineBytes||await Bun.file(fragmentPath).text()!==fragmentBytes||await Bun.file(stagePath).text()!==stageBytes||await Bun.file(recipePath).text()!==recipeBytes||await Bun.file(producerPath).text()!==producerBytes)throw Error('input changed');
const receipt={scope:'existing UMF edited native statement-array export and JSON reload only; no complete required physical inventory, catalog resolution, native execution, migration or runtime adoption',producer:{path:producerPath,sha256:hash(producerBytes)},parentBeforeChild:true,ownerSource:before,bunVersion:Bun.version,backend:backend.identity,recipe:{path:recipePath,sha256:hash(recipeBytes)},inputs:[{path:stagePath,sha256:hash(stageBytes)},{path:baselinePath,sha256:hash(baselineBytes)},{path:fragmentPath,sha256:hash(fragmentBytes)}],modelPath,modelSha256:hash(modelBytes),exportPath,exportSha256:hash(output),originalStatements:original.items.length,addedStatements:0,actualStatements:nodes.length,selectedSequenceSettings:true,existingParentReused:true,reviewMarker:true,metadataOpPreserved:true,baselineArchivePreserved:true,foundationDeltaVerified:true,carrierAndStageExactOriginal:true,editedAstExport:true,reloadedExportExact:true,installationReady:false};
const receiptPath='docs/helix/04-build/evidence/design-audit/reference-history-layout-model-source.json',receiptBytes=JSON.stringify(receipt,null,2)+'\n';
if(checkOnly){if(await Bun.file(receiptPath).text()!==receiptBytes)throw Error('source receipt drift');}
else await Bun.write(receiptPath,receiptBytes);
console.log(JSON.stringify({originalStatements:original.items.length,addedStatements:0,actualStatements:nodes.length,selectedSequenceSettings:true,existingParentReused:true,foundationDeltaVerified:true,carrierAndStageExactOriginal:true,editedAstExport:true,reloadedExportExact:true,installationReady:false}));
