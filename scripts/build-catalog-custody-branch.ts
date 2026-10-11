/** Distinct custody-aware candidate branch, edited and exported through owner AST. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {importPostgresqlSql,getPostgresqlNode,proposePostgresqlNodeEdit,exportPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const oldRecipe='packages/python/src/truss/_profiles/catalog-report-wide-composition-candidate.json';
const newRecipe='packages/python/src/truss/_profiles/catalog-report-custody-composition-candidate.json';
const oldBytes=await Bun.file(oldRecipe).text();
const recipe={...JSON.parse(oldBytes),identity:'truss-catalog-report-custody-composition-candidate',scope:'administrative rollback-only custody branch; no public acceptance or feed qualification'};
recipe.contextMapping.captureProfile='selected profileArtifacts.captureProfile artifact; its original bytes equal retained assertedOriginCaptureProfileHex';
const newBytes=JSON.stringify(recipe,null,2)+'\n';
const renames:Record<string,string>={
 runtime_collect_fresh_catalog_lifecycle:'runtime_collect_custody_catalog_lifecycle_candidate',
 runtime_collect_configured_catalog_graph:'runtime_collect_custody_catalog_graph_candidate',
 runtime_stage_catalog_admitted:'runtime_stage_custody_catalog_admitted_candidate',
 runtime_stage_catalog_with_release:'runtime_stage_custody_catalog_with_release_candidate',
 runtime_write_catalog_report_wide_candidate:'runtime_write_custody_catalog_report_candidate',
 [oldRecipe]:newRecipe,[hash(oldBytes)]:hash(newBytes),
};
const sources=[
 ['packages/postgresql/native/catalog-report/configured-graph.sql','configured-graph'],
 ['packages/postgresql/native/catalog-report/fresh-lifecycle.sql','fresh-lifecycle'],
 ['packages/postgresql/native/catalog-stage-issued.sql','stage-issued'],
 ['packages/postgresql/native/catalog-report/configured-stage.sql','configured-stage'],
 ['packages/postgresql/native/catalog-report/report-write-wide-candidate.sql','report-write'],
] as const;
const artifacts=[];
const outputs:[[string,string]]|[string,string][]=[[newRecipe,newBytes]];
for(const [source,name] of sources){
 const originalBytes=await Bun.file(source).text();
 const model=await importPostgresqlSql(originalBytes,backend,{id:'truss-catalog-custody-'+name+'-candidate'});
 const nodes=JSON.parse(renderTree(getPostgresqlNode(model,'/stmts')));
 const functions=nodes.filter((node:any)=>node.stmt?.CreateFunctionStmt && Object.keys(renames).includes(node.stmt.CreateFunctionStmt.funcname.at(-1).String.sval));
 if(functions.length!==1)throw Error('Exactly one selected original function required: '+source);
 const originalName=functions[0].stmt.CreateFunctionStmt.funcname.at(-1).String.sval;
 const grants=nodes.filter((node:any)=>node.stmt?.GrantStmt && JSON.stringify(node.stmt.GrantStmt).includes(originalName));
 if(grants.length!==1||grants[0].stmt.GrantStmt.is_grant===true)throw Error('Exact original function revoke required: '+source);
 const transformed=[...functions,...grants];
 let replacements=0;
 const edit=(v:any):any=>{
  if(typeof v==='string'){
   for(const [old,next] of Object.entries(renames))if(v.includes(old)){v=v.split(old).join(next);replacements++;}
   if(name==='configured-graph'&&v.includes("'request_receipt_route_guard','request_receipt'")){
    v=v.replace("'request_receipt_route_guard','request_receipt'", "'catalog_revision_custody','request_receipt_route_guard','request_receipt'");replacements++;
   }
   return v;
  }
  if(Array.isArray(v))return v.map(edit);
  if(v&&typeof v==='object')return Object.fromEntries(Object.entries(v).map(([k,val])=>[k,edit(val)]));
  return v;
 };
 const selected=proposePostgresqlNodeEdit(model,'/stmts',JSON.stringify(edit(transformed))).document;
 if(replacements<1)throw Error('No branch rename');
 const saved=JSON.stringify(selected)+'\n',sql=await exportPostgresqlSql(selected,backend);
 if(await exportPostgresqlSql(readDocument(saved,'json'),backend)!==sql)throw Error('Saved model export mismatch');
 const path='packages/postgresql/native/catalog-custody/'+name;
 outputs.push([path+'.umf.json',saved],[path+'.sql',sql]);
 artifacts.push({source,sourceSha256:hash(originalBytes),model:path+'.umf.json',modelSha256:hash(saved),sql:path+'.sql',sqlSha256:hash(sql)});
}
outputs.push(['packages/postgresql/native/catalog-custody/branch-manifest.json',JSON.stringify({scope:'Source composition only; not installed, captured or native-qualified',qualified:false,recipe:newRecipe,recipeSha256:hash(newBytes),artifacts},null,2)+'\n']);
for(const [path,bytes] of outputs)if(process.argv.includes('--check')){if(await Bun.file(path).text()!==bytes)throw Error('Stale custody branch: '+path)}else await Bun.write(path,bytes);
console.log('Distinct custody-aware source branch exported; native qualification pending.');
