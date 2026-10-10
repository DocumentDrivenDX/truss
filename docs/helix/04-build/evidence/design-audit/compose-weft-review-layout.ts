/** One selected read/storage review composition; no installation or runtime adoption. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {getPostgresqlNode,proposePostgresqlNodeEdit,exportPostgresqlSql,getPostgresqlSource} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
import {readDocument,writeDocument} from '/Users/erik/Projects/umf/src/model/document';
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const paths=[
 'docs/helix/02-design/models/truss-layout-journal-stage.proposal.umf.json',
 'docs/helix/02-design/contracts/catalog-owner-homes-v0.1.proposal.umf.json',
 'docs/helix/02-design/contracts/row-home-tree-v0.1.proposal.umf.json',
 'docs/helix/02-design/contracts/row-home-scalar-v0.1.proposal.umf.json',
 'docs/helix/02-design/models/truss-relationship-lineage-candidate.umf.json',
 'docs/helix/02-design/contracts/catalog-definition-source-v0.1.proposal.umf.json',
 'docs/helix/02-design/contracts/row-home-touch-v0.1.proposal.umf.json',
 'docs/helix/02-design/contracts/row-home-capacity-v0.1.proposal.umf.json',
];
const ownerRoot='/Users/erik/Projects/umf';
async function owner(){
 const r=Bun.spawnSync(['git','-C',ownerRoot,'rev-parse','HEAD']);if(r.exitCode)throw Error('owner unavailable');
 const files=await Promise.all(['src/adapters/postgresql/index.ts','src/model/native-json.ts','src/model/document.ts','native/postgresql/runtime.ts'].map(async path=>({path,sha256:hash(await Bun.file(ownerRoot+'/'+path).text())})));
 return {commit:new TextDecoder().decode(r.stdout).trim(),files};
}
const before=await owner();const bytes=await Promise.all(paths.map(p=>Bun.file(p).text()));
const docs=bytes.map(b=>readDocument(b,'json'));
const groups=docs.map(d=>{const n=getPostgresqlNode(d,'/stmts');if(n.kind!=='array')throw Error('statement array');return n.items.map(x=>JSON.parse(renderTree(x)));});
if(groups[0].length!==43||groups[1].length!==4)throw Error('composition inputs changed');
const replacements=new Map(groups[1].filter(n=>n.stmt?.CreateStmt).map(n=>[n.stmt.CreateStmt.relation.relname,n]));
if([...replacements.keys()].sort().join(',')!=='module_access,rel_def,type_def')throw Error('owner replacements');
const nodes=groups[0].map(n=>{const name=n.stmt?.CreateStmt?.relation?.relname;if(replacements.has(name)){const replacement=replacements.get(name);replacements.delete(name);return replacement;}return n;});
if(replacements.size)throw Error('missing baseline replacement');
const comments=nodes.filter(n=>n.stmt?.CommentStmt?.objtype==='OBJECT_SCHEMA');if(comments.length!==1)throw Error('schema marker');
comments[0].stmt.CommentStmt.comment='truss-layout weft-review-0.3 REVIEW ONLY - unqualified';
nodes.push(...groups[1].filter(n=>!n.stmt?.CreateStmt),...groups.slice(2).flat());
const relations=nodes.filter(n=>n.stmt?.CreateStmt).map(n=>n.stmt.CreateStmt.relation);
const names=relations.map(r=>r.schemaname+'.'+r.relname);
if(new Set(names).size!==names.length)throw Error('duplicate table declarations');
const candidate=proposePostgresqlNodeEdit(docs[0],'/stmts',JSON.stringify(nodes)).document;
candidate.id='truss-layout-weft-review-0.3';
if(getPostgresqlSource(candidate)!==getPostgresqlSource(docs[0]))throw Error('baseline archive lost');
const sql=await exportPostgresqlSql(candidate,backend);const model=writeDocument(candidate,'yaml');
if(await exportPostgresqlSql(readDocument(model,'yaml'),backend)!==sql)throw Error('reload export changed');
const after=await owner();if(JSON.stringify(before)!==JSON.stringify(after))throw Error('owner changed');
for(let i=0;i<paths.length;i++)if(await Bun.file(paths[i]).text()!==bytes[i])throw Error('input changed');
const modelPath='docs/helix/02-design/models/truss-layout-weft-review-0.3.proposal.umf.yaml';
const sqlPath='docs/helix/02-design/models/truss-layout-weft-review-0.3.proposal.sql';
await Bun.write(modelPath,model);await Bun.write(sqlPath,sql);
const saved=readDocument(await Bun.file(modelPath).text(),'yaml');
const savedNodes=getPostgresqlNode(saved,'/stmts');
if(savedNodes.kind!=='array')throw Error('saved statements absent');
const astPath='docs/helix/04-build/evidence/design-audit/weft-review-layout.native-ast.json';
const astBytes=renderTree(savedNodes);await Bun.write(astPath,astBytes);
const receipt={scope:'Selected original UMF AST composition with three explicit catalog-owner replacements; all other selected statements preserved in order; no complete native inventory, installer, binding adoption or runtime qualification',ownerSource:before,backend:backend.identity,inputs:paths.map((path,i)=>({path,sha256:hash(bytes[i])})),replacementRelations:['module_access','type_def','rel_def'],modelPath,modelSha256:hash(model),sqlPath,sqlSha256:hash(sql),astPath,astSha256:hash(astBytes),statements:nodes.length,tables:names,sourceArchivePreserved:true,reloadedExportExact:true,installationReady:false};
await Bun.write('docs/helix/04-build/evidence/design-audit/weft-review-layout-composition.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({statements:nodes.length,tables:names.length,reloadedExportExact:true,installationReady:false}));
