/** Capture the registration-owned transition through UMF, retaining native meaning. */
import {backend} from '/Users/erik/.codex/worktrees/0e51/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/.codex/worktrees/0e51/umf/src/model/document';
import {importPostgresqlSql,exportPostgresqlSql,getPostgresqlNode} from '/Users/erik/.codex/worktrees/0e51/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/.codex/worktrees/0e51/umf/src/model/native-json';
import {validateDocument} from '/Users/erik/.codex/worktrees/0e51/umf/src/validation/document';

const base='packages/python/src/truss/_catalog_runtime/';
const source=await Bun.file(base+'catalog-rebind.sql').text();
const boundary=source.indexOf('-- Planned basis');
if(boundary<0)throw Error('Original storage boundary required');
const native=await importPostgresqlSql(source.slice(0,boundary),backend,{id:'truss-catalog-rebind-storage-0.1'});
const nativeBytes=JSON.stringify(native)+'\n';
const ddl=await exportPostgresqlSql(native,backend);
const reloadedDdl=await exportPostgresqlSql(readDocument(nativeBytes,'json'),backend);
if(reloadedDdl!==ddl)throw Error('Saved-model export changed original imported AST meaning');
const nodes=JSON.parse(renderTree(getPostgresqlNode(native,'/stmts')));
const transition=nodes.find((n:any)=>n.stmt?.CreateStmt)?.stmt.CreateStmt;
if(transition?.relation.relname!=='runtime_catalog_rebind_transition')throw Error('Exact transition table required');
const paths={native:'docs/helix/02-design/models/truss-catalog-rebind-storage-0.1.proposal.umf.json',
 core:'docs/helix/02-design/models/truss-catalog-rebind-core-0.1.proposal.umf.json',
 ddl:'docs/helix/04-build/evidence/catalog-rebind-storage-0.1.owner-export.sql',
 receipt:'docs/helix/04-build/evidence/catalog-rebind-storage-0.1.json'};
