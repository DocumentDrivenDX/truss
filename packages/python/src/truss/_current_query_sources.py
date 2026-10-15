"""Private current-query original-source storage; no query or Subject permit.

Installation requires the direct trusted administrator and administrative DDL
quiescence. Capture requires a trusted private executor holding the native cuts;
raw archive access is never granted to an ordinary person by this module.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
import struct
from ._current_query_pipe import _envelope
from ._installation_privileges import installation_administrator_with_cursor
from ._security_catalog_assessment import capture_accepted_catalog
from ._security_graph_source import acquire_graph_source_catalog_cut
from ._security_catalog_subject_installation import _text_rows
from .catalog_runtime import _pin_cursor, _release
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost

_PROFILE = 'truss-current-query-sources/0.1-candidate'
_NAMES = ('current-query:accepted-assessment', 'current-query:accepted-request',
          'current-query:initialize', 'current-query:release')


@dataclass(frozen=True, slots=True)
class CurrentQuerySourceRegistration:
    installation_id: str
    source_receipt: str
    accepted_revision: str
    status: str = 'pending_commit'


@dataclass(frozen=True, slots=True)
class CurrentQuerySourceCapture:
    installation_id: str
    source_receipt: str
    accepted_revision: str
    initialize_bytes: bytes
    accepted_request_bytes: bytes
    accepted_assessment_bytes: bytes


def _initialize(raw):
    if type(raw) is not bytes or not 1 <= len(raw) <= 4 * 1024 * 1024:
        raise ValueError('Bounded original initialize body required')
    envelope = _envelope(raw)
    if set(envelope) != {'kind', 'requestId', 'sources'} or envelope['kind'] != 'initialize':
        raise ValueError('Closed original initialize envelope required')
    sources = envelope['sources']
    if type(sources) is not dict or set(sources) != {
            'policy', 'catalog', 'closure', 'ontology', 'associationBindings', 'extensionSelection'}:
        raise ValueError('Closed original initialize sources required')
    # Only transport structure is inspected here. The original UMF producer
    # must still admit all semantic content before any protected computation.
    return sha256(struct.pack('>I', len(raw)) + raw).hexdigest()


def _inventory_digest(archives):
    # Bind every original artifact, not merely the accepted-catalog assessment.
    inventory = [{'role':role, 'identity':name, 'sha256':sha256(raw).hexdigest(),
                  'bytes':len(raw)} for role,name,raw in sorted(archives, key=lambda row:row[1])]
    return sha256(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _runtime(cursor):
    manifest, digest, _ = _release()
    release = files('truss').joinpath('_catalog_runtime', 'manifest.json').read_bytes()
    if sha256(release).hexdigest() != digest:
        raise ValueError('Original installed release bytes required')
    rows = _text_rows(cursor, 'SELECT installation_id::pg_catalog.text,release_id::pg_catalog.text,release_sha256::pg_catalog.text FROM truss.runtime_current_installation()', limit=1)
    if len(rows) != 1 or rows[0][1:] != (manifest['releaseId'], digest):
        raise ValueError('Original current-query runtime release required')
    return rows[0][0], manifest, digest, release


def _target(cursor):
    rows = _text_rows(cursor, "SELECT d.oid::pg_catalog.text,d.datname::pg_catalog.text,n.oid::pg_catalog.text FROM pg_catalog.pg_database d CROSS JOIN pg_catalog.pg_namespace n WHERE d.datname OPERATOR(pg_catalog.=) pg_catalog.current_database() AND n.nspname OPERATOR(pg_catalog.=) 'truss'", limit=1)
    if len(rows) != 1:
        raise ValueError('Original current-query database and namespace required')
    return json.dumps({'databaseOid':rows[0][0], 'databaseName':rows[0][1],
                       'schemaOid':rows[0][2]}, sort_keys=True, separators=(',', ':'))


def _capture_current_query_sources(cursor):
    """Read stored originals on a private cursor, never authenticate a caller.

    Table cuts remain held until the host settles its outer transaction. This
    component does not install epoch/Subject/fact or final release admission.
    """
    cursor.execute('LOCK TABLE ONLY truss.source_epoch_current,truss.source_epoch_registry IN SHARE MODE NOWAIT', prepare=False)
    cursor.execute('LOCK TABLE ONLY truss.installation_marker IN SHARE MODE NOWAIT', prepare=False)
    acquire_graph_source_catalog_cut(cursor)
    cursor.execute('LOCK TABLE ONLY truss.installation_archive IN SHARE MODE NOWAIT', prepare=False)
    cursor.execute('SELECT (SELECT count(*) FROM truss.source_epoch_current),(SELECT count(*) FROM truss.source_epoch_registry)', prepare=False)
    if cursor.fetchmany(2) != [(0,0)]:
        raise ValueError('Current-query epoch issuer is not composed by source-only capture')
    identity, manifest, digest, release = _runtime(cursor)
    markers = _text_rows(cursor, "SELECT marker_interface_version::pg_catalog.text,installation_id::pg_catalog.text,layout_version::pg_catalog.text,pg_catalog.encode(bundle_sha256,'hex'),inventory_profile::pg_catalog.text,pg_catalog.encode(inventory_sha256,'hex'),database_identity::pg_catalog.text,schema_name::pg_catalog.text FROM ONLY truss.installation_marker WHERE singleton_id OPERATOR(pg_catalog.=) 1", limit=1)
    if len(markers) != 1 or markers[0][:5] != ('truss-bootstrap-marker/0.1.0', identity, manifest['releaseId'], digest, _PROFILE) or markers[0][6:] != (_target(cursor), 'truss'):
        raise ValueError('Original current-query source marker required')
    # Bound the complete physical census before retrieving bytea payloads.
    cursor.execute('SELECT count(*),coalesce(sum(octet_length(artifact_bytes)),0)::bigint FROM ONLY truss.installation_archive', prepare=False)
    if cursor.description is None or tuple(d.type_code for d in cursor.description) != (20,20):
        raise ValueError('Exact source census descriptors required')
    counts = cursor.fetchmany(2)
    if len(counts) != 1 or any(type(v) is not int for v in counts[0]) or counts[0][0] != 4 or not 1 <= counts[0][1] <= 32 * 1024 * 1024:
        raise ValueError('Bounded complete current-query archive required')
    cursor.execute('SELECT artifact_role,artifact_identity,artifact_bytes,artifact_sha256,artifact_identity_sha256,installation_id FROM ONLY truss.installation_archive ORDER BY artifact_identity COLLATE pg_catalog."C"', prepare=False, binary=False)
    if cursor.description is None or tuple(d.type_code for d in cursor.description) != (25,25,17,17,17,25):
        raise ValueError('Exact original source archive descriptors required')
    rows = cursor.fetchmany(5)
    if len(rows) != 4 or tuple(row[1] for row in rows) != _NAMES:
        raise ValueError('Complete original current-query source inventory required')
    for role, name, raw, content_hash, name_hash, installed in rows:
        if (type(raw) is not bytes or type(content_hash) is not bytes or type(name_hash) is not bytes
                or not 1 <= len(raw) <= 16 * 1024 * 1024
                or sha256(raw).digest() != content_hash or sha256(name.encode()).digest() != name_hash
                or installed != identity or role != ('bundle' if name.endswith(':release') else 'expected_inventory' if name.endswith(':accepted-assessment') else 'input')):
            raise ValueError('Original current-query source bytes required')
    assessment, request, initialize, stored_release = (row[2] for row in rows)
    if stored_release != release or _inventory_digest([(row[0],row[1],row[2]) for row in rows]) != markers[0][5]:
        raise ValueError('Original current-query release and assessment required')
    receipt = _initialize(initialize)
    if capture_accepted_catalog(cursor, request, existing_source_cut=True) != assessment:
        raise ValueError('Current-query accepted catalog changed; re-registration required')
    # Revision is read natively, never taken from a caller's assessment field.
    revision = _text_rows(cursor, 'SELECT rev::pg_catalog.text FROM truss.schema_head WHERE id=1', limit=1)
    if len(revision) != 1:
        raise ValueError('Original current-query catalog head required')
    return CurrentQuerySourceCapture(identity, receipt, revision[0][0], initialize, request, assessment)


def capture_current_query_sources_with_cursor(cursor):
    """Capture originals under native cuts; preserve the caller search path."""
    _pin_cursor(cursor)
    if _text_rows(cursor, "SELECT pg_catalog.current_setting('server_version_num')::pg_catalog.text,pg_catalog.current_setting('transaction_isolation')::pg_catalog.text,pg_catalog.current_setting('transaction_read_only')::pg_catalog.text", limit=1) != [('180006','read committed','off')]:
        raise ValueError('Current-query capture requires PG18.6 read-write READ COMMITTED')
    prior = _text_rows(cursor, "SELECT pg_catalog.current_setting('search_path')::pg_catalog.text", limit=1)
    if len(prior) != 1:
        raise ValueError('Original source capture search path required')
    cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)", prepare=False)
    captured = _capture_current_query_sources(cursor)
    cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)", (prior[0][0],), prepare=False)
    if cursor.fetchmany(2) != prior:
        raise ValueError('Original source capture search path restoration required')
    return captured


def register_current_query_sources_in_transaction(host, transaction, *, initialize_bytes, accepted_request_bytes):
    """Fresh installer-only original-byte retention; caller owns commit/rollback."""
    if type(host) is not PsycopgHost:
        return Error(ExecutionFailure('execution_obligation', 'Original current-query installation host required'))
    try:
        _initialize(initialize_bytes)
        if type(accepted_request_bytes) is not bytes or not 1 <= len(accepted_request_bytes) <= 4_000_000:
            raise ValueError('Bounded original accepted source request required')
    except (ValueError, TypeError, KeyError, UnicodeError):
        return Error(ExecutionFailure('execution_obligation', 'Original bounded current-query source inputs required'))
    def install(cursor, observed):
        if observed[0][2:] != ('read_committed', 'read_write'):
            raise ValueError('Current-query registration requires a read-write READ COMMITTED transaction')
        _pin_cursor(cursor)
        prior = _text_rows(cursor, "SELECT pg_catalog.current_setting('search_path')::pg_catalog.text", limit=1)
        if len(prior) != 1:
            raise ValueError('Original source registration search path required')
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)", prepare=False)
        identity, manifest, digest, release = _runtime(cursor)
        installation_administrator_with_cursor(cursor)
        cursor.execute('LOCK TABLE ONLY truss.source_epoch_current,truss.source_epoch_registry IN SHARE ROW EXCLUSIVE MODE NOWAIT', prepare=False)
        cursor.execute('LOCK TABLE ONLY truss.installation_marker IN SHARE ROW EXCLUSIVE MODE NOWAIT', prepare=False)
        cursor.execute('SELECT owner_oid FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE NOWAIT', prepare=False)
        owner = cursor.fetchone()
        if owner is None:
            raise ValueError('Original current-query installation required')
        installation_administrator_with_cursor(cursor, owner[0])
        cursor.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR UPDATE NOWAIT', prepare=False)
        cursor.fetchmany(2)
        acquire_graph_source_catalog_cut(cursor)
        cursor.execute('LOCK TABLE ONLY truss.installation_archive IN SHARE ROW EXCLUSIVE MODE NOWAIT', prepare=False)
        cursor.execute('SELECT (SELECT count(*) FROM truss.installation_marker),(SELECT count(*) FROM truss.installation_archive),(SELECT count(*) FROM truss.source_epoch_current),(SELECT count(*) FROM truss.source_epoch_registry)', prepare=False)
        if cursor.fetchmany(2) != [(0,0,0,0)]:
            raise ValueError('Existing source registration requires explicit migration')
        assessment = capture_accepted_catalog(cursor, accepted_request_bytes, existing_source_cut=True)
        archives = (('expected_inventory',_NAMES[0],assessment),('input',_NAMES[1],accepted_request_bytes),('input',_NAMES[2],initialize_bytes),('bundle',_NAMES[3],release))
        inventory_digest = _inventory_digest(archives)
        cursor.execute("SELECT pg_catalog.clock_timestamp()::pg_catalog.text", prepare=False)
        clock = cursor.fetchone()[0]
        cursor.execute("INSERT INTO truss.installation_marker VALUES(1,'truss-bootstrap-marker/0.1.0',%s,%s,%s,%s,%s,%s,'truss',%s::timestamptz,%s)", (identity,manifest['releaseId'],bytes.fromhex(digest),_PROFILE,bytes.fromhex(inventory_digest),_target(cursor),clock,clock), prepare=False)
        for role, name, raw in archives:
            cursor.execute('INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES(%s,%s,%s,%s,%s)', (identity,role,name,raw,sha256(name.encode()).digest()), prepare=False)
        captured = capture_current_query_sources_with_cursor(cursor)
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)", (prior[0][0],), prepare=False)
        if cursor.fetchmany(2) != prior:
            raise ValueError('Original registration search path restoration required')
        return CurrentQuerySourceRegistration(identity, captured.source_receipt, captured.accepted_revision)
    return host._run_operation(transaction, install)
