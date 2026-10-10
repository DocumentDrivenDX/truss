/** Core structural projection of one original adjunct; no installed identity allocation. */
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {getPostgresqlNode} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
import {validateDocument} from '/Users/erik/Projects/umf/src/validation/document';
const source='docs/helix/02-design/contracts/layout-migration-storage-v0.1.proposal.umf.json';
const prior='docs/helix/02-design/models/truss-layout-core-structural-0.5.proposal.umf.json';
const old=await Bun.file(prior).json(),model=structuredClone(old),module=model.modules.find((m:any)=>m.id==='truss-layout');
const nodes=JSON.parse(renderTree(getPostgresqlNode(readDocument(await Bun.file(source).text(),'json'),'/stmts')));
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const ref=(element:string)=>({module:module.id,element});
const tables=nodes.map((n:any,index:number)=>({stmt:n.stmt?.CreateStmt,index})).filter((n:any)=>n.stmt);
if(tables.length!==1||tables[0].stmt.relation.relname!=='layout_migration_receipt'||module.elements.some((e:any)=>e.id==='layout_migration_receipt'))throw Error('Exactly one new original capture home required');
const {stmt,index}=tables[0],name=stmt.relation.relname;
const inlinePk=stmt.tableElts.find((e:any)=>e.ColumnDef?.constraints?.some((n:any)=>n.Constraint?.contype==='CONSTR_PRIMARY'))?.ColumnDef;
const pk=stmt.tableElts.find((e:any)=>e.Constraint?.contype==='CONSTR_PRIMARY')?.Constraint ?? (inlinePk?{contype:'CONSTR_PRIMARY',keys:[{String:{sval:inlinePk.colname}}]}:undefined);
if(!pk)throw Error('Original capture primary key required');
const record:any={id:name,name,kind:'record',extensions:{},members:[],references:[],keys:[{id:'migration-primary',name:'migration-primary',primary:true,fields:pk.keys.map((k:any)=>ref(name+'.'+k.String.sval))}]};
for(const [i,entry] of stmt.tableElts.entries()){
 if(!entry.ColumnDef)continue;
 const c=entry.ColumnDef,id=name+'.'+c.colname,type=c.typeName.names.at(-1).String.sval;
 const scalarType=({xid8:'postgresql.xid8',int8:'integer',text:'string',bytea:'bytes'} as Record<string,string>)[type];
 if(!scalarType)throw Error('Unselected original column type '+type);
 const required=(c.constraints??[]).some((n:any)=>n.Constraint.contype==='CONSTR_NOTNULL')||pk.keys.some((k:any)=>k.String.sval===c.colname);
 module.elements.push({id,name:c.colname,kind:'field',scalarType,cardinality:'one',nullability:required?'required':'optional',extensions:{'truss.layout.native':{sourceModel:source,sourcePointer:`/${index}/stmt/CreateStmt/tableElts/${i}/ColumnDef`,nativeType:c.typeName,constraints:c.constraints??[],collation:c.collClause??null,sqlNullMeaning:'Native generated/required semantics retained; core optionality is a structural projection'}}});
 record.members.push(ref(id));record.references.push({role:'member',...ref(id)});
}
if(record.members.length!==11)throw Error('Complete eleven-column migration receipt inventory required');
record.extensions['truss.layout.native']={physicalKeys:[{originalKey:record.keys[0],definition:pk,sourceModel:source,interpretation:'Native allocator bigint key; complete native constraints retained separately'}],physicalForeignKeys:[]};
delete record.keys;
module.elements.push(record);
const baselinePath=old.extensions['truss.layout.native'].sourceModel;
if(hash(await Bun.file(baselinePath).text())!==old.extensions['truss.layout.native'].sourceSha256)throw Error('Original baseline hash mismatch');
const baseline=JSON.parse(renderTree(getPostgresqlNode(readDocument(await Bun.file(baselinePath).text(),'json'),'/stmts')));
for(const [i,e] of stmt.tableElts.entries()){
 const c=e.Constraint;if(c?.contype!=='CONSTR_FOREIGN')continue;
 const target=module.elements.find((e:any)=>e.id===c.pktable.relname&&e.kind==='record');
 if(!target)throw Error('Original parent record absent');
 const targetFields=c.pk_attrs.map((k:any)=>target.id+'.'+k.String.sval);
 const original=baseline.find((n:any)=>n.stmt?.CreateStmt?.relation?.relname===target.id)?.stmt.CreateStmt;
 const declaration=original?.tableElts.find((e:any)=>['CONSTR_PRIMARY','CONSTR_UNIQUE'].includes(e.Constraint?.contype)&&JSON.stringify(e.Constraint.keys.map((k:any)=>target.id+'.'+k.String.sval))===JSON.stringify(targetFields))?.Constraint;
 if(!declaration)throw Error('No original unique parent key');
 const id='migration-physical-fk-'+i;
 const correspondence=c.fk_attrs.map((k:any,j:number)=>({source:ref(name+'.'+k.String.sval),target:ref(targetFields[j])}));
 record.extensions['truss.layout.native'].physicalForeignKeys.push({id,sourceModel:source,sourcePointer:`/${index}/stmt/CreateStmt/tableElts/${i}/Constraint`,definition:c,targetKeyDefinition:declaration,fieldCorrespondence:correspondence,interpretation:'Native C-collated text key correspondence retained through core references; no new portable key profile selected'});
 record.references.push({role:'physical-fk:'+id,...ref(target.id)});
 for(const pair of correspondence){const field=module.elements.find((e:any)=>e.id===pair.source.element);if(!field||!module.elements.some((e:any)=>e.id===pair.target.element))throw Error('Original physical FK field absent');(field.references??=[]).push({role:'physical-fk:'+id,...pair.target});}

}
model.id='truss-layout-core-structural-0.6-migration-review';
model.extensions['truss.layout.native']={...old.extensions['truss.layout.native'],structuralSource:prior,structuralSourceSha256:hash(await Bun.file(prior).text()),migrationSourceModel:source,migrationSourceSha256:hash(await Bun.file(source).text()),scope:'Structural projection of baseline0.16 plus uncomposed configuration and migration receipt adjuncts. Native semantics, installation and protected runtime remain unqualified.'};
const validation=validateDocument(model),errors=validation.diagnostics.filter(d=>d.severity==='error');if(errors.length)throw Error(JSON.stringify(errors));
const output='docs/helix/02-design/models/truss-layout-core-structural-0.6.proposal.umf.json',bytes=JSON.stringify(model)+'\n';
const receipt={source,prior,output,outputSha256:hash(bytes),producerSha256:hash(await Bun.file('scripts/project-layout-migration-core.ts').text()),records:module.elements.filter((e:any)=>e.kind==='record').length,fields:module.elements.filter((e:any)=>e.kind==='field').length,addedRelationships:module.relationships.filter((r:any)=>r.id.startsWith('migration-fk-')).length,addedPhysicalReferenceAssociations:record.extensions['truss.layout.native'].physicalForeignKeys.length,valid:validation.valid,complete:validation.complete,errors,scope:model.extensions['truss.layout.native'].scope};
if(receipt.records!==50||receipt.fields!==481||receipt.addedRelationships!==0||receipt.addedPhysicalReferenceAssociations!==1)throw Error('Incomplete structural delta');
for(const [p,b] of [[output,bytes],['docs/helix/04-build/evidence/design-audit/layout-migration-core.json',JSON.stringify(receipt,null,2)+'\n']])if(process.argv.includes('--check')){if(await Bun.file(p).text()!==b)throw Error('Stale core capture projection')}else await Bun.write(p,b);
console.log(JSON.stringify({records:receipt.records,fields:receipt.fields,addedRelationships:receipt.addedRelationships,valid:validation.valid,complete:validation.complete}));
