/** Original owner-emitted statement units for provisional installer construction. */
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {getPostgresqlNode,proposePostgresqlNodeEdit,exportPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
const modelPath='docs/helix/02-design/models/truss-layout-source-epoch-0.16.proposal.umf.json';
const exportPath='docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql';
const hash=(value:string|Uint8Array)=>new Bun.CryptoHasher('sha256').update(value).digest('hex');
const model=await Bun.file(modelPath).text(),document=readDocument(model,'json');
const originalExport=await Bun.file(exportPath).text();
const sourceManifestPath='packages/python/src/truss/_installation/manifest.json';
const sourceManifest=await Bun.file(sourceManifestPath).text(),sourceDefinition=JSON.parse(sourceManifest);
if(sourceDefinition.qualified!==false||sourceDefinition.executable!==false
 ||sourceDefinition.resources.find((r:any)=>r.role==='model')?.sha256!==hash(model)
 ||sourceDefinition.resources.find((r:any)=>r.role==='owner_export')?.sha256!==hash(originalExport))
 throw Error('Original development source definition correspondence required');
if(await exportPostgresqlSql(document,backend)!==originalExport)throw Error('Original complete owner export correspondence required');
const nodes=JSON.parse(renderTree(getPostgresqlNode(document,'/stmts')));
const membership:any={tables:[],sequences:[],indexes:[],routines:[],definitionObligations:[]};
const routineExecution=(f:any)=>{
 const fields:any={language:null,body:null,security:false,volatility:'v',parallel:'u',strict:false,leakproof:false,settings:[]};
 const seen=new Set<string>();
 for(const option of f.options??[]){
  const d=option.DefElem;if(seen.has(d.defname))throw Error('Duplicate routine execution option');seen.add(d.defname);
  if(d.defname==='language')fields.language=d.arg.String.sval;
  else if(d.defname==='as'){if(d.arg.List.items.length!==1)throw Error('Unselected multi-string body');fields.body=d.arg.List.items[0].String.sval;}
  else if(['security','strict','leakproof'].includes(d.defname))fields[d.defname]=d.arg.Boolean.boolval??false;
  else if(d.defname==='volatility'){fields.volatility=({volatile:'v',stable:'s',immutable:'i'} as any)[d.arg.String.sval];if(!fields.volatility)throw Error('Unselected volatility');}
  else if(d.defname==='parallel'){fields.parallel=({unsafe:'u',restricted:'r',safe:'s'} as any)[d.arg.String.sval];if(!fields.parallel)throw Error('Unselected parallel');}
  else if(d.defname==='set'){
   const v=d.arg.VariableSetStmt;if(v.kind!=='VAR_SET_VALUE'||v.name!=='search_path')throw Error('Unselected routine configuration');
   const names=v.args.map((a:any)=>a.A_Const.sval.sval);if(names.some((n:string)=>!['pg_catalog','pg_temp'].includes(n)))throw Error('Unselected routine path');
   fields.settings.push('search_path='+names.join(', '));
  }else throw Error('Unselected routine execution option '+d.defname);
 }
 if(f.sql_body||fields.language!=='plpgsql'||typeof fields.body!=='string')throw Error('Selected original PLpgSQL body required');
 return fields;
};
const sequenceParameters=(s:any)=>{
 const fields:any={type:'pg_catalog.int8',increment:'1',minimum:'1',maximum:'9223372036854775807',start:'1',cache:'1',cycle:false};
 const keys:any={increment:'increment',minvalue:'minimum',maxvalue:'maximum',start:'start',cache:'cache'};
 const seen=new Set<string>();
 for(const option of s.options??[]){const d=option.DefElem;if(seen.has(d.defname))throw Error('Duplicate sequence option');seen.add(d.defname);
  if(d.defname==='as'){const names=d.arg.TypeName.names.map((n:any)=>n.String.sval);if(names.join('.')!=='pg_catalog.int8')throw Error('Unselected sequence type');}
  else if(d.defname==='cycle')fields.cycle=d.arg.Boolean.boolval??false;
  else if(keys[d.defname]){const n=d.arg.Integer?.ival;if(n!==undefined&&!Number.isSafeInteger(n))throw Error('Exact AST integer required');const value=n===undefined?d.arg.Float?.fval:String(n);if(!/^[1-9][0-9]*$/.test(value)||BigInt(value)>9223372036854775807n)throw Error('Unselected sequence numeric token');fields[keys[d.defname]]=value;}
  else throw Error('Unselected sequence option '+d.defname);
 }
 if(!seen.has('start'))fields.start=fields.minimum;
 return fields;
};
const columnType=(c:any)=>{
 const names=c.typeName.names.map((n:any)=>n.String.sval);let type=names.length===1?'pg_catalog.'+names[0]:names.join('.');
 if(!['text','jsonb','int2','int4','int8','timestamptz','bool','bytea','bpchar','xid8','numeric'].some(n=>type==='pg_catalog.'+n)||c.typeName.setof)throw Error('Unselected original column type');
 let dimensions='0';if(c.typeName.arrayBounds){if(type!=='pg_catalog.int4'||c.typeName.arrayBounds.length!==1||c.typeName.arrayBounds[0].Integer?.ival!==-1)throw Error('Unselected original array form');type='pg_catalog._int4';dimensions='1';}
 let modifier='-1';if(c.typeName.typmods){if(type!=='pg_catalog.bpchar'||c.typeName.typmods.length!==1||c.typeName.typmods[0].A_Const?.ival?.ival!==1)throw Error('Unselected original type modifier');modifier='5';}
 const collatable=['pg_catalog.text','pg_catalog.bpchar'].includes(type);
 let collation=collatable?'pg_catalog.default':null;
 if(c.collClause){const names=c.collClause.collname.map((n:any)=>n.String.sval);if(!collatable||!['pg_catalog.C','C'].includes(names.join('.')))throw Error('Unselected original collation');collation='pg_catalog.C';}
 return {type,modifier,collation,dimensions};
};
const columnDefinition=(c:any)=>{
 const constraints=(c.constraints??[]).map((n:any)=>n.Constraint);
 for(const constraint of constraints)if(!['CONSTR_PRIMARY','CONSTR_NOTNULL','CONSTR_DEFAULT','CONSTR_CHECK','CONSTR_FOREIGN','CONSTR_GENERATED','CONSTR_UNIQUE','CONSTR_ATTR_DEFERRABLE','CONSTR_ATTR_DEFERRED'].includes(constraint.contype))throw Error('Unselected column constraint form');
 if(c.identity||c.generated)throw Error('Unselected column identity/generation field');
 return {...columnType(c),notNull:constraints.some((n:any)=>['CONSTR_NOTNULL','CONSTR_PRIMARY'].includes(n.contype)),
  generated:constraints.some((n:any)=>n.contype==='CONSTR_GENERATED')?'s':'',identity:'',hasDefault:constraints.some((n:any)=>['CONSTR_DEFAULT','CONSTR_GENERATED'].includes(n.contype))};
};
const requirePrimary=(table:any,constraint:any)=>{if(constraint.contype==='CONSTR_PRIMARY')for(const key of constraint.keys){const column=table.columns.find((c:any)=>c.name===key.String.sval);if(!column)throw Error('Original primary column absent');column.definition.notNull=true;}};
const tableMap=new Map<string,any>();
const namespace=(r:any)=>{if(r.schemaname!=='truss')throw Error('Original selected namespace required');return r.relname;};
for(const [position,wrapped] of nodes.entries()){
 const stmt=wrapped.stmt,kind=Object.keys(stmt)[0],pointer=`/stmts/${position}/stmt/${kind}`;
 if(kind==='CreateStmt'){
  const name=namespace(stmt.CreateStmt.relation),columns=[];
  for(const [i,e] of (stmt.CreateStmt.tableElts??[]).entries()){
   if(e.ColumnDef)columns.push({name:e.ColumnDef.colname,ordinal:String(columns.length+1),pointer:pointer+`/tableElts/${i}/ColumnDef`,definition:columnDefinition(e.ColumnDef)});
   else if(!e.Constraint)throw Error('Unknown table member form');
  }
  if(tableMap.has(name))throw Error('Duplicate original table');
  const table={name,kind:stmt.CreateStmt.partspec?'p':'r',pointer,columns};tableMap.set(name,table);membership.tables.push(table);
  for(const e of stmt.CreateStmt.tableElts??[])if(e.Constraint)requirePrimary(table,e.Constraint);
 }else if(kind==='AlterTableStmt'){
  const table=tableMap.get(namespace(stmt.AlterTableStmt.relation));if(!table)throw Error('Original alteration owner absent');
  for(const [i,c] of stmt.AlterTableStmt.cmds.entries()){
   const cmd=c.AlterTableCmd,source=pointer+`/cmds/${i}/AlterTableCmd`;
   if(cmd.subtype==='AT_AddColumn')table.columns.push({name:cmd.def.ColumnDef.colname,ordinal:String(table.columns.length+1),pointer:source+'/def/ColumnDef',definition:columnDefinition(cmd.def.ColumnDef)});
   else if(cmd.subtype==='AT_AlterColumnType'){const column=table.columns.find((c:any)=>c.name===cmd.name);if(!column)throw Error('Original altered column absent');Object.assign(column.definition,columnType(cmd.def.ColumnDef));column.typeSourcePointer=source;membership.definitionObligations.push({pointer:source,kind:cmd.subtype,unresolved:'type conversion execution semantics'});}
   else if(['AT_AddConstraint','AT_DropConstraint'].includes(cmd.subtype)){if(cmd.subtype==='AT_AddConstraint')requirePrimary(table,cmd.def.Constraint);membership.definitionObligations.push({pointer:source,kind:cmd.subtype});}
   else throw Error('Unknown original alteration membership');
  }
 }else if(kind==='CreateSeqStmt')membership.sequences.push({name:namespace(stmt.CreateSeqStmt.sequence),pointer,parameters:sequenceParameters(stmt.CreateSeqStmt)});
 else if(kind==='IndexStmt')membership.indexes.push({name:stmt.IndexStmt.idxname,table:namespace(stmt.IndexStmt.relation),pointer});
 else if(kind==='CreateFunctionStmt'){
  const f=stmt.CreateFunctionStmt,name=f.funcname.map((n:any)=>n.String.sval);if(name.length!==2||name[0]!=='truss')throw Error('Original routine namespace required');
  const inputs=(f.parameters??[]).filter((p:any)=>!['FUNC_PARAM_TABLE','FUNC_PARAM_OUT'].includes(p.FunctionParameter.mode)).map((p:any)=>{
   const names=p.FunctionParameter.argType.names.map((n:any)=>n.String.sval);return names.length===1?'pg_catalog.'+names[0]:names.join('.');});
  membership.routines.push({schema:name[0],name:name[1],inputs,kind:f.is_procedure?'p':'f',pointer,execution:routineExecution(f)});
 }else if(['CreateSchemaStmt','CommentStmt','InsertStmt','GrantStmt'].includes(kind))membership.definitionObligations.push({pointer,kind});
 else throw Error('Unknown original statement membership form');
}
for(const table of membership.tables)if(new Set(table.columns.map((c:any)=>c.name)).size!==table.columns.length)throw Error('Duplicate original column');
const statements=[];
for(const [position,node] of nodes.entries()){
 const one=proposePostgresqlNodeEdit(document,'/stmts',JSON.stringify([node])).document;
 const sql=await exportPostgresqlSql(one,backend);
 statements.push({position:String(position),sql,byteLength:Buffer.byteLength(sql),sha256:hash(sql)});
}
if(statements.map(s=>s.sql).join('; ')!==originalExport)throw Error('Ordered owner statement projection must reproduce the complete export');
const revision=Bun.spawnSync(['git','rev-parse','HEAD'],{cwd:'/Users/erik/Projects/umf'});
if(revision.exitCode!==0)throw Error('Committed owner revision required');
const sources:Record<string,string>={};
for(const path of [modelPath,exportPath,sourceManifestPath,'scripts/build-python-installation-statements.ts',
 '/Users/erik/Projects/umf/src/adapters/postgresql/index.ts','/Users/erik/Projects/umf/src/model/native-json.ts',
 '/Users/erik/Projects/umf/native/postgresql/runtime.ts'])sources[path]=hash(new Uint8Array(await Bun.file(path).arrayBuffer()));
const asset=JSON.stringify({nativeMajor:'16',interfaceVersion:'truss-provisional-installation-statements/0.1.0',
 scope:'original_owner_statement_units_rollback_only_construction',ownerRevision:Buffer.from(revision.stdout).toString().trim(),
 modelSha256:hash(model),ownerExportSha256:hash(originalExport),sources,statements,membership,
 completeInstalledProfile:false,installationReady:false},null,2)+'\n';
const path='packages/python/src/truss/_installation/statements.json';
await Bun.write(path,asset);
await Bun.write('packages/python/src/truss/_installation_statement_release.py',
 '"""Generated original construction statement pins; no installation authority."""\nSTATEMENTS_SHA256 = '+JSON.stringify(hash(asset))+'\nSOURCE_MANIFEST_SHA256 = '+JSON.stringify(hash(sourceManifest))+'\n');
console.log(JSON.stringify({statements:statements.length,bytes:Buffer.byteLength(asset),sha256:hash(asset)}));
