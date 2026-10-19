# SPDX-License-Identifier: MIT OR Apache-2.0
"""Run against a NEW local PG18 data directory; all data uses public Truss APIs."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path

import psycopg
from truss import (
    CatalogDocument, CatalogRuntimeConfiguration, CapabilityAvailable, FeedPage,
    FeedAcknowledged, LocalPostgres, ModuleAccessGrant, ObjectFound, ObjectNotFound,
    Ok, QueryRows, QueryRelatedKeys, ReceiptIncluded, adopt_psycopg_host,
    create_reference_assembly,
)
from truss.contracts import MapValue, TextValue
from truss.groups import (
    AliasObjectReference, AuthoredValue, CommittedReceiptReplay, CreateEdge,
    CreateObject, GroupSuccess, NullOrderKey, RequestNone, RootlessOwnership,
)
from truss.imports import ImportCreated, ImportReported


def success(result):
    if not isinstance(result, Ok):
        raise RuntimeError(f'Truss operation failed: {result!r}')
    return result.value


def expect(value, kind):
    if not isinstance(value, kind):
        raise RuntimeError(f'Expected {kind.__name__}, received {value!r}')
    return value


@contextmanager
def transaction(connection, *, read_only=False, commit=True):
    """The caller begins and settles; Truss only adopts this transaction."""
    connection.execute('BEGIN READ ONLY' if read_only else 'BEGIN')
    host = adopt_psycopg_host(connection, statement_timeout_ms=10000,
                             operation_timeout_ms=30000)
    try:
        tx = success(host.adopt_transaction(access_mode='read_only' if read_only else 'read_write'))
        assembly = success(create_reference_assembly(CatalogRuntimeConfiguration(), host))
        yield assembly, tx
    except BaseException:
        if host.detach():
            try:
                connection.rollback()
            except BaseException:
                connection.close()
        else:
            connection.close()
        raise
    else:
        if not host.detach():
            connection.close()
            raise RuntimeError('Truss host release unavailable; owned connection closed')
        try:
            connection.commit() if commit else connection.rollback()
        except BaseException:
            connection.close()
            raise


def sync_directory(directory):
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def run_workflow(directory, *, bun_executable='bun'):
    directory = Path(directory).resolve()
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('The demo requires a new or empty directory')
    missing = []
    ancestor = directory
    while not ancestor.exists():
        missing.append(ancestor)
        ancestor = ancestor.parent
    directory.mkdir(parents=True, exist_ok=True)
    for created in reversed(missing):
        sync_directory(created.parent)
    sync_directory(directory.parent)
    source = Path(__file__).with_name('notes.umf.json').read_bytes()
    documents = (CatalogDocument('notes', 'r1', source),)
    with LocalPostgres(directory / 'postgres') as runtime:
        params = psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
        with psycopg.connect(**params, autocommit=True, options='-c statement_timeout=10000') as admin:
            with transaction(admin) as (assembly, tx):
                installed = success(assembly.install_in_transaction(tx))
                if not success(assembly.status_in_transaction(tx)).installed:
                    raise RuntimeError('Installation status did not confirm installation')
            # Operations setup only. No administrative data rows are inserted.
            admin.execute('CREATE ROLE demo_person LOGIN')
            admin.execute('CREATE ROLE demo_reader NOLOGIN')
            admin.execute('CREATE ROLE demo_writer NOLOGIN')
            admin.execute(psycopg.sql.SQL('GRANT {} TO demo_person WITH SET FALSE').format(
                psycopg.sql.Identifier(installed.registrar_role)))
            person_params = dict(params, user='demo_person')
            with psycopg.connect(**person_params, autocommit=True, options='-c statement_timeout=10000') as person:
                with transaction(person) as (assembly, tx):
                    prepared = assembly.prepare_catalog(documents, bun_executable=bun_executable)
                    success(assembly.accept_in_transaction(tx, prepared,
                        request_key='register-notes', origin_bytes=b'{"x-action":"register"}'))
                    view = success(assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())).view
                    note = next(d.reference for d in view.definitions
                                if d.reference.kind == 'type' and d.reference.authored_identity == 'Note')
                with transaction(admin) as (assembly, tx):
                    success(assembly.configure_module_access_in_transaction(tx, (
                        ModuleAccessGrant('notes', 'notes', 'demo_reader', 'demo_writer'),)))
                    success(assembly.register_feed_consumer_in_transaction(tx,
                        consumer_id='demo-sink', reader_role='demo_reader'))
                admin.execute('GRANT demo_reader,demo_writer TO demo_person WITH SET FALSE')
                admin.execute(psycopg.sql.SQL('REVOKE {} FROM demo_person').format(
                    psycopg.sql.Identifier(installed.registrar_role)))

                def values(title):
                    return (AuthoredValue(name='title', value=TextValue(kind='string', text=title)),)

                def create(title, alias):
                    return CreateObject(type_definition_pin=note.definition_pin,
                        values=values(title), ownership=RootlessOwnership(), alias=alias)

                with transaction(person) as (assembly, tx):
                    relation = success(assembly.get_relationship_reference_in_transaction(tx,
                        document_id='notes', module_id='notes', relationship_id='references'))
                    context = success(assembly.group_context_in_transaction(tx))
                    original_input = context.input((create('first', 'first'), create('second', 'second'),
                        CreateEdge(relationship_definition_pin=relation.definition_pin,
                            source=AliasObjectReference(alias='first'), target=AliasObjectReference(alias='second'),
                            values=(), order_key=NullOrderKey(), alias='link')), MapValue(entries=()))
                    original_request = context.request('create-two-notes')
                    expect(success(assembly.apply_in_transaction(tx, original_input, original_request,
                        documents=documents, bun_executable=bun_executable)), GroupSuccess)
                # A durable token is obtained only after caller commit and original retry.
                with transaction(person) as (assembly, tx):
                    replay = expect(success(assembly.apply_in_transaction(tx, original_input,
                        original_request, documents=documents, bun_executable=bun_executable)), GroupSuccess)
                    token = expect(replay.response, CommittedReceiptReplay).receipt_token
                with transaction(person, read_only=True) as (assembly, tx):
                    included = expect(success(assembly.reached_in_transaction(tx, token)), ReceiptIncluded)
                    if not included.included:
                        raise RuntimeError('Committed receipt was not visible')
                    behind = expect(success(assembly.reached_in_transaction(tx, token, consumer_id='demo-sink')), ReceiptIncluded)
                    if behind.included or behind.comparison_profile == included.comparison_profile:
                        raise RuntimeError('Expected distinct feed comparison before ACK')
                    found = expect(success(assembly.lookup_key_in_transaction(tx, document_id='notes',
                        module_id='notes', record_id='Note', key_id='title-key', values=('first',),
                        bun_executable=bun_executable)), ObjectFound)
                    if found.object.ownership.state != 'rootless':
                        raise RuntimeError('Unexpected ownership for the rootless note')
                    selected = expect(assembly.compiled_execution(assembly.compiled_selection), CapabilityAvailable)
                    rows = expect(success(selected.capability.query_in_transaction(tx,
                        sql='SELECT n.title,RELATED_KEYS(n.references,10) AS linked FROM Note n '
                            'WHERE HAS_RELATED(n.references,KEY(:title))',
                        document_ids=('notes',), parameters={'title': 'second'})), QueryRows)
                    if rows.rows != (('first', QueryRelatedKeys(items=(('second',),), truncated=False)),):
                        raise RuntimeError(f'Unexpected query result: {rows!r}')
                # Dry-run means real execution followed by caller rollback.
                with transaction(person, commit=False) as (assembly, tx):
                    context = success(assembly.group_context_in_transaction(tx))
                    expect(success(assembly.apply_in_transaction(tx,
                        context.input((create('dry-run', 'temporary'),), MapValue(entries=())),
                        RequestNone(), documents=documents, bun_executable=bun_executable)), GroupSuccess)
                with transaction(person, read_only=True) as (assembly, tx):
                    expect(success(assembly.lookup_key_in_transaction(tx, document_id='notes',
                        module_id='notes', record_id='Note', key_id='title-key', values=('dry-run',),
                        bun_executable=bun_executable)), ObjectNotFound)
                with transaction(person) as (assembly, tx):
                    context = success(assembly.import_context_in_transaction(tx))
                    record = success(assembly.object_import_record_in_transaction(tx,
                        document_id='notes', module_id='notes', record_id='Note', values=values('imported')))
                    imported = expect(assembly.import_in_transaction(tx,
                        context.input((record,), load_id='demo-load', asserted_origin=MapValue(entries=())),
                        documents=documents, bun_executable=bun_executable), ImportReported)
                    expect(imported.report.outcomes[0], ImportCreated)
                # All writer/read transactions above are settled before feed reads.
                sink = directory / 'sink'
                sink.mkdir(parents=True, exist_ok=True)
                sync_directory(directory)
                delivered = 0
                for _ in range(32):
                    with transaction(person, read_only=True) as (assembly, tx):
                        page = expect(success(assembly.read_feed_in_transaction(tx,
                            consumer_id='demo-sink')), FeedPage)
                    # This example applies the feed by retaining its exact payload in
                    # a durable local sink. Content-addressed writes make redelivery safe.
                    with (sink / (page.sha256 + '.json')).open('wb') as output:
                        output.write(page.content)
                        output.flush()
                        os.fsync(output.fileno())
                    sync_directory(sink)
                    with transaction(person) as (assembly, tx):
                        expect(success(assembly.acknowledge_feed_in_transaction(tx, page)), FeedAcknowledged)
                    if page.outcome == 'empty_interval':
                        break
                    delivered += 1
                else:
                    raise RuntimeError('Demo feed exceeded its finite delivery bound')
                if delivered < 1:
                    raise RuntimeError('Expected committed feed transactions')
                with transaction(person, read_only=True) as (assembly, tx):
                    caught_up = expect(success(assembly.reached_in_transaction(tx, token, consumer_id='demo-sink')), ReceiptIncluded)
                    if not caught_up.included:
                        raise RuntimeError('Committed feed ACK did not include the receipt')
                return {'catalog': 'accepted', 'mutation': 'committed', 'replay': 'committed',
                        'receipt': 'included', 'query': 'relationship', 'dry_run': 'rolled_back',
                        'import': 'created', 'feed_transactions': delivered, 'ack': 'committed'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, help='New empty local demo directory')
    parser.add_argument('--bun', default='bun', dest='bun_executable')
    arguments = parser.parse_args()
    print(json.dumps(run_workflow(arguments.directory, bun_executable=arguments.bun_executable), indent=2))
