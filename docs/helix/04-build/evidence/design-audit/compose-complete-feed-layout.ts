/** Complete-feed source composition only; no marker publication or DB execution. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {getPostgresqlNode,proposePostgresqlNodeEdit,exportPostgresqlSql,getPostgresqlSource} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
const paths=['docs/helix/02-design/models/truss-layout-weft-review-0.5.proposal.umf.yaml','docs/helix/02-design/contracts/feed-native-layout-v0.1.proposal.umf.json','docs/helix/02-design/contracts/complete-feed-consumer-v0.1.proposal.umf.json'];
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const bytes=await Promise.all(paths.map(p=>Bun.file(p).text())),docs=bytes.map((b,i)=>readDocument(b,i===0?'yaml':'json'));
const groups=docs.map(d=>{const n=getPostgresqlNode(d,'/stmts');if(n.kind!=='array')throw Error('statements absent');return n.items.map(x=>JSON.parse(renderTree(x)));});
if(groups[0].length!==78||groups[1].length!==4||groups[2].length!==3)throw Error('selected inputs changed');
const nodes=groups.flat();const comments=nodes.filter(n=>n.stmt?.CommentStmt?.objtype==='OBJECT_SCHEMA');if(comments.length!==1)throw Error('marker');comments[0].stmt.CommentStmt.comment='truss-layout weft-review-0.6 REVIEW ONLY - unqualified';
const names=nodes.filter(n=>n.stmt?.CreateStmt).map(n=>n.stmt.CreateStmt.relation.relname);if(new Set(names).size!==names.length)throw Error('duplicate table');
const d=proposePostgresqlNodeEdit(docs[0],'/stmts',JSON.stringify(nodes)).document;d.id='truss-layout-weft-review-0.6';
if(getPostgresqlSource(d)!==getPostgresqlSource(docs[0]))throw Error('source archive lost');
// Compact ordinary JSON is accepted by UMF readDocument under the same limits.
// Validate and re-export the saved encoding; no limit or native-tree meaning changes.
const model=JSON.stringify(d)+'\n';readDocument(model,'json');const sql=await exportPostgresqlSql(d,backend);
const modelPath='docs/helix/02-design/models/truss-layout-weft-review-0.6.proposal.umf.json',sqlPath='docs/helix/02-design/models/truss-layout-weft-review-0.6.proposal.sql';
await Bun.write(modelPath,model);await Bun.write(sqlPath,sql);const saved=readDocument(await Bun.file(modelPath).text(),'json');
if(await exportPostgresqlSql(saved,backend)!==sql)throw Error('saved export changed');
const astPath='docs/helix/04-build/evidence/design-audit/complete-feed-layout-profile.native-ast.json',ast=renderTree(getPostgresqlNode(saved,'/stmts'));await Bun.write(astPath,ast);
for(let i=0;i<paths.length;i++)if(await Bun.file(paths[i]).text()!==bytes[i])throw Error('input changed');
await Bun.write('docs/helix/04-build/evidence/design-audit/complete-feed-layout-profile-composition.json',JSON.stringify({serialization:'compact ECMAScript JSON; owner readDocument limits/validation unchanged',scope:'Complete ordered 0.5 source profile plus four complete-feed stores and consumer registration/checkpoint home; no native admission, initialization, privileges, migration, ready marker or compiler binding adoption',inputs:paths.map((path,i)=>({path,sha256:hash(bytes[i])})),modelPath,modelSha256:hash(model),sqlPath,sqlSha256:hash(sql),astPath,astSha256:hash(ast),statements:nodes.length,tables:names,reloadedExportExact:true,installationReady:false},null,2)+'\n');
console.log(JSON.stringify({statements:nodes.length,tables:names.length,reloadedExportExact:true,installationReady:false}));
