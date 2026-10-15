"""Public current-policy query reference workflow on a fresh local PG18 runtime.

The adjacent original model/policy/designation is a reference fixture, not a
universal security configuration. Use a qualified exact Weft cohort and Bun1.4.2.
The activated profile is read-only; bootstrap writes happen before activation.
"""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path

import psycopg
from truss import (
    CatalogDocument, CatalogRuntimeConfiguration, CurrentQueryExecutor,
    LocalPostgres, ModuleAccessGrant, Ok, QueryRows,
    activate_current_query_protection_in_transaction, adopt_psycopg_host,
    create_reference_assembly, prepare_current_query_originals,
    register_current_query_sources_in_transaction,
    register_current_query_subjects_in_transaction,
)
from truss.contracts import BooleanValue, MapValue, TextValue
from truss.groups import AuthoredValue, CreateObject, GroupSuccess, RequestNone, RootlessOwnership


def success(result):
    if not isinstance(result, Ok):
        raise RuntimeError(f'Truss operation failed: {result!r}')
    return result.value


def expect(value, kind):
    if not isinstance(value, kind):
        raise RuntimeError(f'Expected {kind.__name__}, received {value!r}')
    return value


@contextmanager
def adopted(connection, *, commit=True):
    """Confirm host release before settlement; close an unusable owned connection."""
    connection.execute('BEGIN')
    host = adopt_psycopg_host(connection, statement_timeout_ms=10000, operation_timeout_ms=30000)
    try:
        tx = success(host.adopt_transaction())
        assembly = success(create_reference_assembly(CatalogRuntimeConfiguration(), host))
        yield host, tx, assembly
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


def original_sources():
    request = json.loads(Path(__file__).with_name('current-query-model-request.json').read_bytes())
    # Keep the exact original inner strings and pins; do not reserialize models.
    modules = [{'pin': m['pin'], 'documentJson': m['documentJson']} for m in request['modules']]
    documents = tuple(CatalogDocument(m['pin']['documentId'], m['pin']['revision'],
                                     m['documentJson'].encode('utf8')) for m in modules)
    opaque = request['opaqueSources']
    sources = {item['role']: json.loads(item['utf8']) for item in opaque}
    closure = {
        'pins': [{'documentId': m['pin']['documentId'], 'revision': m['pin']['revision']} for m in modules],
        'documents': [{'revision': m['pin']['revision'], 'document': json.loads(m['documentJson'])} for m in modules],
    }
    initialize = json.dumps({'kind': 'initialize', 'requestId': 'initialize', 'sources': {
        'policy': sources['policy'], 'catalog': sources['catalog'], 'ontology': sources['ontology'],
        'closure': closure, 'associationBindings': [], 'extensionSelection': None,
    }}, separators=(',', ':')).encode('utf8')
    accepted = json.dumps({'modules': modules}, separators=(',', ':')).encode('utf8')
    originals = prepare_current_query_originals(json.dumps(opaque, separators=(',', ':')).encode('utf8'))
    return documents, initialize, accepted, originals