const hash=(value:string)=>new Bun.CryptoHasher('sha256').update(value).digest('hex');
const module:any={id:'truss-catalog-rebind',namespace:'truss',elements:[],relationships:[]};
const ref=(element:string)=>({module:module.id,element});
const declarations:any[]=[];
const parentSources:any[]=[];
for(const name of ['runtime.sql','layout.sql']){
 const originalBytes=await Bun.file(base+name).text();
 parentSources.push({path:base+name,sha256:hash(originalBytes)});
 const original=await importPostgresqlSql(originalBytes,backend,{id:'rebind-parent-'+name});
 declarations.push(...JSON.parse(renderTree(getPostgresqlNode(original,'/stmts'))).filter((n:any)=>n.stmt?.CreateStmt));
}
const parents=[['catalog_registration_request','registration_id'],['schema_rev','rev']] as const;
const project=(stmt:any,selected?:string)=>{
 const name=stmt.relation.relname;
 const record:any={id:name,name,kind:'record',members:[],references:[],keys:[],extensions:{'truss.layout.native':{projection:selected?'Referenced primary-key column only; other columns remain in original source':'Complete transition column inventory',definition:stmt}}};
 for(const [columnIndex,entry] of stmt.tableElts.entries()){
  const c=entry.ColumnDef;if(!c||selected&&c.colname!==selected)continue;
  const id=name+'.'+c.colname,type=c.typeName.names.at(-1).String.sval;
  const required=(c.constraints??[]).some((n:any)=>['CONSTR_NOTNULL','CONSTR_PRIMARY'].includes(n.Constraint.contype));
  const scalarType=({int8:'integer',int4:'integer'} as Record<string,string>)[type];
  const field:any={id,name:c.colname,kind:'field',cardinality:'one',nullability:required?'required':'unspecified',extensions:{'truss.layout.native':{definition:c,nativeType:type,...(name==='runtime_catalog_rebind_transition'?{sourceModel:paths.native,sourcePointer:'/stmts/'+nodes.findIndex((n:any)=>n.stmt?.CreateStmt===stmt)+'/stmt/CreateStmt/tableElts/'+columnIndex+'/ColumnDef'}:{}),interpretation:'Native constraints, SQL NULL, defaults and equality retained; no portable UUID/xid8/oid/JSONB semantics asserted'}}};
  if(scalarType)field.scalarType=scalarType;
  module.elements.push(field);record.members.push(ref(id));record.references.push({role:'member',...ref(id)});
  for(const n of c.constraints??[])if(n.Constraint.contype==='CONSTR_PRIMARY')record.keys.push({id:'primary',name:'primary',primary:true,fields:[ref(id)]});
 }
 module.elements.push(record);return record;
};
project(transition);
for(const [name,column] of parents){
 const stmt=declarations.find((n:any)=>n.stmt.CreateStmt.relation.relname===name)?.stmt.CreateStmt;
 if(!stmt)throw Error('Original parent declaration absent: '+name);
 const record=project(stmt,column);if(record.keys.length!==1)throw Error('Original referenced primary key required');
 if(name==='catalog_registration_request'){record.extensions['truss.layout.native'].physicalKeys=record.keys;delete record.keys;}
}
const foreign:any[]=[];
for(const entry of transition.tableElts){
 const column=entry.ColumnDef;
 for(const wrapper of column?.constraints??[]){
  const c=wrapper.Constraint;if(c.contype!=='CONSTR_FOREIGN')continue;
  foreign.push({definition:c,source:[column.colname],target:c.pk_attrs.map((k:any)=>k.String.sval)});
 }
}
for(const {definition:c,source,target} of foreign){
 const id='rebind-'+source.join('-');
 if(c.pktable.relname==='catalog_registration_request'){
  const record=module.elements.find((e:any)=>e.id===transition.relation.relname);
  record.references.push({role:'physical-fk:'+id,...ref(c.pktable.relname)});
  const field=module.elements.find((e:any)=>e.id===transition.relation.relname+'.'+source[0]);
  field.references=[{role:'physical-fk:'+id,...ref(c.pktable.relname+'.'+target[0])}];
  field.extensions['truss.layout.native'].foreignKey={definition:c,interpretation:'UUID equality has no selected portable core key contract; physical correspondence retained through core references'};
  continue;
 }
 module.relationships.push({id,name:id,source:[ref(transition.relation.relname)],target:[{...ref(c.pktable.relname),key:'primary'}],
  sourceMultiplicity:{min:0,max:'*'},targetMultiplicity:{min:1,max:1},targetLifecycle:'unspecified',directed:true,
  fieldCorrespondence:source.map((column:string,i:number)=>({source:ref(transition.relation.relname+'.'+column),target:ref(c.pktable.relname+'.'+target[i])})),
  nativeCorrespondence:{definition:c,interpretation:'Physical integer foreign-key association; original immediate enforcement retained separately'}});
}
if(module.elements.filter((e:any)=>e.kind==='field').length!==14||module.relationships.length!==1)throw Error('Complete 12 transition columns and two referenced keys/FKs required');
const core:any={umf:'0.8.0',id:'truss-catalog-rebind-core-0.1',vocabularies:{'truss.layout.native':{version:'0.1.0'}},modules:[module],
 extensions:{'truss.layout.native':{sourceModel:paths.native,sourceSha256:hash(nativeBytes),runtimeSource:base+'catalog-rebind.sql',runtimeSourceSha256:hash(source),parentSources,
 scope:'Native61 registration-owned transition candidate. Core columns and physical FK relationships; complete native AST drives UMF SQL export. Capture validation alone does not qualify callable rebinding or a published release.'}}};
const validation=validateDocument(core),errors=validation.diagnostics.filter(d=>d.severity==='error');
if(errors.length)throw Error(JSON.stringify(errors));
const coreBytes=JSON.stringify(core)+'\n';
const receipt=JSON.stringify({profile:'truss-catalog-rebind-storage/0.1',umfSourceRevision:'cbb6fb8718aad59fd2061b62d12976387570db2f',
 parser:backend.identity,sourceSha256:hash(source),nativeSha256:hash(nativeBytes),coreSha256:hash(coreBytes),ddlSha256:hash(ddl),
 transitionColumns:12,referencedKeyColumns:2,foreignKeys:2,coreRelationships:1,physicalReferenceAssociations:1,reloadedExportExact:reloadedDdl===ddl,
 valid:validation.valid,complete:validation.complete,scope:core.extensions['truss.layout.native'].scope},null,2)+'\n';
for(const [path,bytes] of [[paths.native,nativeBytes],[paths.core,coreBytes],[paths.ddl,ddl],[base+'catalog-rebind-storage.sql',ddl],[paths.receipt,receipt]]){
 if(process.argv.includes('--check')){if(await Bun.file(path).text()!==bytes)throw Error('Stale capture: '+path);}
 else await Bun.write(path,bytes);
}
console.log(receipt);
