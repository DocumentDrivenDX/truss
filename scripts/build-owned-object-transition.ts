/** Prepare multi-object transition storage through UMF's existing native editor/exporter. */
import {backend} from '/Users/erik/.codex/worktrees/0e51/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/.codex/worktrees/0e51/umf/src/model/document';
import {importPostgresqlSql,exportPostgresqlSql,getPostgresqlNode,proposePostgresqlNodeEdit} from '/Users/erik/.codex/worktrees/0e51/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/.codex/worktrees/0e51/umf/src/model/native-json';
import {validateDocument} from '/Users/erik/.codex/worktrees/0e51/umf/src/validation/document';

const directory='docs/helix/02-design/models/';
const baselinePath=directory+'truss-object-transition-baseline-0.1.umf.json';
let baseline;
if(await Bun.file(baselinePath).exists())baseline=readDocument(await Bun.file(baselinePath).text(),'json');
else{
 const source=await Bun.file('packages/python/src/truss/_catalog_runtime/operations.sql').text();
 const start=source.indexOf('CREATE TABLE truss.runtime_object_transition (');
 if(start<0)throw Error('Original transition table required');
 baseline=await importPostgresqlSql(source.slice(start,source.indexOf(';',start)+1),backend,{id:'truss-object-transition-baseline-0.1'});
 await Bun.write(baselinePath,JSON.stringify(baseline)+'\n');
}
const originalNodes=JSON.parse(renderTree(getPostgresqlNode(baseline,'/stmts')));
if(originalNodes.length!==1)throw Error('Exactly the original transition table required');
const original=originalNodes[0].stmt.CreateStmt;
const constraintIndex=original.tableElts.findIndex((e:any)=>e.Constraint?.contype==='CONSTR_UNIQUE');
const constraint=original.tableElts[constraintIndex]?.Constraint;
if(JSON.stringify(constraint?.keys?.map((k:any)=>k.String.sval))!==JSON.stringify(['attempt_id','operation_index']))throw Error('Original single-object transition uniqueness required');
const replacement={...constraint,keys:['attempt_id','operation_index','object_id','type_id'].map(sval=>({String:{sval}}))};
const edited=proposePostgresqlNodeEdit(baseline,`/stmts/0/stmt/CreateStmt/tableElts/${constraintIndex}/Constraint`,JSON.stringify(replacement)).document;
edited.id='truss-owned-object-transition-storage-0.1';
const nativeBytes=JSON.stringify(edited)+'\n';
const ddl=await exportPostgresqlSql(edited,backend);
if(await exportPostgresqlSql(readDocument(nativeBytes,'json'),backend)!==ddl)throw Error('Saved model must generate identical SQL');
if(await exportPostgresqlSql(baseline,backend)===ddl)throw Error('Export must consume edited model rather than archived SQL');
const stmt=JSON.parse(renderTree(getPostgresqlNode(edited,'/stmts/0/stmt/CreateStmt')));
const module:any={id:'truss-owned-object-transition',namespace:'truss',elements:[]};
const ref=(element:string)=>({module:module.id,element});
const record:any={id:'runtime_object_transition',name:'runtime_object_transition',kind:'record',members:[],references:[],keys:[],extensions:{'truss.layout.native':{definition:stmt}}};
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
record.keys.push({id:'operation-object',name:'operation-object',fields:['attempt_id','operation_index','object_id','type_id'].map(c=>ref(record.id+'.'+c))});
// UUID keys are not a portable core-key claim. Preserve exact physical identity.
record.extensions['truss.layout.native'].physicalKeys=record.keys.filter((k:any)=>k.id==='operation-object');
record.keys=record.keys.filter((k:any)=>k.id!=='operation-object');
module.elements.push(record,{id:'runtime_object_attempt.id',name:'id',kind:'field',cardinality:'one',nullability:'required',extensions:{'truss.layout.native':{nativeType:'uuid',interpretation:'Original referenced attempt identifier; no portable UUID key asserted'}}},{id:'runtime_object_attempt',name:'runtime_object_attempt',kind:'record',members:[ref('runtime_object_attempt.id')],references:[{role:'member',...ref('runtime_object_attempt.id')}],extensions:{'truss.layout.native':{projection:'Referenced primary-key column; full original attempt remains in operations.sql'}}});
const core:any={umf:'0.8.0',id:'truss-owned-object-transition-core-0.1',vocabularies:{'truss.layout.native':{version:'0.1.0'}},modules:[module],extensions:{'truss.layout.native':{sourceModel:directory+'truss-owned-object-transition-storage-0.1.proposal.umf.json',scope:'Candidate multi-object transition uniqueness; core column/FK references and retained native keys. Not installed ownership or migration support.'}}};
const validation=validateDocument(core);
if(validation.diagnostics.some(d=>d.severity==='error'))throw Error(JSON.stringify(validation.diagnostics));
if(record.members.length!==10)throw Error('Complete original ten-column transition required');
await Bun.write(directory+'truss-owned-object-transition-storage-0.1.proposal.umf.json',nativeBytes);
await Bun.write(directory+'truss-owned-object-transition-core-0.1.proposal.umf.json',JSON.stringify(core)+'\n');
await Bun.write('docs/helix/04-build/owned-object-transition.generated.sql',ddl);
console.log(JSON.stringify({columns:record.members.length,unique:['attempt_id','operation_index','object_id','type_id'],fk:'runtime_object_attempt.id',valid:validation.valid,complete:validation.complete,ownerExport:true,installed:false}));
