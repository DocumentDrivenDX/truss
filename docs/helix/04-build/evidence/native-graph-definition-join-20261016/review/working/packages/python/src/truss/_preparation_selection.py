"""Excluded-administrator selection diagnostic, never a protected data entrypoint.

The trusted assessor supplies a dedicated RR/read-only connection. No ordinary
caller, permit, current-authority result or arbitrary SQL is accepted. Source
and writer closure remain obligations of the unfinished native guard.
"""
from dataclasses import dataclass
import psycopg
from psycopg.rows import tuple_row
from psycopg.types.string import StrDumper, TextLoader
from uuid import uuid4
from ._preparation_program import OriginalPreparationProgram, _json, _verify_home, _artifact, _encode
from ._preparation_compiler_replay import replay_preparation_program


@dataclass(frozen=True, slots=True)
class PreparationSelectionDiagnostic:
    program_id: int
    rows: tuple[tuple[str, ...], ...]
    original_lowering: bytes
    preflights_completed: int
    authority: bool = False
    security_ready: bool = False


def _parameters(statement):
    result = []
    for index, parameter in enumerate(statement['parameters'], 1):
        value = parameter['value']
        if (parameter['name'] != 'p'+str(index) or type(value) is not dict
                or set(value) != {'string'} or type(value['string']) is not str
                or '\x00' in value['string']):
            raise ValueError('Selected original string parameter profile required')
        # str is encoded by psycopg's text dumper, never numeric conversion.
        value['string'].encode('utf8')
        result.append(value['string'])
    return tuple(result)


def diagnose_preparation_selection(connection, *, program_id, native_module_path):
    """Execute original producer SQL unchanged with RawCursor's $n protocol.

    Caller owns transaction settlement. All population preflights precede any
    selector submission; no row escapes on a violation or overflow. The returned
    original lowering retains the complete typed column/parameter mapping.
    """
    if type(connection) is not psycopg.Connection or type(program_id) is not int or program_id <= 0:
        raise ValueError('Dedicated original diagnostic connection and program required')
    if connection.info.transaction_status != psycopg.pq.TransactionStatus.INTRANS:
        raise ValueError('Existing diagnostic transaction required')
    context_sql = "SELECT current_setting('server_version_num'),current_setting('transaction_isolation'),current_setting('transaction_read_only'),current_setting('client_encoding'),session_user=current_user,(SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname=session_user),pg_backend_pid(),pg_current_snapshot()::text"
    with connection.cursor(row_factory=tuple_row) as cursor:
        cursor.execute(context_sql)
        original_context = cursor.fetchone()
        if original_context[:6] != ('180006','repeatable read', 'on', 'UTF8', True, True):
            raise ValueError('Excluded PG18.6 superuser RR/read-only UTF8 diagnostic required')
        cursor.execute('SELECT owner_oid FROM truss.catalog_runtime_installation WHERE singleton')
        owners = cursor.fetchmany(2)
        if len(owners) != 1:
            raise ValueError('Original installation required')
        _verify_home(cursor, owners[0][0])
        cursor.execute('SELECT compiler_source_pin,original_configuration,original_request,original_plan_artifact,original_binding_artifact,original_lowering FROM ONLY truss.preparation_program_registration WHERE program_id=%s', (program_id,))
        rows = cursor.fetchmany(2)
        if len(rows) != 1:
            raise ValueError('Original enrolled program required')
        program = OriginalPreparationProgram(*rows[0])
    replay_preparation_program(program, native_module_path=native_module_path)
    lowering = _json(_json(program.lowering)['response'].encode('utf8'))
    binding = _artifact(_json(program.binding_artifact))
    with connection.cursor(row_factory=tuple_row) as cursor:
        cursor.execute('SELECT installation_id::text,release_id,release_sha256,(SELECT rev FROM truss.schema_head WHERE id=1) FROM truss.runtime_current_installation() WHERE singleton')
        if cursor.fetchmany(2) != [(binding['installationId'],binding['releaseId'],binding['releaseSha256'],binding['catalogRevision'])]:
            raise ValueError('Original selected installation/catalog binding required')
        for document in binding['documents']:
            cursor.execute('SELECT doc_revision,content_sha256 FROM truss.schema_doc WHERE doc_id=%s AND rev<=%s ORDER BY rev DESC LIMIT 1',(document['documentId'],binding['catalogRevision']))
            if cursor.fetchmany(2) != [(document['revision'],document['sha256'])]:
                raise ValueError('Original selected document binding required')
    maximum = lowering['bounds']['maxItems']
    if (lowering['bounds']['fetchLimit'] != maximum+1 or not 1 <= maximum <= 10000
            or lowering['ordering'] != {'kind':'native-integer-identity','direction':'asc'}):
        raise ValueError('Original bounded integer ordering required')
    with psycopg.RawCursor(connection, row_factory=tuple_row) as cursor:
        cursor.adapters.register_dumper(str,StrDumper)
        cursor.adapters.register_loader(25,TextLoader)
        completed = 0
        for preflight in lowering['preflight']:
            cursor.execute(preflight['sql'], _parameters(preflight), prepare=False)
            if (cursor.description is None or [(c.name,c.type_code) for c in cursor.description] != [('violations',25)]
                    or cursor.fetchmany(2) != [('0',)]):
                raise ValueError('Original complete-population preflight refused')
            completed += 1
    selected = []
    total_bytes = 0
    diagnostic_bytes = 2
    manifest_limit = _json(program.request)['limits']['maxManifestBytes']
    if diagnostic_bytes > manifest_limit:
        raise ValueError('Original manifest bound exceeded by diagnostic rows')
    with psycopg.RawServerCursor(connection,'truss_selection_'+uuid4().hex,row_factory=tuple_row,withhold=False) as cursor:
        cursor.adapters.register_dumper(str,StrDumper)
        cursor.adapters.register_loader(25,TextLoader)
        cursor.execute(lowering['sql'], _parameters(lowering))
        columns = lowering['columns']
        if (cursor.description is None or [(c.name,c.type_code) for c in cursor.description]
                != [(column['name'],25) for column in columns]):
            raise ValueError('Original text column mapping required')
        while True:
            batch = cursor.fetchmany(1)
            if not batch: break
            row = batch[0]
            if any(type(value) is not str for value in row):
                raise ValueError('Original non-null text selection required')
            total_bytes += sum(len(value.encode('utf8')) for value in row)
            if total_bytes > binding['maximumBytes']:
                raise ValueError('Original selection byte bound exceeded')
            diagnostic_bytes += len(_encode(row)) + (1 if selected else 0)
            if diagnostic_bytes > manifest_limit:
                raise ValueError('Original manifest bound exceeded by diagnostic rows')
            selected.append(row)
            if len(selected) > maximum:
                raise ValueError('Original selection overflow refused without trimming')
        previous = 0
        for row in selected:
            if any(type(value) is not str for value in row):
                raise ValueError('Original non-null text selection required')
            if (not row[0].isascii() or not row[0].isdecimal() or int(row[0]) <= previous
                    or str(int(row[0])) != row[0] or not row[1].isascii()
                    or not row[1].isdecimal() or int(row[1]) <= 0 or str(int(row[1])) != row[1]):
                raise ValueError('Original positive integer identity/version ordering required')
            previous = int(row[0])
    with connection.cursor(row_factory=tuple_row) as cursor:
        cursor.execute(context_sql)
        if cursor.fetchone() != original_context:
            raise ValueError('Original diagnostic transaction changed')
    return PreparationSelectionDiagnostic(program_id, tuple(selected), program.lowering, completed)
