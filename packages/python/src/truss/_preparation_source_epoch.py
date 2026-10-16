"""Private metadata-source bootstrap for ordinary accepted UMF catalogs.

Direct trusted superuser and quiescent initial installation are premises. This
profile covers catalog metadata and original runtime code, not action roles,
object facts, bulk selection programs, or a protected execution permit. Callers
own commit/rollback. Existing markers or epochs require explicit migration.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
import re
from .catalog_runtime import _release, _pin_cursor
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost
from ._installation_privileges import installation_administrator_with_cursor
from ._security_catalog_assessment import SOURCE_TABLES, capture_accepted_catalog
from ._security_source_epoch_installation import (
    PendingSourceEpochInfrastructure, _MANIFEST_SHA256, _sources, _verify,
)
from ._psycopg_epoch_cut import _EpochComparison

_PROFILE = 'truss.preparation-catalog-metadata-source/0.1'


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf8')


def _parameters(original):
    # Closed original release declarations only; never caller SQL interpretation.
    original = original.replace("convert_to('[]','UTF8')", '__empty_condition_keys__')
    result = []
    for part in original.split(',') if original.strip() else ():
        match = re.fullmatch(r'\s*(\w+)\s+([\w.]+(?:\[\])?)(?:\s+DEFAULT\s+(NULL|true|false|0|1|__empty_condition_keys__))?\s*', part)
        if match is None:
            raise ValueError('Unsupported original routine declaration')
        result.append(match.groups())
    return result


def _runtime_recipe(sources):
    result = []
    for source in sources:
        for match in re.finditer(r"CREATE FUNCTION\s+(truss\.\w+)\(([\s\S]*?)\)\s+RETURNS\s+([\s\S]*?)\bLANGUAGE\s+(sql|plpgsql)\s+([\s\S]*?)\bAS\s+(\$\$[\s\S]*?\$\$|'(?:[^']|'')*')\s*;", source):
            name, arguments, returns, language, attributes, body = match.groups()
            inputs = _parameters(arguments)
            returns = returns.strip()
            outputs = _parameters(returns[len('TABLE'):].strip()[1:-1]) if returns.startswith('TABLE') else []
            return_type = ('record' if len(outputs) > 1 else outputs[0][1]) if outputs else returns.removeprefix('SETOF ').strip()
            if not re.fullmatch(r'[\w.]+(?:\[\])?', return_type):
                raise ValueError('Unsupported original return declaration')
            settings = []
            for setting in re.finditer(r"\bSET\s+(\w+)\s*(?:=|TO)\s*([^\n]*?)(?=\s+SET\b|$)", attributes, re.IGNORECASE):
                key, value = setting.groups()
                key = 'TimeZone' if key.lower() == 'timezone' else key.lower()
                value = value.strip().strip("'")
                if key == 'search_path': value = ', '.join(p.strip() for p in value.split(','))
                settings.append(key + '=' + value)
            result.append(dict(name=name, inputs=inputs, outputs=outputs, returns=return_type,
                language=language, set=bool(outputs) or returns.startswith('SETOF '),
                security='SECURITY DEFINER' in attributes, strict=bool(re.search(r'\bSTRICT\b', attributes)),
                volatility='i' if 'IMMUTABLE' in attributes else 's' if 'STABLE' in attributes else 'v',
                parallel='s' if 'PARALLEL SAFE' in attributes else 'r' if 'PARALLEL RESTRICTED' in attributes else 'u',
                settings=settings or None, body=body[2:-2] if body.startswith('$$') else body[1:-1].replace("''", "'")))
    if len(result) != 203 or len({r['name'] for r in result}) != 203:
        raise ValueError('Complete original runtime routine recipe required')
    return result


def _runtime_inventory(cursor, sources, owner):
    recipe = _runtime_recipe(sources)
    result = []
    for expected in recipe:
        types = [p[1] for p in expected['inputs'] + expected['outputs']]
        types.append(expected['returns'])
        cursor.execute('SELECT pg_catalog.to_regtype(t)::pg_catalog.oid FROM pg_catalog.unnest(%s::pg_catalog.text[]) t', (types,), prepare=False)
        oids = [row[0] for row in cursor.fetchmany(len(types) + 1)]
        if len(oids) != len(types) or any(type(oid) is not int or oid <= 0 for oid in oids):
            raise ValueError('Original routine native types required')
        cursor.execute("""SELECT pg_catalog.to_jsonb(p)::pg_catalog.text,l.lanname::pg_catalog.text,
            pg_catalog.pg_get_expr(p.proargdefaults,0)::pg_catalog.text
            FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
            JOIN pg_catalog.pg_language l ON l.oid=p.prolang
            WHERE n.nspname='truss' AND p.proname=%s""", (expected['name'].split('.')[1],), prepare=False, binary=False)
        rows = cursor.fetchmany(2)
        if len(rows) != 1 or type(rows[0][0]) is not str:
            raise ValueError('Unique original runtime signature required')
        actual = json.loads(rows[0][0]); count = len(expected['inputs'])
        names = [p[0] for p in expected['inputs'] + expected['outputs']] or None
        all_types = [str(oid) for oid in oids[:-1]] if expected['outputs'] else None
        modes = ['i'] * count + ['t'] * len(expected['outputs']) if expected['outputs'] else None
        defaults = []
        aliases = {'int': 'integer', 'bool': 'boolean'}
        for _, typename, default in expected['inputs']:
            if default is None: continue
            defaults.append('NULL::' + aliases.get(typename, typename) if default == 'NULL' else
                "convert_to('[]'::text, 'UTF8'::name)" if default == '__empty_condition_keys__' else default)
        checks = dict(proowner=str(owner), prokind='f', prorettype=str(oids[-1]), proretset=expected['set'],
            proargtypes=[str(oid) for oid in oids[:count]], pronargs=count,
            proallargtypes=all_types, proargnames=names, proargmodes=modes, pronargdefaults=len(defaults),
            prosecdef=expected['security'], proisstrict=expected['strict'], provolatile=expected['volatility'],
            proparallel=expected['parallel'], proleakproof=False, prosupport='-', proconfig=expected['settings'], prosrc=expected['body'])
        # PG18 native JSON: OIDs are strings; oidvector is an OID-string array.
        if rows[0][1] != expected['language'] or rows[0][2] != (', '.join(defaults) if defaults else None) or any(actual.get(k) != v for k, v in checks.items()):
            raise ValueError('Original runtime body and execution attributes required: ' + expected['name'])
        cursor.execute("SELECT a.grantee,a.grantor,a.privilege_type,a.is_grantable FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE p.oid=%s::pg_catalog.oid ORDER BY a.grantee,a.grantor,a.privilege_type,a.is_grantable", (actual['oid'],), prepare=False)
        acl = cursor.fetchmany(257)
        if not acl or len(acl) > 256 or any(row[0] == 0 or row[1:] != (owner, 'EXECUTE', False) for row in acl):
            raise ValueError('Original private runtime execution ACL required')
        result.append(dict(signature=expected['name'] + '(' + ','.join(p[1] for p in expected['inputs']) + ')',
            oid=str(actual['oid']), owner=str(owner), bodySha256=sha256(expected['body'].encode()).hexdigest(), acl=acl))
    return _json({'profile': _PROFILE, 'routines': result, 'scope': 'original_runtime_code_and_private_acl_only'})


@dataclass(frozen=True, slots=True)
class PendingPreparationSourceMarker:
    installation_id: str
    release_sha256: str
    target_incarnation: bytes
    source_request: bytes
    assessment: bytes
    routines: bytes
    status: str = 'pending_commit'
    security_ready: bool = False


@dataclass(frozen=True, slots=True)
class PendingPreparationSourceEpoch:
    comparison: _EpochComparison
    status: str = 'pending_commit'
    security_ready: bool = False


def _archives(marker, release):
    return [('bundle', 'preparation:original-runtime-release', release),
        ('input', 'preparation:original-catalog-documents', marker.source_request),
        ('input', 'preparation:target-incarnation', marker.target_incarnation),
        ('expected_inventory', 'preparation:accepted-catalog', marker.assessment),
        ('installed_inventory', 'preparation:runtime-routines', marker.routines)]


def _lock(cursor):
    # Native issuer will write these homes; SHARE would forbid its own issuance.
    cursor.execute('LOCK TABLE truss.source_epoch_current,truss.source_epoch_registry IN ROW EXCLUSIVE MODE NOWAIT', prepare=False)
    cursor.execute('SELECT singleton_id FROM truss.installation_marker FOR UPDATE NOWAIT', prepare=False)
    cursor.fetchmany(2)
    for name in SOURCE_TABLES:
        cursor.execute('LOCK TABLE ONLY truss.' + name + ' IN SHARE MODE NOWAIT', prepare=False)
    cursor.execute('LOCK TABLE ONLY truss.installation_archive IN SHARE MODE NOWAIT', prepare=False)


def _context(cursor):
    _pin_cursor(cursor)
    cursor.execute("SELECT pg_catalog.current_setting('search_path')", prepare=False)
    rows = cursor.fetchmany(2)
    if len(rows) != 1 or type(rows[0][0]) is not str: raise ValueError('Original source installer path required')
    path = rows[0][0]
    cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)", prepare=False)
    cursor.fetchmany(2)
    cursor.execute("SELECT pg_catalog.current_setting('server_version_num'),pg_catalog.current_setting('transaction_isolation'),pg_catalog.current_setting('transaction_read_only'),pg_catalog.current_setting('event_triggers')", prepare=False)
    if cursor.fetchmany(2) != [('180006', 'read committed', 'off', 'on')]: raise ValueError('PG18.6 direct source installer transaction required')
    _lock(cursor)
    cursor.execute('SELECT installation_id::pg_catalog.text,owner_oid FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE NOWAIT', prepare=False)
    rows = cursor.fetchmany(2)
    if len(rows) != 1: raise ValueError('Original catalog installation required')
    identity, owner = rows[0]
    actor = installation_administrator_with_cursor(cursor, owner)
    if not actor[2]: raise ValueError('Direct superuser source installer required')
    cursor.execute('SELECT rolcanlogin,rolsuper,rolcreaterole,rolcreatedb,rolreplication,rolbypassrls FROM pg_catalog.pg_roles WHERE oid=%s::pg_catalog.oid', (owner,), prepare=False)
    if cursor.fetchmany(2) != [(False,False,False,False,False,False)]: raise ValueError('Original unprivileged runtime owner required')
    return path, identity, owner, actor[0]


def _restore(cursor, path):
    cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)", (path,), prepare=False)
    if cursor.fetchmany(2) != [(path,)]: raise ValueError('Original source installer path restoration required')


def bootstrap_preparation_source_marker_in_transaction(host, transaction):
    if type(host) is not PsycopgHost:
        return Error(ExecutionFailure('execution_obligation', 'Original native source installer required'))
    manifest, digest, sources = _release()
    release = files('truss').joinpath('_catalog_runtime', 'manifest.json').read_bytes()
    def install(cursor, observed):
        path, identity, owner, actor = _context(cursor)
        cursor.execute('SELECT (SELECT count(*) FROM truss.installation_marker),(SELECT count(*) FROM truss.installation_archive),(SELECT count(*) FROM truss.source_epoch_current),(SELECT count(*) FROM truss.source_epoch_registry)', prepare=False)
        if cursor.fetchmany(2) != [(0,0,0,0)]: raise ValueError('Existing source metadata requires explicit migration')
        routines = _runtime_inventory(cursor, sources, owner)
        cursor.execute('SELECT doc_id,doc_revision,umf_version,content_sha256,document FROM (SELECT DISTINCT ON (doc_id) * FROM truss.schema_doc ORDER BY doc_id,rev DESC,ord DESC) d ORDER BY doc_id', prepare=False)
        rows = cursor.fetchmany(257)
        if not rows or len(rows) > 256 or any(any(type(v) is not str for v in row) for row in rows): raise ValueError('Bounded current accepted documents required')
        request = _json({'modules': [dict(pin=dict(documentId=a, revision=b, umfVersion=c, sha256=d), documentJson=e) for a,b,c,d,e in rows]})
        if not 1 <= len(request) <= 4_000_000: raise ValueError('Bounded complete accepted documents required')
        assessment = capture_accepted_catalog(cursor, request, existing_source_cut=True)
        if len(assessment) > 1048576 or len(routines) > 1048576: raise ValueError('Source issuer evidence bound exceeded')
        cursor.execute("SELECT d.oid::pg_catalog.text,d.datname::pg_catalog.text,n.oid::pg_catalog.text,pg_catalog.clock_timestamp()::pg_catalog.text FROM pg_catalog.pg_database d CROSS JOIN pg_catalog.pg_namespace n WHERE d.datname=pg_catalog.current_database() AND n.nspname='truss'", prepare=False)
        rows = cursor.fetchmany(2)
        if len(rows) != 1 or any(type(v) is not str for v in rows[0]): raise ValueError('Original catalog namespace required')
        db_oid, db_name, schema_oid, clock = rows[0]
        incarnation = _json(dict(interfaceVersion='truss-catalog-source-target/0.1.0', databaseOid=db_oid, schemaOid=schema_oid))
        marker = PendingPreparationSourceMarker(identity, digest, incarnation, request, assessment, routines)
        cursor.execute("INSERT INTO truss.installation_marker VALUES(1,'truss-bootstrap-marker/0.1.0',%s,%s,%s,%s,%s,%s,'truss',%s::pg_catalog.timestamptz,%s)", (identity,manifest['releaseId'],bytes.fromhex(digest),_PROFILE,sha256(assessment).digest(),_json(dict(databaseOid=db_oid,databaseName=db_name)).decode(),clock,clock), prepare=False)
        for role, name, raw in _archives(marker, release):
            cursor.execute('INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES(%s,%s,%s,%s,%s)', (identity,role,name,raw,sha256(name.encode()).digest()), prepare=False)
        _verify_marker(cursor, marker, release, manifest)
        _restore(cursor, path)
        return marker
    return host._run_operation(transaction, install)


def _verify_marker(cursor, marker, release, manifest):
    cursor.execute("SELECT d.oid::pg_catalog.text,d.datname::pg_catalog.text,n.oid::pg_catalog.text FROM pg_catalog.pg_database d CROSS JOIN pg_catalog.pg_namespace n WHERE d.datname=pg_catalog.current_database() AND n.nspname='truss'", prepare=False)
    rows = cursor.fetchmany(2)
    if len(rows) != 1 or any(type(v) is not str for v in rows[0]): raise ValueError('Original current source target required')
    db_oid, db_name, schema_oid = rows[0]
    incarnation = _json(dict(interfaceVersion='truss-catalog-source-target/0.1.0', databaseOid=db_oid, schemaOid=schema_oid))
    if marker.target_incarnation != incarnation: raise ValueError('Actual current database/schema source incarnation required')
    cursor.execute('SELECT marker_interface_version,installation_id,layout_version,bundle_sha256,inventory_profile,inventory_sha256,database_identity,schema_name FROM truss.installation_marker WHERE singleton_id=1 FOR UPDATE NOWAIT', prepare=False)
    if cursor.fetchmany(2) != [('truss-bootstrap-marker/0.1.0',marker.installation_id,manifest['releaseId'],bytes.fromhex(marker.release_sha256),_PROFILE,sha256(marker.assessment).digest(),_json(dict(databaseOid=db_oid,databaseName=db_name)).decode(),'truss')]: raise ValueError('Exact metadata source marker required')
    cursor.execute('SELECT installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_sha256,artifact_identity_sha256 FROM truss.installation_archive ORDER BY artifact_identity COLLATE pg_catalog."C"', prepare=False)
    expected = sorted([(marker.installation_id,role,name,raw,sha256(raw).digest(),sha256(name.encode()).digest()) for role,name,raw in _archives(marker, release)], key=lambda row: row[2])
    if cursor.fetchmany(len(expected)+1) != expected: raise ValueError('Exact metadata source archives required')


def issue_initial_preparation_source_epoch_in_transaction(host, transaction, *, marker, infrastructure):
    if type(host) is not PsycopgHost or type(marker) is not PendingPreparationSourceMarker or type(infrastructure) is not PendingSourceEpochInfrastructure:
        return Error(ExecutionFailure('execution_obligation', 'Original metadata source inputs required'))
    manifest, digest, sources = _release()
    release = files('truss').joinpath('_catalog_runtime', 'manifest.json').read_bytes()
    if marker.release_sha256 != digest or infrastructure.installation_id != marker.installation_id or infrastructure.source_manifest_sha256 != _MANIFEST_SHA256 or marker.security_ready is not False or infrastructure.security_ready is not False:
        return Error(ExecutionFailure('execution_obligation', 'Matching metadata source installation required'))
    def issue(cursor, observed):
        path, identity, owner, actor = _context(cursor)
        if identity != marker.installation_id: raise ValueError('Original metadata source installation required')
        # Marker row lock precedes source recapture and holds through native issuance.
        _verify_marker(cursor, marker, release, manifest)
        _verify(cursor, _sources(), actor)
        if _runtime_inventory(cursor, sources, owner) != marker.routines or capture_accepted_catalog(cursor, marker.source_request, existing_source_cut=True) != marker.assessment: raise ValueError('Current original metadata source correspondence required')
        cursor.execute('SELECT (SELECT count(*) FROM truss.source_epoch_current),(SELECT count(*) FROM truss.source_epoch_registry)', prepare=False)
        if cursor.fetchmany(2) != [(0,0)]: raise ValueError('Existing source epoch requires migration')
        profile = _json(dict(interfaceVersion=_PROFILE, scope='accepted_catalog_metadata_and_original_runtime_only', releaseSha256=digest,
            assessmentSha256=sha256(marker.assessment).hexdigest(), routinesSha256=sha256(marker.routines).hexdigest(), authority=False, businessFacts=False, registeredSelectionPrograms=False))
        evidence = _json(dict(interfaceVersion=_PROFILE, archives=[dict(role=r,identity=n,sha256=sha256(raw).hexdigest()) for r,n,raw in _archives(marker,release)]))
        if len(profile) > 65536 or len(evidence) > 1048576 or not 1 <= len(marker.target_incarnation) <= 1024: raise ValueError('Bounded original metadata epoch inputs required')
        cursor.execute('SELECT truss.runtime_issue_source_epoch(%s,NULL,%s,%s,%s)', (identity,marker.target_incarnation.decode(),profile,evidence), prepare=False)
        rows = cursor.fetchmany(2)
        if len(rows) != 1 or type(rows[0][0]) is not str: raise ValueError('Original native source epoch issuance required')
        epoch = rows[0][0]
        cursor.execute('SELECT r.installation_id,r.source_epoch,r.target_incarnation,r.predecessor_epoch,r.transition_reason,r.profile_bytes,r.evidence_bytes FROM truss.source_epoch_registry r JOIN truss.source_epoch_current c ON c.installation_id=r.installation_id AND c.source_epoch=r.source_epoch WHERE c.singleton_id=1', prepare=False)
        if cursor.fetchmany(2) != [(identity,epoch,marker.target_incarnation.decode(),None,'initial',profile,evidence)]: raise ValueError('Exact original issued metadata epoch readback required')
        _restore(cursor, path)
        return PendingPreparationSourceEpoch(_EpochComparison(identity,epoch,marker.target_incarnation.decode(),profile,evidence))
    return host._run_operation(transaction, issue)