def run_workflow(directory, *, bun_executable='bun'):
    directory = Path(directory).resolve()
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('The example requires a new or empty directory')
    directory.mkdir(parents=True, exist_ok=True)
    documents, initialize, accepted, originals = original_sources()
    with LocalPostgres(directory / 'postgres') as runtime:
        params = psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
        with psycopg.connect(**params, autocommit=True, options='-c statement_timeout=10000') as admin:
            with adopted(admin) as (_, tx, assembly):
                installed = success(assembly.install_in_transaction(tx))
            # Local development roles only. Production identity/bootstrap setup
            # remains the host's responsibility; no administrative data seeding.
            admin.execute('CREATE ROLE policy_person LOGIN')
            admin.execute('CREATE ROLE policy_reader NOLOGIN')
            admin.execute('CREATE ROLE policy_writer NOLOGIN')
            admin.execute(psycopg.sql.SQL('GRANT {} TO policy_person WITH SET FALSE').format(
                psycopg.sql.Identifier(installed.registrar_role)))
            person_params = dict(params, user='policy_person')
            with psycopg.connect(**person_params, autocommit=True, options='-c statement_timeout=10000') as person:
                with adopted(person) as (_, tx, assembly):
                    prepared = assembly.prepare_catalog(documents, source_version='0.8.0',
                                                        bun_executable=bun_executable)
                    success(assembly.accept_in_transaction(tx, prepared, request_key='reference-policy-model'))
                    view = success(assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())).view
                    types = {item.reference.authored_identity: item.reference for item in view.definitions
                             if item.reference.kind == 'type'}
                with adopted(admin) as (_, tx, assembly):
                    success(assembly.configure_module_access_in_transaction(tx, (
                        ModuleAccessGrant('domain', 'm', 'policy_reader', 'policy_writer'),)))
                admin.execute('GRANT policy_writer TO policy_person WITH SET FALSE')
                admin.execute(psycopg.sql.SQL('REVOKE {} FROM policy_person').format(
                    psycopg.sql.Identifier(installed.registrar_role)))
                records = [
                    ('Staff', {'staffId': 'alice'}),
                    ('Project', {'projectId': 'p1'}),
                    ('Resource', {'resourceId': 'r1', 'salary': 9007199254740993, 'token': 'opaque-one'}),
                    ('Resource', {'resourceId': 'r2', 'salary': 9007199254740993, 'token': 'opaque-two'}),
                    ('Ownership', {'ownerId': 'o1', 'ownerResource': 'r1', 'ownerProject': 'p1'}),
                    ('Assignment', {'assignmentId': 'a1', 'assignmentStaff': 'alice',
                                    'assignmentProject': 'p1', 'active': True}),
                ]
                operations = []
                for index, (record, fields) in enumerate(records):
                    values = tuple(AuthoredValue(name=name, value=(
                        BooleanValue(value=value) if type(value) is bool else
                        TextValue(kind='integer' if type(value) is int else 'string', text=str(value))))
                        for name, value in fields.items())
                    operations.append(CreateObject(type_definition_pin=types[record].definition_pin,
                        values=values, ownership=RootlessOwnership(), alias='record' + str(index)))
                with adopted(person) as (_, tx, assembly):
                    context = success(assembly.group_context_in_transaction(tx))
                    expect(success(assembly.apply_in_transaction(tx,
                        context.input(tuple(operations), MapValue(entries=())), RequestNone(),
                        documents=documents, bun_executable=bun_executable)), GroupSuccess)
            # The ordinary connection is closed. The host must keep all other
            # ordinary traffic/new connections stopped until activation commits.
            with adopted(admin) as (installer, tx, _):
                success(register_current_query_sources_in_transaction(installer, tx,
                    initialize_bytes=initialize, accepted_request_bytes=accepted, query_originals=originals))
                subjects = success(register_current_query_subjects_in_transaction(installer, tx,
                    bindings=(('policy_person', 'alice'),)))
                success(activate_current_query_protection_in_transaction(installer, tx,
                    subject_registration=subjects))
            # Begin a fresh dedicated private transaction after committed
            # activation. It has no previous business operation or assigned xid.
            with psycopg.connect(**person_params, autocommit=True, options='-c statement_timeout=10000') as person:
                with adopted(admin, commit=False) as (worker, worker_tx, _):
                    with adopted(person) as (_, tx, assembly):
                        executor = CurrentQueryExecutor(worker, worker_tx, subjects,
                                                        bun_executable=bun_executable)
                        rows = expect(success(assembly.query_current_in_transaction(tx,
                            executor=executor, sql='SELECT r.salary FROM Resource r WHERE r.salary=:minimum',
                            document_ids=('domain',), parameters={'minimum': 9007199254740993})), QueryRows)
                        if rows.columns != ('salary',) or rows.rows != (('[private]',),):
                            raise RuntimeError(f'Unexpected policy query result: {rows!r}')
            # Both transaction hosts are confirmed detached and settled before connections
            # or the owned local server close. Only the allowed public row leaves.
            return {'columns': list(rows.columns), 'rows': [list(row) for row in rows.rows]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--bun', default='bun')
    args = parser.parse_args()
    print(json.dumps(run_workflow(args.directory, bun_executable=args.bun)))
