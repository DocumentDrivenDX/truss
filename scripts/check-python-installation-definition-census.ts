// SPDX-License-Identifier: MIT OR Apache-2.0
/** Independent original AST category census; not semantic/authority closure. */
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {getPostgresqlNode} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const source='docs/helix/02-design/models/truss-layout-source-epoch-0.16.proposal.umf.json';
const nodes=JSON.parse(renderTree(getPostgresqlNode(readDocument(await Bun.file(source).text(),'json'),'/stmts')));
const definitions=await Bun.file('packages/python/src/truss/_installation/definitions.json').json();
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
if(hash(await Bun.file(source).text())!==definitions.modelSha256)throw Error('Original model correspondence required');
const kinds:Record<string,number>={c:0,f:0,p:0,u:0};let expressions=0,indexes=0;
const named=new Map<string,string>();
function constraint(c:any,table:string){
 const kind=({CONSTR_CHECK:'c',CONSTR_FOREIGN:'f',CONSTR_PRIMARY:'p',CONSTR_UNIQUE:'u'} as any)[c.contype];
 if(kind){kinds[kind]++;const selectedName=c.conname??(kind==='u'&&c.keys?table+'_'+c.keys.map((k:any)=>k.String.sval).join('_')+'_key':null);if(selectedName){if(new TextEncoder().encode(selectedName).length>63)throw Error('Unselected generated name truncation');const name=table+'\0'+selectedName;if(named.has(name))throw Error('Duplicate original constraint identity');named.set(name,kind);}}
 else if(['CONSTR_DEFAULT','CONSTR_GENERATED'].includes(c.contype))expressions++;
 else if(!['CONSTR_NOTNULL','CONSTR_ATTR_DEFERRABLE','CONSTR_ATTR_DEFERRED'].includes(c.contype))throw Error('Unclassified original constraint');
}
for(const wrapped of nodes){const s=wrapped.stmt;
 if(s.CreateStmt)for(const e of s.CreateStmt.tableElts??[]){if(e.Constraint)constraint(e.Constraint,s.CreateStmt.relation.relname);else if(e.ColumnDef)for(const c of e.ColumnDef.constraints??[])constraint(c.Constraint,s.CreateStmt.relation.relname);else throw Error('Unclassified original table element');}
 else if(s.AlterTableStmt)for(const e of s.AlterTableStmt.cmds){const c=e.AlterTableCmd,table=s.AlterTableStmt.relation.relname;
  if(c.subtype==='AT_AddConstraint')constraint(c.def.Constraint,table);
  else if(c.subtype==='AT_AddColumn')for(const k of c.def.ColumnDef.constraints??[])constraint(k.Constraint,table);
  else if(c.subtype==='AT_DropConstraint'){const name=table+'\0'+c.name,kind=named.get(name);if(!kind)throw Error('Original dropped constraint absent');kinds[kind]--;named.delete(name);}
  else if(c.subtype!=='AT_AlterColumnType')throw Error('Unclassified original alteration');
 }
 else if(s.IndexStmt)indexes++;
}
const observed=JSON.parse(definitions.compiledOriginal),nativeKinds:Record<string,number>={c:0,f:0,p:0,u:0};
for(const c of observed.constraints){if(!(c.kind in nativeKinds))throw Error('Unclassified compiled constraint');nativeKinds[c.kind]++;}
if(JSON.stringify(kinds)!==JSON.stringify(nativeKinds)||expressions!==observed.expressions.length||indexes+kinds.p+kinds.u!==observed.indexes.length)throw Error('Independent original declaration category coverage mismatch');
console.log(JSON.stringify({sourceSha256:definitions.modelSha256,constraints:kinds,expressions,explicitIndexes:indexes,compiledIndexes:observed.indexes.length,scope:'Independent original AST category census only; expression/definition correspondence has separate native evidence'}));
