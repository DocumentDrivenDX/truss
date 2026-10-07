/** Selected key/report profile evolution; no installer or database execution. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {getPostgresqlNode,proposePostgresqlNodeEdit,exportPostgresqlSql,getPostgresqlSource} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
import {readDocument,writeDocument} from '/Users/erik/Projects/umf/src/model/document';
const paths=['docs/helix/02-design/models/truss-layout-weft-review-0.3.proposal.umf.yaml','docs/helix/02-design/contracts/key-bucket-layout-v0.1.draft.umf.json','docs/helix/02-design/contracts/catalog-acceptance-report-v0.1.proposal.umf.json','docs/helix/02-design/contracts/catalog-id-high-water-v0.1.draft.umf.json'];
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const bytes=await Promise.all(paths.map(p=>Bun.file(p).text()));const documents=bytes.map((b,i)=>readDocument(b,i===0?'yaml':'json'));
const groups=documents.map(d=>{const n=getPostgresqlNode(d,'/stmts');if(n.kind!=='array')throw Error('statement array');return n.items.map(x=>JSON.parse(renderTree(x)));});
if(groups[0].length!==64||groups[1].length!==6||groups[2].length!==1||groups[3].length!==4)throw Error('selected input inventory changed');
const original=groups[0];let removedKeys=0,removedReports=0,edgeReservation=0;
const nodes=original.filter(n=>{if(n.stmt?.CreateStmt?.relation?.relname==='object_key'){removedKeys++;return false;}return true;});
for(const n of nodes){
 const c=n.stmt?.CreateStmt;
 if(c?.relation?.relname==='schema_rev')c.tableElts=c.tableElts.filter((x:any)=>{if(x.ColumnDef?.colname==='report'){removedReports++;return false;}return true;});
 if(c?.relation?.relname==='key_tombstone'){
  const column=c.tableElts.find((x:any)=>x.ColumnDef?.colname==='entity_kind')?.ColumnDef;
  const check=column?.constraints?.find((x:any)=>x.Constraint?.contype==='CONSTR_CHECK')?.Constraint;
  const values=check?.raw_expr?.A_Expr?.rexpr?.List?.items;
  if(JSON.stringify(values?.map((x:any)=>x.A_Const?.sval?.sval))!==JSON.stringify(['o','e']))throw Error('reservation kind grammar');
  check.raw_expr.A_Expr.rexpr.List.items=values.filter((x:any)=>x.A_Const.sval.sval==='e');edgeReservation++;
 }
 if(n.stmt?.CommentStmt?.objtype==='OBJECT_SCHEMA')n.stmt.CommentStmt.comment='truss-layout weft-review-0.4 REVIEW ONLY - unqualified';
}
if(removedKeys!==1||removedReports!==1||edgeReservation!==1)throw Error('replacement inventory');
nodes.push(...groups.slice(1).flat());
const names=nodes.filter(n=>n.stmt?.CreateStmt).map(n=>n.stmt.CreateStmt.relation.relname);
if(new Set(names).size!==names.length)throw Error('duplicate tables');
const d=proposePostgresqlNodeEdit(documents[0],'/stmts',JSON.stringify(nodes)).document;d.id='truss-layout-weft-review-0.4';
if(getPostgresqlSource(d)!==getPostgresqlSource(documents[0]))throw Error('archive lost');
const sql=await exportPostgresqlSql(d,backend),model=writeDocument(d,'yaml');
const modelPath='docs/helix/02-design/models/truss-layout-weft-review-0.4.proposal.umf.yaml',sqlPath='docs/helix/02-design/models/truss-layout-weft-review-0.4.proposal.sql';
await Bun.write(modelPath,model);await Bun.write(sqlPath,sql);
const saved=readDocument(await Bun.file(modelPath).text(),'yaml');if(await exportPostgresqlSql(saved,backend)!==sql)throw Error('saved export mismatch');
const astPath='docs/helix/04-build/evidence/design-audit/weft-key-profile.native-ast.json',ast=renderTree(getPostgresqlNode(saved,'/stmts'));await Bun.write(astPath,ast);
for(let i=0;i<paths.length;i++)if(await Bun.file(paths[i]).text()!==bytes[i])throw Error('input changed');
await Bun.write('docs/helix/04-build/evidence/design-audit/weft-key-profile-composition.json',JSON.stringify({scope:'Selected proposal replacing canonical legacy object-key/report homes, retaining edge-only tombstones and adding bucket/report/high-water declarations; no installed enforcement or binding adoption',inputs:paths.map((path,i)=>({path,sha256:hash(bytes[i])})),modelPath,modelSha256:hash(model),sqlPath,sqlSha256:hash(sql),astPath,astSha256:hash(ast),statements:nodes.length,tables:names,installationReady:false,reloadedExportExact:true},null,2)+'\n');
console.log(JSON.stringify({statements:nodes.length,tables:names.length,reloadedExportExact:true,installationReady:false}));
