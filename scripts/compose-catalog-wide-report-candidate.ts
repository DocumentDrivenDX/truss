/** Distinct bounded report-artifact profile; preserve all historical producers. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {getPostgresqlNode,proposePostgresqlNodeEdit,importPostgresqlSql,exportPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const profileRoot='packages/python/src/truss/_profiles';
const revision=await Bun.file(`${profileRoot}/catalog-revision-composition-candidate.json`).json();
revision.identity='truss-administrative-catalog-revision-wide-report-composition';revision.version='0.2.0-candidate';
revision.resources.maxOriginalReportBytes='786432';revision.resources.maxArtifactBase64Utf8Bytes='1048576';
revision.resources.largeScalarScope='only /report/bytesBase64; native base64 of the original report; other keys and strings retain65536 byte ceiling';
const revisionPath=`${profileRoot}/catalog-revision-wide-report-composition-candidate.json`;
const revisionBytes=JSON.stringify(revision,null,2)+'\n';await Bun.write(revisionPath,revisionBytes);
const composition=await Bun.file(`${profileRoot}/catalog-report-composition-candidate.json`).json();
composition.identity='truss-administrative-wide-report-composition';composition.version='0.2.0-candidate';
composition.revisionEncoder={path:revisionPath,sha256:hash(revisionBytes)};
const compositionPath=`${profileRoot}/catalog-report-wide-composition-candidate.json`;
const compositionBytes=JSON.stringify(composition,null,2)+'\n';await Bun.write(compositionPath,compositionBytes);
const registration=await Bun.file(`${profileRoot}/catalog-revision-registration-candidate.json`).json();
registration.version='0.3.0-wide-report-candidate';registration.payloadProfile={path:revisionPath,sha256:hash(revisionBytes)};
registration.reportComposition={path:compositionPath,sha256:hash(compositionBytes)};
const registrationPath=`${profileRoot}/catalog-revision-wide-registration-candidate.json`;
const registrationBytes=JSON.stringify(registration,null,2)+'\n';await Bun.write(registrationPath,registrationBytes);
const inputs:any[]=[];
async function emit(source:string,target:string,oldName:string,newName:string,patch:(body:string)=>string){
 const raw=await Bun.file(source).text();const original=await importPostgresqlSql(raw,backend,{id:'original-'+oldName});
 const nodes=JSON.parse(renderTree(getPostgresqlNode(original,'/stmts')));
 const candidates=nodes.filter((n:any)=>n.stmt?.CreateFunctionStmt?.funcname.at(-1)?.String.sval===oldName);
 if(candidates.length!==1)throw Error('One original function required');
 const node=structuredClone(candidates[0]),fn=node.stmt.CreateFunctionStmt;
 fn.funcname.at(-1).String.sval=newName;
 const body=fn.options.find((o:any)=>o.DefElem.defname==='as').DefElem.arg.List.items[0].String;
 body.sval=patch(body.sval);
 const selected=proposePostgresqlNodeEdit(original,'/stmts',JSON.stringify([node])).document;
 const sql=await exportPostgresqlSql(selected,backend);
 const revoked=await importPostgresqlSql(sql+`; REVOKE ALL ON FUNCTION truss.${newName}(text,text,text,text,bytea,bytea,bytea) FROM PUBLIC`,backend,{id:'candidate-'+newName});
 const model=JSON.stringify(revoked)+'\n',finalSql=await exportPostgresqlSql(revoked,backend);
 if(await exportPostgresqlSql(readDocument(model,'json'),backend)!==finalSql)throw Error('Reload/export correspondence required');
 await Bun.write(target+'.umf.json',model);await Bun.write(target+'.sql',finalSql);
 inputs.push({source,sourceSha256:hash(raw),target,targetModelSha256:hash(model),targetSqlSha256:hash(finalSql)});
}
function exact(body:string,from:string,to:string){if(!body.includes(from))throw Error('Original source anchor absent '+from);return body.split(from).join(to)}
await emit('packages/postgresql/native/catalog-report/report-write-candidate.sql','packages/postgresql/native/catalog-report/report-write-wide-candidate','runtime_write_catalog_report_candidate','runtime_write_catalog_report_wide_candidate',body=>{
 body=exact(body,'packages/python/src/truss/_profiles/catalog-report-composition-candidate.json',compositionPath);
 body=exact(body,'3f5f83a5b827451bdf29a018eca85b0bdac3811a37ec8efcbadafc1a79fd10fe',hash(compositionBytes));
 body=exact(body,'packages/python/src/truss/_profiles/catalog-revision-composition-candidate.json',revisionPath);
 body=exact(body,'6e22d1e2393935f8d15fcade4ca5ac22a6f81b3a0ff47836d24741068d215e57',hash(revisionBytes));
 body=exact(body,'((octet_length(original_report)::bigint+2)/3)*4>65536','((octet_length(original_report)::bigint+2)/3)*4>1048576');
 return exact(body,'truss.runtime_canonical_tree_bytes(revision_tree)','truss.runtime_revision_report_tree_bytes_wide_candidate(revision_tree,original_report)');
});
await emit('packages/postgresql/native/catalog-report/revision-registration-candidate.sql','packages/postgresql/native/catalog-report/revision-registration-wide-candidate','runtime_write_catalog_report_and_register_revision_candidate','runtime_write_report_register_revision_wide_candidate',body=>{
 body=exact(body,'packages/python/src/truss/_profiles/catalog-revision-registration-candidate.json',registrationPath);
 body=exact(body,'a32febdea06ee57405d856038ede3b503430a4f823226e0dfa65b072fae2f725',hash(registrationBytes));
 return exact(body,'truss.runtime_write_catalog_report_candidate(','truss.runtime_write_catalog_report_wide_candidate(');
});
await Bun.write('packages/postgresql/native/catalog-report/wide-report-source-manifest.json',JSON.stringify({scope:'selected owner AST function composition; native qualification separate',ownerCommit:new TextDecoder().decode(Bun.spawnSync(['git','-C','/Users/erik/Projects/umf','rev-parse','HEAD']).stdout).trim(),inputs,profiles:[{path:revisionPath,sha256:hash(revisionBytes)},{path:compositionPath,sha256:hash(compositionBytes)},{path:registrationPath,sha256:hash(registrationBytes)}]},null,2)+'\n');
console.log(JSON.stringify({functions:inputs.length}));
