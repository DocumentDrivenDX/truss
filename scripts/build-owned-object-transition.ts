/** Prepare multi-object transition storage through UMF's existing native editor/exporter. */
import {backend} from '/Users/erik/.codex/worktrees/0e51/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/.codex/worktrees/0e51/umf/src/model/document';
import {importPostgresqlSql,exportPostgresqlSql,getPostgresqlNode,proposePostgresqlNodeEdit} from '/Users/erik/.codex/worktrees/0e51/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/.codex/worktrees/0e51/umf/src/model/native-json';
import {validateDocument} from '/Users/erik/.codex/worktrees/0e51/umf/src/validation/document';

const directory='docs/helix/02-design/models/';
const baselinePath=directory+'truss-owned-transition-baseline-0.1.umf.json';
let baseline;
if(await Bun.file(baselinePath).exists())baseline=readDocument(await Bun.file(baselinePath).text(),'json');
else{
 const source=await Bun.file('packages/python/src/truss/_catalog_runtime/operations.sql').text();
 const statements=['runtime_object_transition','runtime_edge_transition'].map(name=>{
  const start=source.indexOf('CREATE TABLE truss.'+name+' (');
  if(start<0)throw Error('Original transition table required: '+name);
  return source.slice(start,source.indexOf(';',start)+1);
 });
 baseline=await importPostgresqlSql(statements.join('\n'),backend,{id:'truss-owned-transition-baseline-0.1'});
 await Bun.write(baselinePath,JSON.stringify(baseline)+'\n');
}
const originalNodes=JSON.parse(renderTree(getPostgresqlNode(baseline,'/stmts')));
if(originalNodes.length!==2)throw Error('Both original transition tables required');
let edited=baseline;
for(const [index,originalNode] of originalNodes.entries()){
 const original=originalNode.stmt.CreateStmt;
 const name=original.relation.relname;
 const identity=name==='runtime_object_transition'?['object_id','type_id']:name==='runtime_edge_transition'?['edge_id','rel_type_id']:null;
 if(!identity)throw Error('Exact original transition table required');
 const constraintIndex=original.tableElts.findIndex((e:any)=>e.Constraint?.contype==='CONSTR_UNIQUE');
 const constraint=original.tableElts[constraintIndex]?.Constraint;
 if(JSON.stringify(constraint?.keys?.map((k:any)=>k.String.sval))!==JSON.stringify(['attempt_id','operation_index']))throw Error('Original single-entity transition uniqueness required');
 const replacement={...constraint,keys:['attempt_id','operation_index',...identity].map(sval=>({String:{sval}}))};
 edited=proposePostgresqlNodeEdit(edited,`/stmts/${index}/stmt/CreateStmt/tableElts/${constraintIndex}/Constraint`,JSON.stringify(replacement)).document;
}
// Retain endpoint root provenance after later moves/deletion; legacy rows stay SQL NULL.
const columnModel=await importPostgresqlSql('ALTER TABLE truss.runtime_edge_transition ADD COLUMN endpoint_ownership jsonb;',backend,{id:'owned-endpoint-context-column'});
const columnCommand=JSON.parse(renderTree(getPostgresqlNode(columnModel,'/stmts/0/stmt/AlterTableStmt/cmds/0')));
const edgeElements=JSON.parse(renderTree(getPostgresqlNode(edited,'/stmts/1/stmt/CreateStmt/tableElts')));
edgeElements.push({ColumnDef:columnCommand.AlterTableCmd.def.ColumnDef});
edited=proposePostgresqlNodeEdit(edited,'/stmts/1/stmt/CreateStmt/tableElts',JSON.stringify(edgeElements)).document;
edited.id='truss-owned-object-transition-storage-0.1';
const nativeBytes=JSON.stringify(edited)+'\n';
const ddl=await exportPostgresqlSql(edited,backend);
if(await exportPostgresqlSql(readDocument(nativeBytes,'json'),backend)!==ddl)throw Error('Saved model must generate identical SQL');
if(await exportPostgresqlSql(baseline,backend)===ddl)throw Error('Export must consume edited model rather than archived SQL');
const statements=JSON.parse(renderTree(getPostgresqlNode(edited,'/stmts'))).map((n:any)=>n.stmt.CreateStmt);
// Migration statements are edited from a native baseline using the same constraints.
const upgradeSource=statements.map((stmt:any)=>`ALTER TABLE truss.${stmt.relation.relname} DROP CONSTRAINT ${stmt.relation.relname}_attempt_id_operation_index_key, ADD UNIQUE(attempt_id,operation_index);`).join('\n');
let upgrade=await importPostgresqlSql(upgradeSource,backend,{id:'truss-owned-transition-upgrade-0.1'});
for(const [index,stmt] of statements.entries()){
 const constraint=stmt.tableElts.find((e:any)=>e.Constraint?.contype==='CONSTR_UNIQUE').Constraint;
 upgrade=proposePostgresqlNodeEdit(upgrade,`/stmts/${index}/stmt/AlterTableStmt/cmds/1/AlterTableCmd/def/Constraint`,JSON.stringify(constraint)).document;
}
const edgeCommands=JSON.parse(renderTree(getPostgresqlNode(upgrade,'/stmts/1/stmt/AlterTableStmt/cmds')));
edgeCommands.push(columnCommand);
upgrade=proposePostgresqlNodeEdit(upgrade,'/stmts/1/stmt/AlterTableStmt/cmds',JSON.stringify(edgeCommands)).document;
const upgradeBytes=JSON.stringify(upgrade)+'\n';
const upgradeDdl=await exportPostgresqlSql(upgrade,backend);
if(await exportPostgresqlSql(readDocument(upgradeBytes,'json'),backend)!==upgradeDdl)throw Error('Saved upgrade model must generate identical SQL');
await Bun.write(directory+'truss-owned-transition-upgrade-0.1.proposal.umf.json',upgradeBytes);
await Bun.write('docs/helix/04-build/owned-transition-upgrade.generated.sql',upgradeDdl);
const module:any={id:'truss-owned-object-transition',namespace:'truss',elements:[]};
const ref=(element:string)=>({module:module.id,element});
let columnCount=0;
for(const stmt of statements){
const record:any={id:stmt.relation.relname,name:stmt.relation.relname,kind:'record',members:[],references:[],keys:[],extensions:{'truss.layout.native':{definition:stmt}}};
for(const entry of stmt.tableElts){
 const c=entry.ColumnDef;if(!c)continue;
 const id=record.id+'.'+c.colname,nativeType=c.typeName.names.at(-1).String.sval;
 const required=(c.constraints??[]).some((w:any)=>['CONSTR_NOTNULL','CONSTR_PRIMARY'].includes(w.Constraint.contype));
 const field:any={id,name:c.colname,kind:'field',cardinality:'one',nullability:required?'required':'unspecified',extensions:{'truss.layout.native':{definition:c,nativeType,interpretation:'Native constraints/NULL/defaults and exact JSONB, xid8 and UUID semantics remain native meaning'}}};
 if(['int8','int4'].includes(nativeType))field.scalarType='integer';
 record.members.push(ref(id));record.references.push({role:'member',...ref(id)});
 for(const w of c.constraints??[]){
  if(w.Constraint.contype==='CONSTR_PRIMARY')record.keys.push({id:'primary',name:'primary',primary:true,fields:[ref(id)]});
  if(w.Constraint.contype==='CONSTR_FOREIGN'){
   field.references=[{role:'physical-fk:attempt',...ref('runtime_object_attempt.id')}];
   field.extensions['truss.layout.native'].foreignKey=w.Constraint;
   record.references.push({role:'physical-fk:attempt',...ref('runtime_object_attempt')});
  }
 }
 module.elements.push(field);
}
record.keys.push({id:'operation-object',name:'operation-object',fields:['attempt_id','operation_index',...(record.id==='runtime_object_transition'?['object_id','type_id']:['edge_id','rel_type_id'])].map(c=>ref(record.id+'.'+c))});
// UUID keys are not a portable core-key claim. Preserve exact physical identity.
record.extensions['truss.layout.native'].physicalKeys=record.keys.filter((k:any)=>k.id==='operation-object');
record.keys=record.keys.filter((k:any)=>k.id!=='operation-object');
columnCount+=record.members.length;
module.elements.push(record);
}
module.elements.push({id:'runtime_object_attempt.id',name:'id',kind:'field',cardinality:'one',nullability:'required',extensions:{'truss.layout.native':{nativeType:'uuid',interpretation:'Original referenced attempt identifier; no portable UUID key asserted'}}},{id:'runtime_object_attempt',name:'runtime_object_attempt',kind:'record',members:[ref('runtime_object_attempt.id')],references:[{role:'member',...ref('runtime_object_attempt.id')}],extensions:{'truss.layout.native':{projection:'Referenced primary-key column; full original attempt remains in operations.sql'}}});
const core:any={umf:'0.8.0',id:'truss-owned-object-transition-core-0.1',vocabularies:{'truss.layout.native':{version:'0.1.0'}},modules:[module],extensions:{'truss.layout.native':{sourceModel:directory+'truss-owned-object-transition-storage-0.1.proposal.umf.json',scope:'Candidate multi-object/multi-edge transitions and retained endpoint root contexts; core column/FK references and retained native keys. Not installed ownership or migration support.'}}};
const validation=validateDocument(core);
if(validation.diagnostics.some(d=>d.severity==='error'))throw Error(JSON.stringify(validation.diagnostics));
if(columnCount!==24)throw Error('All23 original transition columns plus endpoint ownership context required');
await Bun.write(directory+'truss-owned-object-transition-storage-0.1.proposal.umf.json',nativeBytes);
await Bun.write(directory+'truss-owned-object-transition-core-0.1.proposal.umf.json',JSON.stringify(core)+'\n');
await Bun.write('docs/helix/04-build/owned-object-transition.generated.sql',ddl);
console.log(JSON.stringify({columns:columnCount,unique:{object:['attempt_id','operation_index','object_id','type_id'],edge:['attempt_id','operation_index','edge_id','rel_type_id']},fk:'runtime_object_attempt.id',valid:validation.valid,complete:validation.complete,ownerExport:true,installed:false}));
