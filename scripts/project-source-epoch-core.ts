/** Bounded authored structural delta; native semantics remain retained. */
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {getPostgresqlNode} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
import {validateDocument} from '/Users/erik/Projects/umf/src/validation/document';
const source='docs/helix/02-design/models/truss-layout-source-epoch-0.16.proposal.umf.json';
const prior='docs/helix/02-design/models/truss-layout-core-structural-0.3.proposal.umf.json';
const model:any=readDocument(await Bun.file(source).text(),'json');
const old=await Bun.file(prior).json();const module=structuredClone(old.modules.find((m:any)=>m.id==='truss-layout'));
const nodes=JSON.parse(renderTree(getPostgresqlNode(model,'/stmts')));
const ref=(element:string)=>({module:module.id,element});
const newTables=nodes.map((n:any,i:number)=>({stmt:n.stmt?.CreateStmt,index:i})).filter((x:any)=>['source_epoch_registry','source_epoch_current'].includes(x.stmt?.relation.relname));
if(newTables.length!==2)throw Error('Exact two epoch tables required');
for(const {stmt,index} of newTables){
 const name=stmt.relation.relname,fields:any[]=[],keys:any[]=[];
 const record:any={id:name,name,kind:'record',extensions:{},members:[],references:[],keys};
 for(const [i,entry] of stmt.tableElts.entries()){
  if(!entry.ColumnDef)continue;const c=entry.ColumnDef,id=name+'.'+c.colname;
  const type=c.typeName.names.at(-1).String.sval;
  const scalarType=({text:'string',bytea:'bytes',int2:'integer'} as Record<string,string>)[type];
  if(!scalarType)throw Error('Unselected epoch column type '+type);
  const required=(c.constraints??[]).some((n:any)=>['CONSTR_NOTNULL','CONSTR_PRIMARY'].includes(n.Constraint.contype))||stmt.tableElts.some((e:any)=>e.Constraint?.contype==='CONSTR_PRIMARY'&&e.Constraint.keys.some((k:any)=>k.String.sval===c.colname));
  fields.push({id,name:c.colname,kind:'field',scalarType,cardinality:'one',nullability:required?'required':'optional',extensions:{'truss.layout.native':{sourcePointer:`/${index}/stmt/CreateStmt/tableElts/${i}/ColumnDef`,nativeType:c.typeName,constraints:c.constraints??[],collation:c.collClause??null,sqlNullMeaning:'retained native constraints; not core absence'}}});
  record.members.push(ref(id));record.references.push({role:'member',...ref(id)});
  for(const n of c.constraints??[])if(n.Constraint.contype==='CONSTR_PRIMARY')keys.push({id:'epoch-primary',name:'epoch-primary',fields:[ref(id)],primary:true});
 }
 for(const e of stmt.tableElts){const c=e.Constraint;if(c&&['CONSTR_PRIMARY','CONSTR_UNIQUE'].includes(c.contype)){const id=c.contype==='CONSTR_PRIMARY'?'epoch-primary':'epoch-unique';keys.push({id,name:id,fields:c.keys.map((k:any)=>ref(name+'.'+k.String.sval)),primary:c.contype==='CONSTR_PRIMARY'});}}
 module.elements.push(record,...fields);
}
for(const {stmt,index} of newTables){
 for(const [i,e] of stmt.tableElts.entries()){
  const c=e.Constraint;if(c?.contype!=='CONSTR_FOREIGN')continue;
  const target=module.elements.find((e:any)=>e.id===c.pktable.relname);
  const targetFields=c.pk_attrs.map((k:any)=>c.pktable.relname+'.'+k.String.sval);
  const key=target.keys.find((k:any)=>JSON.stringify(k.fields.map((r:any)=>r.element))===JSON.stringify(targetFields));
  if(!key)throw Error('Original target key correspondence missing');
  const id='epoch-fk-'+module.relationships.length;
  module.relationships.push({id,name:id,source:[ref(stmt.relation.relname)],target:[{...ref(target.id),key:key.id}],sourceMultiplicity:{min:0,max:'*'},targetMultiplicity:{min:0,max:1},targetLifecycle:'unspecified',directed:true,fieldCorrespondence:c.fk_attrs.map((k:any,j:number)=>({source:ref(stmt.relation.relname+'.'+k.String.sval),target:ref(targetFields[j])})),nativeCorrespondence:{sourcePointer:`/${index}/stmt/CreateStmt/tableElts/${i}/Constraint`,definition:c,scope:'Physical association only; broad multiplicity is not native enforcement equivalence'}});
 }
}
model.umf='0.7.0';model.id='truss-layout-core-structural-0.4-epoch-review';model.modules=[module];model.vocabularies['truss.layout.native']={version:'0.1.0'};
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
model.extensions={'truss.layout.native':{sourceModel:source,sourceSha256:hash(await Bun.file(source).text()),structuralSource:prior,structuralSourceSha256:hash(await Bun.file(prior).text()),scope:'Epoch layout0.16 structural mirror and complete retained native source; no installed identity or DDL equivalence claim'}};
const output='docs/helix/02-design/models/truss-layout-core-structural-0.4.proposal.umf.json';
const serialized=JSON.stringify(model)+'\n';const validation=validateDocument(model);const errors=validation.diagnostics.filter(d=>d.severity==='error');if(errors.length)throw Error(JSON.stringify(errors));
await Bun.write(output,serialized);
await Bun.write('docs/helix/04-build/evidence/design-audit/source-epoch-core.json',JSON.stringify({source,prior,output,outputSha256:hash(serialized),records:module.elements.filter((e:any)=>e.kind==='record').length,fields:module.elements.filter((e:any)=>e.kind==='field').length,relationships:module.relationships.length,valid:validation.valid,complete:validation.complete,errors,scope:model.extensions['truss.layout.native'].scope},null,2)+'\n');
console.log(JSON.stringify({valid:validation.valid,complete:validation.complete,errors:errors.length}));
