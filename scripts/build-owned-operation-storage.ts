// SPDX-License-Identifier: MIT OR Apache-2.0
/** Native operation custody for cascades/reparents, through UMF's SQL exporter. */
import {backend} from '/Users/erik/.codex/worktrees/0e51/umf/native/postgresql/runtime';
import {readDocument} from '/Users/erik/.codex/worktrees/0e51/umf/src/model/document';
import {importPostgresqlSql, exportPostgresqlSql, getPostgresqlNode} from '/Users/erik/.codex/worktrees/0e51/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/.codex/worktrees/0e51/umf/src/model/native-json';
import {validateDocument} from '/Users/erik/.codex/worktrees/0e51/umf/src/validation/document';

const directory = 'docs/helix/02-design/models/';
const sourceModel = directory + 'truss-owned-operation-storage-0.1.proposal.umf.json';
const native = await importPostgresqlSql(`
CREATE TABLE truss.runtime_owned_operation (
 attempt_id uuid NOT NULL REFERENCES truss.runtime_object_attempt(id),
 operation_index int NOT NULL CHECK(operation_index BETWEEN 0 AND 1023),
 writer_xid xid8 NOT NULL,
 plan jsonb NOT NULL,
 result jsonb,
 PRIMARY KEY(attempt_id,operation_index),
 CHECK(jsonb_typeof(plan)='object'),
 CHECK(octet_length(convert_to(plan::text,'UTF8')) BETWEEN 1 AND 16777216),
 CHECK(result IS NULL OR (jsonb_typeof(result)='object' AND octet_length(convert_to(result::text,'UTF8')) BETWEEN 1 AND 16777216))
);`, backend, {id:'truss-owned-operation-storage-0.1'});
const nativeBytes = JSON.stringify(native) + '\n';
const ddl = await exportPostgresqlSql(readDocument(nativeBytes, 'json'), backend);
if (ddl !== await exportPostgresqlSql(native, backend)) throw Error('Saved UMF must reproduce exact DDL');
const definition = JSON.parse(renderTree(getPostgresqlNode(native, '/stmts/0/stmt/CreateStmt')));
const module:any = {id:'truss-owned-operation', namespace:'truss', elements:[]};
const ref = (element:string) => ({module:module.id, element});
const record:any = {id:'runtime_owned_operation', name:'runtime_owned_operation', kind:'record',
    members:[], references:[], extensions:{'truss.layout.native':{definition}}};
for (const entry of definition.tableElts) {
    const column = entry.ColumnDef;
    if (!column) continue;
    const id = record.id + '.' + column.colname;
    const nativeType = column.typeName.names.at(-1).String.sval;
    const field:any = {id, name:column.colname, kind:'field', cardinality:'one',
        nullability:(column.constraints ?? []).some((entry:any) => entry.Constraint.contype === 'CONSTR_NOTNULL') ? 'required' : 'nullable',
        extensions:{'truss.layout.native':{definition:column, nativeType,
            interpretation:'Original native UUID, xid8 and JSONB semantics; no portable UUID key or JSON scalar claim'}}};
    if (nativeType === 'int4') field.scalarType = 'integer';
    for (const wrapper of column.constraints ?? []) {
        if (wrapper.Constraint.contype === 'CONSTR_FOREIGN') {
            field.references = [{role:'physical-fk:attempt', ...ref('runtime_object_attempt.id')}];
            field.extensions['truss.layout.native'].foreignKey = wrapper.Constraint;
            record.references.push({role:'physical-fk:attempt', ...ref('runtime_object_attempt')});
        }
    }
    record.members.push(ref(id));
    record.references.push({role:'member', ...ref(id)});
    module.elements.push(field);
}
record.extensions['truss.layout.native'].physicalKeys = definition.tableElts
    .filter((entry:any) => entry.Constraint?.contype === 'CONSTR_PRIMARY')
    .map((entry:any) => entry.Constraint);
module.elements.push(record,
    {id:'runtime_object_attempt.id', name:'id', kind:'field', cardinality:'one', nullability:'required',
        extensions:{'truss.layout.native':{nativeType:'uuid'}}},
    {id:'runtime_object_attempt', name:'runtime_object_attempt', kind:'record',
        members:[ref('runtime_object_attempt.id')], references:[{role:'member', ...ref('runtime_object_attempt.id')}],
        extensions:{'truss.layout.native':{projection:'Referenced key only; full attempt remains in operations.sql'}}});
const core:any = {umf:'0.8.0', id:'truss-owned-operation-core-0.1',
    vocabularies:{'truss.layout.native':{version:'0.1.0'}}, modules:[module],
    extensions:{'truss.layout.native':{sourceModel,
        scope:'Private immutable per-original-operation affected inventory with one write-once result for the owned executor. Not a public planning API or installed ownership claim.'}}};
const validation = validateDocument(core);
if (validation.diagnostics.some(d => d.severity === 'error')) throw Error(JSON.stringify(validation.diagnostics));
if (record.members.length !== 5 || record.references.filter((r:any) => r.role === 'physical-fk:attempt').length !== 1)
    throw Error('Complete five-column/FK projection required');
await Bun.write(sourceModel, nativeBytes);
await Bun.write(directory+'truss-owned-operation-core-0.1.proposal.umf.json', JSON.stringify(core)+'\n');
await Bun.write('packages/postgresql/owned-groups/operation-storage.generated.sql', ddl);
console.log(JSON.stringify({columns:5, attemptForeignKey:true, coreValid:validation.valid,
    coreComplete:validation.complete, ownerExport:true, installed:false}));
