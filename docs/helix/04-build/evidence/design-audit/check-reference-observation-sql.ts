/** Source/AST custody only; no database execution or catalog/operator resolution. */
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'../../../../..');
const umf=resolve(process.argv[2]??'/Users/erik/Projects/umf');
const capture=process.argv[3]==='--capture';
const expectedHead='16c35e8d943769ccfa7bb57d16785aa7159abe65';
if(execFileSync('git',['rev-parse','HEAD'],{cwd:umf,encoding:'utf8'}).trim()!==expectedHead || execFileSync('git',['status','--porcelain'],{cwd:umf,encoding:'utf8'}).trim())throw Error('UMF source checkpoint changed or dirty');
const {backend}=await import(umf+'/native/postgresql/runtime.ts');
const api=await import(umf+'/src/index.ts');
const digest=(bytes:any)=>createHash('sha256').update(bytes).digest('hex');
const dependencies=[];
for(const path of ['native/postgresql/runtime.ts','src/adapters/postgresql/index.ts','spec/extensions/postgresql/native-ast.schema.json','node_modules/@libpg-query/parser/wasm/libpg-query.wasm'])dependencies.push({path,sha256:digest(await Bun.file(umf+'/'+path).bytes())});
const cases=[];
for(const [name,parameters] of [['reference-participation-observation.proposal.sql',[1,2,3,4,5]],['reference-code-equality-observation.proposal.sql',[1,2]],['reference-outgoing-participation.proposal.sql',[1,2,3]],['reference-incoming-participation.proposal.sql',[1,2,3]]] as const){
 const path='docs/helix/02-design/contracts/'+name,source=await Bun.file(root+'/'+path).text();
 const ast=await backend.parse(source);
 if(ast.version!==170004||ast.stmts?.length!==1||!ast.stmts[0].stmt.SelectStmt)throw Error('Expected one PostgreSQL 17.4 SelectStmt');
 const found=new Set<number>();
 function visit(value:any){if(!value||typeof value!=='object')return;if(value.ParamRef)found.add(value.ParamRef.number);for(const child of Object.values(value))visit(child);}
 visit(ast);if(JSON.stringify([...found].sort())!==JSON.stringify(parameters))throw Error('Parameter inventory mismatch');
 const doc=await api.importPostgresqlSql(source,backend,{id:'truss.source-review.'+name});
 for(const format of ['json','yaml']){const restored=api.readDocument(api.writeDocument(doc,format),format);if(api.getPostgresqlSource(restored)!==source||JSON.stringify(api.getPostgresqlNode(restored,''))!==JSON.stringify(api.getPostgresqlNode(doc,'')))throw Error('UMF source/tree changed');}
 const exported=await api.exportPostgresqlSql(doc,backend);
 cases.push({path,sha256:digest(source),parameters,statement:'SelectStmt',umfJsonYamlSourceAndTreePreserved:true,ownerExportReparseAstEquality:true,exportedSql:exported});
}
const receipt={scope:'Pinned UMF parser/codec/JSON-YAML/export round-trip only; no native execution, catalog dependency resolution, policy, resource or Weft qualification',producerSha256:digest(await Bun.file(fileURLToPath(import.meta.url)).bytes()),umfCommit:expectedHead,backend:backend.identity,parserTreeVersion:170004,dependencies,cases};
const output=here+'/reference-observation-sql-source-review.json';
if(capture)await Bun.write(output,JSON.stringify(receipt,null,2)+'\n');
else if(JSON.stringify(await Bun.file(output).json())!==JSON.stringify(receipt))throw Error('Stale source review receipt');
console.log(JSON.stringify({mode:capture?'capture':'check',cases:cases.length,sourceCustody:true,nativeExecution:false}));
