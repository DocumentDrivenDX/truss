# SPDX-License-Identifier: MIT OR Apache-2.0
"""Truss quickstart.

Starts a private PostgreSQL 18 on a Unix socket, installs Truss, registers a UMF
document, creates two notes and an edge, looks one note up, runs a relationship
query, then reads and acknowledges the committed change feed.

    python quickstart.py ./truss-demo      # the directory must be new or empty

Prints one JSON object on success. `adopter_workflow.py` is the longer example
(receipts, replay, imports, dry-run).
"""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path

import psycopg
from truss import (
    CatalogDocument, CatalogRuntimeConfiguration, CapabilityAvailable, FeedAcknowledged, FeedPage,
    LocalPostgres, ModuleAccessGrant, ObjectFound, Ok, QueryRelatedKeys, QueryRows,
    adopt_psycopg_host, create_reference_assembly,
)
from truss.contracts import MapValue, TextValue
from truss.groups import (
    AliasObjectReference, AuthoredValue, CreateEdge, CreateObject, GroupSuccess, NullOrderKey,
    RootlessOwnership,
)


def success(result):
    if not isinstance(result, Ok):
        raise RuntimeError(f'Truss operation failed: {result!r}')
    return result.value


def expect(value, kind):
    if not isinstance(value, kind):
        raise RuntimeError(f'Expected {kind.__name__}, received {value!r}')
    return value


@contextmanager
def transaction(connection, *, read_only=False):
    """The caller begins and settles the transaction; Truss only adopts it."""
    connection.execute('BEGIN READ ONLY' if read_only else 'BEGIN')
    host = adopt_psycopg_host(connection, statement_timeout_ms=10000, operation_timeout_ms=30000)
    try:
        tx = success(host.adopt_transaction(access_mode='read_only' if read_only else 'read_write'))
        yield success(create_reference_assembly(CatalogRuntimeConfiguration(), host)), tx
    except BaseException:
        if host.detach():
            connection.rollback()
        else:
            connection.close()
        raise
    else:
        if not host.detach():
            connection.close()
            raise RuntimeError('Truss host release unavailable; connection closed')
        connection.commit()


def run(directory):
    directory = Path(directory).resolve()
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('The quickstart needs a new or empty directory')
    directory.mkdir(parents=True, exist_ok=True)
    documents = (CatalogDocument('notes', 'r1', Path(__file__).with_name('notes.umf.json').read_bytes()),)
    with LocalPostgres(directory / 'postgres') as runtime:
        params = psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
        options = '-c statement_timeout=10000'
        with psycopg.connect(**params, autocommit=True, options=options) as admin:
            # 1. Install the Truss schema (administrator).
            with transaction(admin) as (assembly, tx):
                installed = success(assembly.install_in_transaction(tx))
            admin.execute('CREATE ROLE demo_person LOGIN')
            admin.execute('CREATE ROLE demo_reader NOLOGIN')
            admin.execute('CREATE ROLE demo_writer NOLOGIN')
            admin.execute(psycopg.sql.SQL('GRANT {} TO demo_person WITH SET FALSE').format(
                psycopg.sql.Identifier(installed.registrar_role)))
            with psycopg.connect(**dict(params, user='demo_person'), autocommit=True, options=options) as person:
                # 2. Register the UMF document (a catalog registrar).
                with transaction(person) as (assembly, tx):
                    prepared = assembly.prepare_catalog(documents)
                    success(assembly.accept_in_transaction(tx, prepared, request_key='register-notes',
                                                           origin_bytes=b'{"x-action":"register"}'))
                    view = success(assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())).view
                    note = next(d.reference for d in view.definitions
                                if d.reference.kind == 'type' and d.reference.authored_identity == 'Note')
                # 3. Grant module access and register a feed consumer (administrator).
                with transaction(admin) as (assembly, tx):
                    success(assembly.configure_module_access_in_transaction(tx, (
                        ModuleAccessGrant('notes', 'notes', 'demo_reader', 'demo_writer'),)))
                    success(assembly.register_feed_consumer_in_transaction(
                        tx, consumer_id='demo-sink', reader_role='demo_reader'))
                admin.execute('GRANT demo_reader,demo_writer TO demo_person WITH SET FALSE')
                admin.execute(psycopg.sql.SQL('REVOKE {} FROM demo_person').format(
                    psycopg.sql.Identifier(installed.registrar_role)))

                def create(title):
                    return CreateObject(
                        type_definition_pin=note.definition_pin,
                        values=(AuthoredValue(name='title', value=TextValue(kind='string', text=title)),),
                        ownership=RootlessOwnership(), alias=title)

                # 4. Create two notes and an edge in one atomic group.
                with transaction(person) as (assembly, tx):
                    relation = success(assembly.get_relationship_reference_in_transaction(
                        tx, document_id='notes', module_id='notes', relationship_id='references'))
                    context = success(assembly.group_context_in_transaction(tx))
                    group = context.input((create('first'), create('second'), CreateEdge(
                        relationship_definition_pin=relation.definition_pin,
                        source=AliasObjectReference(alias='first'), target=AliasObjectReference(alias='second'),
                        values=(), order_key=NullOrderKey(), alias='link')), MapValue(entries=()))
                    expect(success(assembly.apply_in_transaction(
                        tx, group, context.request('create-two-notes'), documents=documents)), GroupSuccess)
                # 5. Look one up by key, then run a relationship query.
                with transaction(person, read_only=True) as (assembly, tx):
                    expect(success(assembly.lookup_key_in_transaction(
                        tx, document_id='notes', module_id='notes', record_id='Note', key_id='title-key',
                        values=('first',))), ObjectFound)
                    query = expect(assembly.compiled_execution(assembly.compiled_selection), CapabilityAvailable)
                    rows = expect(success(query.capability.query_in_transaction(
                        tx, sql='SELECT n.title,RELATED_KEYS(n.references,10) AS linked FROM Note n '
                                'WHERE HAS_RELATED(n.references,KEY(:title))',
                        document_ids=('notes',), parameters={'title': 'second'})), QueryRows)
                    if rows.rows != (('first', QueryRelatedKeys(items=(('second',),), truncated=False)),):
                        raise RuntimeError(f'Unexpected query result: {rows!r}')
                # 6. Read the committed change feed and acknowledge each page.
                delivered = 0
                for _ in range(32):
                    with transaction(person, read_only=True) as (assembly, tx):
                        page = expect(success(assembly.read_feed_in_transaction(tx, consumer_id='demo-sink')), FeedPage)
                    with transaction(person) as (assembly, tx):
                        expect(success(assembly.acknowledge_feed_in_transaction(tx, page)), FeedAcknowledged)
                    if page.outcome == 'empty_interval':
                        break
                    delivered += 1
                else:
                    raise RuntimeError('Feed did not drain within its bound')
                if delivered < 1:
                    raise RuntimeError('Expected at least one committed feed transaction')
    return {'catalog': 'accepted', 'mutation': 'committed', 'lookup': 'found', 'query': 'relationship',
            'feed_transactions': delivered, 'ack': 'committed'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('directory', type=Path, help='New or empty demo directory')
    print(json.dumps(run(parser.parse_args().directory)))
