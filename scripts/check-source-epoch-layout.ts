/** Full candidate DDL installation in an isolated rollback-only namespace. */
import {SQL} from 'bun';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {getPostgresqlNode} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const url=process.env.TRUSS_OPERATION_TEST_URL;
if(!url?.startsWith('postgres://postgres@127.0.0.1:15434/'))throw Error('Owned fixture URL required');
const sql=new SQL(url,{max:1});const namespace='truss_epoch_layout_component';
let inventory:unknown,version='';
const model='docs/helix/02-design/models/truss-layout-source-epoch-0.16.proposal.umf.json';
const nodes=JSON.parse(renderTree(getPostgresqlNode(readDocument(await Bun.file(model).text(),'json'),'/stmts')));
const declaredColumns=new Set<string>(),declaredIndexes=new Set<string>(),declaredSequences=new Set<string>(),declaredRoutines=new Set<string>();
for(const wrapped of nodes){
 const s=wrapped.stmt;
 if(s.CreateStmt)for(const c of s.CreateStmt.tableElts??[])if(c.ColumnDef)declaredColumns.add(s.CreateStmt.relation.relname+'\0'+c.ColumnDef.colname);
 if(s.AlterTableStmt)for(const c of s.AlterTableStmt.cmds??[])if(c.AlterTableCmd.subtype==='AT_AddColumn')declaredColumns.add(s.AlterTableStmt.relation.relname+'\0'+c.AlterTableCmd.def.ColumnDef.colname);
 if(s.IndexStmt)declaredIndexes.add(s.IndexStmt.relation.relname+'\0'+s.IndexStmt.idxname);
 if(s.CreateSeqStmt)declaredSequences.add(s.CreateSeqStmt.sequence.relname);
 if(s.CreateFunctionStmt)declaredRoutines.add(s.CreateFunctionStmt.funcname.at(-1).String.sval);
}
function compareKeys(expected:Set<string>,observed:string[],kind:string){
 if(observed.length!==new Set(observed).size||expected.size!==observed.length||observed.some(k=>!expected.has(k)))throw Error('Complete native '+kind+' identity mismatch');
}
try {
 await sql.begin(async tx=>{
  const exists=await tx`SELECT to_regnamespace(${namespace})::text AS n`;
  if(exists[0].n!==null)throw Error('Component namespace exists; refuse overwrite');
  const ddl=await Bun.file('docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').text();
  // Explicit test-only namespace substitution; original bytes remain retained.
  await tx.unsafe(ddl.replace(/\btruss\b/g,namespace));
  const tables=await tx`SELECT c.relname AS name,count(a.attnum)::text AS columns FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace LEFT JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped WHERE n.nspname=${namespace} AND c.relkind IN ('r','p') GROUP BY c.relname ORDER BY c.relname COLLATE pg_catalog."C"`;
  if(tables.length!==48||tables.reduce((n:bigint,t:{columns:string})=>n+BigInt(t.columns),0n)!==454n)throw Error('Complete installed table/column count mismatch');
  const epoch=await tx`SELECT c.relname,a.attname,pg_catalog.format_type(a.atttypid,a.atttypmod) AS type,a.attnotnull,a.attgenerated FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped WHERE n.nspname=${namespace} AND c.relname IN ('source_epoch_registry','source_epoch_current') ORDER BY c.relname COLLATE pg_catalog."C",a.attnum`;
  const fks=await tx`SELECT c.relname,con.conname,pg_catalog.pg_get_constraintdef(con.oid) AS definition FROM pg_catalog.pg_constraint con JOIN pg_catalog.pg_class c ON c.oid=con.conrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=${namespace} AND c.relname IN ('source_epoch_registry','source_epoch_current') AND con.contype='f' ORDER BY c.relname COLLATE pg_catalog."C",con.conname COLLATE pg_catalog."C"`;
  if(epoch.length!==11||fks.length!==3)throw Error('Epoch columns/FKs mismatch');
  const columns=await tx`SELECT c.relname AS relation,a.attname AS name,a.attnum::text AS ordinal,pg_catalog.format_type(a.atttypid,a.atttypmod) AS type,a.atttypid::text AS type_oid,a.atttypmod::text AS type_modifier,a.attnotnull AS not_null,a.attgenerated AS generated,a.attidentity AS identity,a.attacl::text AS acl,cn.nspname AS collation_schema,co.collname AS collation_name,pg_catalog.pg_get_expr(ad.adbin,ad.adrelid) AS default_expression FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped LEFT JOIN pg_catalog.pg_attrdef ad ON ad.adrelid=c.oid AND ad.adnum=a.attnum LEFT JOIN pg_catalog.pg_collation co ON co.oid=a.attcollation LEFT JOIN pg_catalog.pg_namespace cn ON cn.oid=co.collnamespace WHERE n.nspname=${namespace} AND c.relkind IN ('r','p') ORDER BY c.relname COLLATE pg_catalog."C",a.attnum`;
  compareKeys(declaredColumns,columns.map((c:{relation:string;name:string})=>c.relation+'\0'+c.name),'column');
  const constraints=await tx`SELECT c.relname AS relation,con.conname AS name,con.contype AS kind,con.convalidated AS validated,con.condeferrable AS deferrable,con.condeferred AS initially_deferred,con.conkey::text AS columns,con.confkey::text AS target_columns,con.confupdtype AS update_action,con.confdeltype AS delete_action,pg_catalog.pg_get_constraintdef(con.oid) AS definition FROM pg_catalog.pg_constraint con JOIN pg_catalog.pg_class c ON c.oid=con.conrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=${namespace} ORDER BY c.relname COLLATE pg_catalog."C",con.conname COLLATE pg_catalog."C"`;
  const indexes=await tx`SELECT t.relname AS relation,c.relname AS name,i.indisunique AS unique_index,i.indisprimary AS primary_index,i.indisvalid AS valid,i.indisready AS ready,i.indislive AS live,i.indnullsnotdistinct AS nulls_not_distinct,i.indkey::text AS columns,i.indcollation::text AS collations,i.indclass::text AS operator_classes,pg_catalog.pg_get_indexdef(c.oid) AS definition FROM pg_catalog.pg_index i JOIN pg_catalog.pg_class c ON c.oid=i.indexrelid JOIN pg_catalog.pg_class t ON t.oid=i.indrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=${namespace} ORDER BY t.relname COLLATE pg_catalog."C",c.relname COLLATE pg_catalog."C"`;
  compareKeys(declaredIndexes,indexes.map((i:{relation:string;name:string})=>i.relation+'\0'+i.name).filter((k:string)=>declaredIndexes.has(k)),'explicit index');
  const sequences=await tx`SELECT c.relname AS name,pg_catalog.format_type(s.seqtypid,-1) AS type,s.seqstart::text AS start,s.seqincrement::text AS increment,s.seqmax::text AS maximum,s.seqmin::text AS minimum,s.seqcache::text AS cache,s.seqcycle AS cycle FROM pg_catalog.pg_sequence s JOIN pg_catalog.pg_class c ON c.oid=s.seqrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=${namespace} ORDER BY c.relname COLLATE pg_catalog."C"`;
  compareKeys(declaredSequences,sequences.map((s:{name:string})=>s.name),'sequence');
  const routines=await tx`SELECT p.proname AS name,pg_catalog.pg_get_function_identity_arguments(p.oid) AS arguments,pg_catalog.pg_get_function_result(p.oid) AS result,p.prosecdef AS security_definer,p.provolatile AS volatility,p.proparallel AS parallel,p.proconfig::text AS settings,p.proacl::text AS acl,r.rolname AS owner,l.lanname AS language,pg_catalog.pg_get_functiondef(p.oid) AS definition FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace JOIN pg_catalog.pg_roles r ON r.oid=p.proowner JOIN pg_catalog.pg_language l ON l.oid=p.prolang WHERE n.nspname=${namespace} ORDER BY p.proname COLLATE pg_catalog."C",pg_catalog.pg_get_function_identity_arguments(p.oid) COLLATE pg_catalog."C"`;
  compareKeys(declaredRoutines,routines.map((p:{name:string})=>p.name),'routine name');
  const triggers=await tx`SELECT c.relname AS relation,t.tgname AS name,t.tgisinternal AS internal,t.tgenabled AS enabled,fn.nspname AS function_schema,p.proname AS function_name,pg_catalog.pg_get_function_identity_arguments(p.oid) AS function_arguments,t.tgconstraint::text AS constraint_oid,pg_catalog.pg_get_triggerdef(t.oid) AS definition FROM pg_catalog.pg_trigger t JOIN pg_catalog.pg_class c ON c.oid=t.tgrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_proc p ON p.oid=t.tgfoid JOIN pg_catalog.pg_namespace fn ON fn.oid=p.pronamespace WHERE n.nspname=${namespace} ORDER BY c.relname COLLATE pg_catalog."C",t.tgname COLLATE pg_catalog."C"`;
  const policies=await tx`SELECT c.relname AS relation,p.polname AS name,p.polcmd AS command,p.polpermissive AS permissive,p.polroles::text AS roles,pg_catalog.pg_get_expr(p.polqual,p.polrelid) AS using_expression,pg_catalog.pg_get_expr(p.polwithcheck,p.polrelid) AS check_expression FROM pg_catalog.pg_policy p JOIN pg_catalog.pg_class c ON c.oid=p.polrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=${namespace} ORDER BY c.relname COLLATE pg_catalog."C",p.polname COLLATE pg_catalog."C"`;
  const relationPrivileges=await tx`SELECT c.relname AS name,c.relkind AS kind,r.rolname AS owner,c.relacl::text AS acl,c.relrowsecurity AS row_security,c.relforcerowsecurity AS forced_row_security FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_roles r ON r.oid=c.relowner WHERE n.nspname=${namespace} ORDER BY c.relname COLLATE pg_catalog."C"`;
  const namespacePrivilege=await tx`SELECT n.nspname AS name,r.rolname AS owner,n.nspacl::text AS acl,pg_catalog.obj_description(n.oid,'pg_namespace') AS comment FROM pg_catalog.pg_namespace n JOIN pg_catalog.pg_roles r ON r.oid=n.nspowner WHERE n.nspname=${namespace}`;
  await tx.unsafe('SAVEPOINT source_identity_control');
  const probe=columns.find((c:{relation:string})=>c.relation==='setting');if(!probe)throw Error('Original setting column absent');
  const quoted=(s:string)=>'"'+s.replaceAll('"','""')+'"';
  await tx.unsafe('ALTER TABLE '+quoted(namespace)+'.'+quoted(probe.relation)+' RENAME COLUMN '+quoted(probe.name)+' TO "__truss_substituted_column"');
  const changed=await tx`SELECT c.relname AS relation,a.attname AS name FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped WHERE n.nspname=${namespace} AND c.relkind IN ('r','p')`;
  let substitutedRefused=false;try{compareKeys(declaredColumns,changed.map((c:{relation:string;name:string})=>c.relation+'\0'+c.name),'column')}catch(e){substitutedRefused=(e as Error).message==='Complete native column identity mismatch'}
  if(changed.length!==454||!substitutedRefused)throw Error('Same-count native column substitution not refused');
  await tx.unsafe('ROLLBACK TO SAVEPOINT source_identity_control');await tx.unsafe('RELEASE SAVEPOINT source_identity_control');
  const restored=await tx`SELECT c.relname AS relation,a.attname AS name FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped WHERE n.nspname=${namespace} AND c.relkind IN ('r','p')`;
  compareKeys(declaredColumns,restored.map((c:{relation:string;name:string})=>c.relation+'\0'+c.name),'column');
  inventory={tables,tableCount:tables.length,columnCount:454,columns,constraints,indexes,sequences,routines,triggers,policies,relationPrivileges,namespacePrivilege,epochColumns:epoch,epochForeignKeys:fks,sourceCorrespondence:{allColumnNames:true,allExplicitIndexNames:true,allSequenceNames:true,allRoutineNames:true,sameCountNativeColumnSubstitutionRefused:true,rollbackRestoresSourceColumnNames:true,semanticDefinitionsQualified:false},counts:{constraints:constraints.length,indexes:indexes.length,sequences:sequences.length,routines:routines.length,internalTriggers:triggers.filter((t:{internal:boolean})=>t.internal).length,protectedUserTriggers:triggers.filter((t:{internal:boolean})=>!t.internal).length,policies:policies.length}};
  version=(await tx`SELECT version() AS version`)[0].version;
  throw Error('ROLLBACK_LAYOUT_COMPONENT');
 }).catch(e=>{if(e.message!=='ROLLBACK_LAYOUT_COMPONENT')throw e;});
 const after=await sql`SELECT to_regnamespace(${namespace})::text AS n`;
 if(after[0].n!==null)throw Error('Rollback leaked candidate namespace');
 const sources:Record<string,string>={};for(const path of ['scripts/check-source-epoch-layout.ts','docs/helix/02-design/models/truss-layout-source-epoch-0.16.proposal.umf.json','docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql'])sources[path]=new Bun.CryptoHasher('sha256').update(await Bun.file(path).arrayBuffer()).digest('hex');
 await Bun.write('docs/helix/04-build/evidence/design-audit/source-epoch-layout-native.json',JSON.stringify({database:version,sources,inventory,rollbackNamespaceAbsent:true,scope:'Complete generated candidate DDL in explicitly substituted rollback-only namespace. All source column/explicit-index/sequence/routine names correspond; native definitions, constraints, triggers, policies and direct ACLs observed. No complete semantic parity, effective-privilege/transitive callable closure, protected installer or deployment adoption.',qualified:false},null,2)+'\n');console.log(JSON.stringify({tables:48,columns:454,inventory:(inventory as any).counts,rollbackNamespaceAbsent:true}));
}finally{await sql.close();}
