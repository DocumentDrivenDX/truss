// SPDX-License-Identifier: MIT OR Apache-2.0
/** Prepare genuine create before-images through UMF's existing SQL exporter. */
import {backend} from '/Users/erik/.codex/worktrees/0e51/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/.codex/worktrees/0e51/umf/src/model/document';
import {importPostgresqlSql,exportPostgresqlSql,getPostgresqlNode,proposePostgresqlNodeEdit} from '/Users/erik/.codex/worktrees/0e51/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/.codex/worktrees/0e51/umf/src/model/native-json';
import {validateDocument} from '/Users/erik/.codex/worktrees/0e51/umf/src/validation/document';

const directory='docs/helix/02-design/models/';
const source=readDocument(await Bun.file(directory+'truss-owned-object-transition-storage-0.1.proposal.umf.json').text(),'json');
const original=JSON.parse(renderTree(getPostgresqlNode(source,'/stmts/0/stmt/CreateStmt')));
if(original.relation.relname!=='runtime_object_transition')throw Error('Original object transition required');
const index=original.tableElts.findIndex((e:any)=>e.ColumnDef?.colname==='before_object');
const before=original.tableElts[index]?.ColumnDef;
if(!before || before.constraints?.filter((c:any)=>c.Constraint?.contype==='CONSTR_NOTNULL').length!==1)throw Error('Original required before-image constraint required');
const changed={...before};
const remaining=before.constraints.filter((c:any)=>c.Constraint?.contype!=='CONSTR_NOTNULL');
if(remaining.length)changed.constraints=remaining;else delete changed.constraints;
let edited=proposePostgresqlNodeEdit(source,`/stmts/0/stmt/CreateStmt/tableElts/${index}/ColumnDef`,JSON.stringify(changed)).document;
edited.id='truss-owned-object-transition-storage-0.2';
const nativeBytes=JSON.stringify(edited)+'\n';
const ddl=await exportPostgresqlSql(edited,backend);
if(ddl===await exportPostgresqlSql(source,backend))throw Error('DDL must consume edited model');
if(ddl!==await exportPostgresqlSql(readDocument(nativeBytes,'json'),backend))throw Error('Saved native model must reproduce exact DDL');

// Change an imported native constraint command, then export its saved UMF model.
let upgrade=await importPostgresqlSql('ALTER TABLE truss.runtime_object_transition ALTER COLUMN before_object SET NOT NULL;',backend,{id:'truss-unified-transition-upgrade-0.1'});
const command=JSON.parse(renderTree(getPostgresqlNode(upgrade,'/stmts/0/stmt/AlterTableStmt/cmds/0/AlterTableCmd')));
if(command.subtype!=='AT_SetNotNull' || command.name!=='before_object')throw Error('Original before-image constraint command required');
upgrade=proposePostgresqlNodeEdit(upgrade,'/stmts/0/stmt/AlterTableStmt/cmds/0/AlterTableCmd',JSON.stringify({...command,subtype:'AT_DropNotNull'})).document;
const upgradeBytes=JSON.stringify(upgrade)+'\n';
const upgradeDdl=await exportPostgresqlSql(upgrade,backend);
if(upgradeDdl!==await exportPostgresqlSql(readDocument(upgradeBytes,'json'),backend))throw Error('Saved upgrade model must reproduce exact DDL');

const core=JSON.parse(await Bun.file(directory+'truss-owned-object-transition-core-0.1.proposal.umf.json').text());
core.id='truss-owned-object-transition-core-0.2';
const elements=core.modules[0].elements;
const field=elements.find((e:any)=>e.id==='runtime_object_transition.before_object');
if(field.nullability!=='required')throw Error('Original core required before-image required');
field.nullability='unspecified';
field.extensions['truss.layout.native'].definition=changed;
field.extensions['truss.layout.native'].nullMeaning='SQL NULL is the absent before-image for a genuine new-profile create; JSON null is not substituted. Original profile/input/transition evidence must establish creation.';
elements.find((e:any)=>e.id==='runtime_object_transition').extensions['truss.layout.native'].definition=JSON.parse(renderTree(getPostgresqlNode(edited,'/stmts/0/stmt/CreateStmt')));
core.extensions['truss.layout.native'].sourceModel=directory+'truss-owned-object-transition-storage-0.2.proposal.umf.json';
core.extensions['truss.layout.native'].scope='Uninstalled unified create/update/delete transitions; SQL NULL before-image does not alone prove a create. Native guard, reservation, journal and attribution integration remains required.';
const validation=validateDocument(core);
if(validation.diagnostics.some(d=>d.severity==='error'))throw Error(JSON.stringify(validation.diagnostics));
await Bun.write(directory+'truss-owned-object-transition-storage-0.2.proposal.umf.json',nativeBytes);
await Bun.write(directory+'truss-owned-object-transition-core-0.2.proposal.umf.json',JSON.stringify(core)+'\n');
await Bun.write(directory+'truss-unified-transition-upgrade-0.1.proposal.umf.json',upgradeBytes);
await Bun.write('packages/postgresql/owned-groups/transition.generated.sql',ddl);
await Bun.write('packages/postgresql/owned-groups/transition-upgrade.generated.sql',upgradeDdl);
console.log(JSON.stringify({ownerExport:true,coreValid:validation.valid,coreComplete:validation.complete,installed:false,beforeImage:'SQL NULL only for genuine new-profile creates'}));
