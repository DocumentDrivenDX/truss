# SPDX-License-Identifier: MIT OR Apache-2.0
"""Owned graph example for the unreleased native69 development assembly.

The application owns transactions. No data is inserted administratively and no
private Truss API is used. Run against a new local PG18 directory.
"""
import argparse
import json
from pathlib import Path

import psycopg
from truss import (
    CatalogDocument, EdgeFound, HistoricalRecord, HistoryEntity, LocalPostgres,
    ModuleAccessGrant, ObjectFound, ObjectNotFound, TraversalComplete, TraversalHop,
)
from truss.contracts import MapValue, TextValue
from truss.groups import (
    AliasObjectReference, AuthoredValue, CommittedReceiptReplay, CreateEdge,
    CreateObject, Delete, EndpointChange, GroupSuccess, NullOrderKey,
    OwnedOwnership, RootlessOwnership, StoredObjectReference, UpdateEdge, UpdateObject,
)
from adopter_workflow import expect, success, transaction


def run_workflow(directory, *, bun_executable='bun'):
    directory = Path(directory).resolve()
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('The example requires a new or empty directory')
    documents = (CatalogDocument('notes', 'r1',
        Path(__file__).with_name('notes-owned.umf.json').read_bytes()),)
    with LocalPostgres(directory / 'postgres') as runtime:
        params = psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
        with psycopg.connect(**params, autocommit=True, options='-c statement_timeout=10000') as admin:
            with transaction(admin) as (assembly, tx):
                installed = success(assembly.install_in_transaction(tx))
            admin.execute('CREATE ROLE owned_demo LOGIN')
            admin.execute('CREATE ROLE owned_reader NOLOGIN')
            admin.execute('CREATE ROLE owned_writer NOLOGIN')
            admin.execute(psycopg.sql.SQL('GRANT {} TO owned_demo WITH SET FALSE').format(
                psycopg.sql.Identifier(installed.registrar_role)))
            with psycopg.connect(**dict(params, user='owned_demo'), autocommit=True,
                                 options='-c statement_timeout=10000') as person:
                with transaction(person) as (assembly, tx):
                    accepted = assembly.prepare_catalog(documents, source_version='0.8.0', bun_executable=bun_executable)
                    success(assembly.accept_in_transaction(tx, accepted, request_key='register-notes',
                        origin_bytes=b'{"x-action":"register"}'))
                    view = success(assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())).view
                    note = next(d.reference for d in view.definitions
                        if d.reference.kind == 'type' and d.reference.authored_identity == 'Note')
                with transaction(admin) as (assembly, tx):
                    success(assembly.configure_module_access_in_transaction(tx, (
                        ModuleAccessGrant('notes', 'notes', 'owned_reader', 'owned_writer'),)))
                admin.execute('GRANT owned_reader,owned_writer TO owned_demo WITH SET FALSE')
                admin.execute(psycopg.sql.SQL('REVOKE {} FROM owned_demo').format(
                    psycopg.sql.Identifier(installed.registrar_role)))

                def alias(name):
                    return AliasObjectReference(alias=name)

                def stored(identity):
                    return StoredObjectReference(identity=identity)

                def create(title, ownership):
                    return CreateObject(type_definition_pin=note.definition_pin, alias=title,
                        values=(AuthoredValue(name='title', value=TextValue(kind='string', text=title)),),
                        ownership=ownership)

                def link(source, target):
                    return CreateEdge(relationship_definition_pin=relation.definition_pin,
                        source=alias(source), target=alias(target), values=(), order_key=NullOrderKey())

                def apply(assembly, tx, operations, key):
                    context = success(assembly.group_context_in_transaction(tx))
                    original = context.input(tuple(operations), MapValue(entries=()))
                    request = context.request(key)
                    result = expect(success(assembly.apply_in_transaction(tx, original, request,
                        documents=documents, bun_executable=bun_executable)), GroupSuccess)
                    return result, original, request

                with transaction(person) as (assembly, tx):
                    relation = success(assembly.get_relationship_reference_in_transaction(tx,
                        document_id='notes', module_id='notes', relationship_id='children'))
                    created, original, request = apply(assembly, tx, (
                        create('first-root', RootlessOwnership()),
                        create('second-root', RootlessOwnership()),
                        create('child', OwnedOwnership(root=alias('first-root'))),
                        create('grandchild', OwnedOwnership(root=alias('first-root'))),
                        link('first-root', 'child'), link('child', 'grandchild'),
                    ), 'create-owned-tree')
                    first, second, child, grandchild, parent_edge, child_edge = (
                        result.identity for result in created.response.semantic.results)
                # IDs/results above become externally committed facts only after
                # the application's transaction context commits.
                with transaction(person) as (assembly, tx):
                    replay = expect(success(assembly.apply_in_transaction(tx, original, request,
                        documents=documents, bun_executable=bun_executable)), GroupSuccess)
                    expect(replay.response, CommittedReceiptReplay)

                move = (
                    UpdateEdge(target=stored(parent_edge), set=(), unset=(), expected_version='1',
                        endpoint_change=EndpointChange(source=stored(second), target=stored(child))),
                    UpdateObject(target=stored(child), set=(), unset=(), expected_version='1',
                        ownership_change=OwnedOwnership(root=stored(second))),
                )
                # Real execution + caller rollback is the dry-run contract.
                with transaction(person, commit=False) as (assembly, tx):
                    apply(assembly, tx, move, 'move-subtree')
                    found = expect(success(assembly.get_object_in_transaction(tx, document_id='notes',
                        module_id='notes', record_id='Note', object_id=int(grandchild.id))), ObjectFound)
                    assert found.object.ownership == OwnedOwnership(root=stored(second))
                with transaction(person, read_only=True) as (assembly, tx):
                    found = expect(success(assembly.get_object_in_transaction(tx, document_id='notes',
                        module_id='notes', record_id='Note', object_id=int(grandchild.id))), ObjectFound)
                    assert found.object.ownership == OwnedOwnership(root=stored(first))
                with transaction(person) as (assembly, tx):
                    apply(assembly, tx, move, 'move-subtree')
                with transaction(person, read_only=True) as (assembly, tx):
                    found = expect(success(assembly.lookup_key_in_transaction(tx, document_id='notes',
                        module_id='notes', record_id='Note', key_id='title-key', values=('grandchild',))), ObjectFound)
                    assert found.object.ownership == OwnedOwnership(root=stored(second))
                    assert found.object.version == 2
                    edge = expect(success(assembly.get_edge_in_transaction(tx, document_id='notes',
                        module_id='notes', relationship_id='children', edge_id=int(parent_edge.id))), EdgeFound)
                    assert (edge.edge.source, edge.edge.target) == (second, child)
                    reached = expect(success(assembly.traverse_in_transaction(tx, start=second,
                        hops=(TraversalHop(relationship=relation),) * 2)), TraversalComplete)
                    assert tuple(obj.identity for obj in reached.objects) == (grandchild,)
                    assert reached.objects[0].ownership == OwnedOwnership(root=stored(second))
                with transaction(person) as (assembly, tx):
                    deleted, _, _ = apply(assembly, tx, (
                        Delete(operation='delete_object', target=stored(second), expected_version='1'),
                    ), 'delete-owned-tree')
                    deleted_ids = {entry.identity for entry in deleted.response.semantic.results[0].deleted}
                    assert deleted_ids == {second, child, grandchild, parent_edge, child_edge}
                with transaction(person, read_only=True) as (assembly, tx):
                    expect(success(assembly.get_object_in_transaction(tx, document_id='notes',
                        module_id='notes', record_id='Note', object_id=int(grandchild.id))), ObjectNotFound)
                    for version, root in ((1, first), (2, second)):
                        record = expect(success(assembly.reconstruct_in_transaction(tx,
                            entity=HistoryEntity(kind='object', document_id='notes', module_id='notes',
                                definition_id='Note', id=int(grandchild.id)), version=version)), HistoricalRecord)
                        assert json.loads(record.record)['ownership']['root']['id'] == root.id
                with transaction(person) as (assembly, tx):
                    replay = expect(success(assembly.apply_in_transaction(tx, original, request,
                        documents=documents, bun_executable=bun_executable)), GroupSuccess)
                    expect(replay.response, CommittedReceiptReplay)
                return {'created_objects': 4, 'reparented_objects': 2, 'cascade_deleted': len(deleted_ids),
                        'original_receipt_replayed_after_delete': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--bun', default='bun')
    arguments = parser.parse_args()
    print(json.dumps(run_workflow(arguments.directory, bun_executable=arguments.bun)))
