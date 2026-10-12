"""Owned flat identity read spike within one host operation; no public authority.

UMF owns decoding, keys and policy semantics. Administrative issuer/mapping and
trusted=true remain fixture premises. This tool never exposes raw cells as output.
"""
from pathlib import Path
from dataclasses import asdict,dataclass
import hashlib,json,subprocess
from truss._psycopg_dependency_fact_cut import (_epoch_dependency_recipe,_OriginalFactSources,
    _inspect_original_fact_sources,_capture_dependency_relation_cells,_run_dependency_fact_operation,_verify_native_profile_caller)
ROOT=Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class _OwnedEvaluatorSourcePins:
    tool: Path
    pins: tuple


def _pin_owned_evaluator_sources():
    """Private administrative source snapshot, never an authority capability."""
    tool=ROOT/'scripts/evaluate-security-captured-identity-fixture.ts'
    owner=Path('/Users/erik/.codex/worktrees/security-main-integration/umf')
    paths=[tool]+[p for p in (owner/'src').rglob('*') if p.is_file() and p.suffix in ('.ts','.json')]+[owner/'tests/security/fixture.ts']
    return _OwnedEvaluatorSourcePins(tool,tuple((p,hashlib.sha256(p.read_bytes()).digest()) for p in paths))


def _run_owned_identity_read(host, transaction, epoch, requirements, sources, delegated=False, caller_database=None, evaluator_sources=None):
    if type(sources) is not _OriginalFactSources:raise ValueError('Original fixture sources required')
    sources=_OriginalFactSources(sources.policy,sources.resolution)
    digest=hashlib.sha256(requirements).hexdigest()
    _inspect_original_fact_sources(requirements,digest,sources)
    selected,providers=_epoch_dependency_recipe(epoch,digest,sources)
    profile=json.loads(selected.profile)
    if profile['kind'] not in ('truss-flat-fact-provider-fixture/0.2','truss-flat-fact-provider-fixture/0.3','truss-flat-fact-provider-fixture/0.4'):
        raise ValueError('Original source-bound fixture profile required')
    if profile['kind'].endswith('/0.4')!=delegated:
        raise ValueError('Original delegated caller scope required')
    groups={}
    for p in providers:
        group=groups.setdefault(p.relation.oid,{'relation':p.relation,'fields':[],'associations':[]})
        if p.kind=='field':
            c=p.column
            if c is None or c.type_oid not in (16,20,25) or c.generated!='':raise ValueError('Ordinary native fixture column required')
            group['fields'].append((p.reference,c))
        else:group['associations'].append(p.reference)
    if len(groups)>32 or any(len(g['fields'])>32 for g in groups.values()):raise ValueError('Bounded fixture capture required')
    prepared=_pin_owned_evaluator_sources() if evaluator_sources is None else evaluator_sources
    if type(prepared) is not _OwnedEvaluatorSourcePins:raise ValueError('Original private evaluator preparation required')
    tool,pins=prepared.tool,dict(prepared.pins)
    def execute(cursor):
        caller=profile.get('caller')
        if caller_database is not None:
            cursor.execute('SELECT oid::pg_catalog.text FROM pg_catalog.pg_database WHERE datname OPERATOR(pg_catalog.=) pg_catalog.current_database()',prepare=False,binary=False)
            if cursor.description is None or len(cursor.description)!=1 or cursor.description[0].type_code!=25 or cursor.fetchmany(2)!=[caller_database]:
                raise ValueError('Original caller/executor database correspondence required')
        _verify_native_profile_caller(cursor,json.dumps({'caller':profile['executor']}).encode() if delegated else selected.profile)
        cells=_capture_dependency_relation_cells(cursor,groups)
        captured=[asdict(c) for c in cells]
        payload=json.dumps(captured if caller is None else {'cells':captured,'subjectKey':caller['subjectKey']})
        if len(payload.encode('utf8'))>1048576:raise ValueError('Bounded semantic fixture input required')
        try:
            result=subprocess.run(['/opt/homebrew/bin/bun',str(tool)],cwd=ROOT,input=payload,capture_output=True,text=True,timeout=4)
        except subprocess.TimeoutExpired:
            raise TimeoutError('Original evaluator deadline expired') from None
        if result.returncode or len(result.stdout.encode('utf8'))>65536:raise ValueError('Original UMF fixture evaluation refused')
        if any(hashlib.sha256(p.read_bytes()).digest()!=h for p,h in pins.items()):raise ValueError('Original evaluator sources changed')
        receipt=json.loads(result.stdout)
        if type(receipt) is not dict or set(receipt)!= {'decision','identities'}:raise ValueError('Original fixture decision envelope required')
        decision=receipt['decision']
        if type(decision) is not dict or decision.get('decision') not in ('permit','deny'):raise ValueError('Determinate fixture decision required')
        # No raw cells, private fact identities or evaluator diagnostics leave
        # this owned operation. Dispositions remain original UMF output.
        return decision
    return _run_dependency_fact_operation(host,transaction,selected,requirements,digest,providers,execute)


def run_owned_identity_read(host, transaction, epoch, requirements, sources):
    return _run_owned_identity_read(host,transaction,epoch,requirements,sources)


def _exclude_native_private_fact_privileges(cursor, providers):
    """Conservative native caller privilege snapshot, not complete call closure."""
    oids=tuple(sorted({p.relation.oid for p in providers}))
    cursor.execute("SELECT r.oid::pg_catalog.text FROM pg_catalog.pg_roles r "
                   "WHERE (pg_catalog.pg_has_role(session_user,r.oid,'SET') OR pg_catalog.pg_has_role(current_user,r.oid,'SET')) "
                   "AND (r.rolsuper OR r.rolcreaterole OR r.rolbypassrls "
                   "OR EXISTS(SELECT 1 FROM pg_catalog.pg_proc p WHERE p.prosecdef AND pg_catalog.has_function_privilege(r.oid,p.oid,'EXECUTE')) "
                   "OR EXISTS(SELECT 1 FROM pg_catalog.unnest(%s::pg_catalog.oid[]) f(oid) WHERE "
                   "pg_catalog.has_table_privilege(r.oid,f.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN') "
                   "OR pg_catalog.has_any_column_privilege(r.oid,f.oid,'SELECT,INSERT,UPDATE,REFERENCES'))) LIMIT 1",
                   ('{'+','.join(str(v) for v in oids)+'}',),prepare=False,binary=False)
    rows=cursor.fetchmany(2)
    if (cursor.description is None or len(cursor.description)!=1
            or cursor.description[0].type_code!=25 or rows!=[]):
        raise ValueError('Original private fact privilege exclusion required')


def run_delegated_owned_identity_read(caller_host, caller_transaction, executor_host, executor_transaction, epoch, requirements, sources):
    """Trusted service spike: actual caller scope encloses executor operation.

    Both host references belong to the trusted application, never request claims.
    Endpoint/database correspondence is not independent server authentication.
    Executor credentials, mapping issuer and final release remain unqualified.
    """
    if caller_host is executor_host:raise ValueError('Separate original caller/executor hosts required')
    selected,providers=_epoch_dependency_recipe(epoch,hashlib.sha256(requirements).hexdigest(),sources)
    if not json.loads(selected.profile)['kind'].endswith('/0.4'):raise ValueError('Original delegated profile required')
    prepared=_pin_owned_evaluator_sources()
    left,right=caller_host.connection.info,executor_host.connection.info
    if (left.host,left.port,left.dbname)!=(right.host,right.port,right.dbname):raise ValueError('Original configured endpoint correspondence required')
    def capture(cursor,observed):
        from truss._psycopg_epoch_cut import _exclude_native_predefined_role_reachability
        _exclude_native_predefined_role_reachability(cursor)
        _exclude_native_private_fact_privileges(cursor,providers)
        _verify_native_profile_caller(cursor,selected.profile)
        cursor.execute('SELECT oid::pg_catalog.text FROM pg_catalog.pg_database WHERE datname OPERATOR(pg_catalog.=) pg_catalog.current_database()',prepare=False,binary=False)
        database=cursor.fetchone()
        if database is None or len(database)!=1:raise ValueError('Original caller database observation required')
        result=_run_owned_identity_read(executor_host,executor_transaction,selected,requirements,sources,delegated=True,caller_database=database,evaluator_sources=prepared)
        # Return only a successful original executor decision. The outer caller
        # operation still confirms its native custody before publication.
        from truss.execution import Ok
        if type(result) is not Ok:raise ValueError('Original executor operation refused')
        def retained(executor_cursor,executor_observed):
            # Observe existing locks only: do not reacquire a lost guard and
            # accidentally bless an earlier decision under a new data cut.
            required=tuple(sorted({p.relation.oid for p in providers}))
            executor_cursor.execute("SELECT count(*)::pg_catalog.text FROM pg_catalog.pg_locks WHERE pid OPERATOR(pg_catalog.=) pg_catalog.pg_backend_pid() AND granted AND mode OPERATOR(pg_catalog.=) 'ShareLock' AND relation OPERATOR(pg_catalog.=) ANY(%s::pg_catalog.oid[])",('{'+','.join(str(v) for v in required)+'}',),prepare=False,binary=False)
            if executor_cursor.description is None or len(executor_cursor.description)!=1 or executor_cursor.description[0].type_code!=25 or executor_cursor.fetchmany(2)!=[(str(len(required)),)]:
                raise ValueError('Original native fact guards unavailable at release')
            executor_cursor.execute("SELECT count(*)::pg_catalog.text FROM pg_catalog.pg_locks WHERE pid OPERATOR(pg_catalog.=) pg_catalog.pg_backend_pid() AND granted AND mode OPERATOR(pg_catalog.=) 'ShareLock' AND relation IN ('truss.source_epoch_current'::pg_catalog.regclass,'truss.source_epoch_registry'::pg_catalog.regclass)",prepare=False,binary=False)
            if executor_cursor.description is None or len(executor_cursor.description)!=1 or executor_cursor.description[0].type_code!=25 or executor_cursor.fetchmany(2)!=[('2',)]:
                raise ValueError('Original native authority guards unavailable at release')
            return 'original-guards-retained'
        checked=executor_host._run_operation(executor_transaction,retained)
        if type(checked) is not Ok:raise ValueError('Original executor release guard refused')
        _exclude_native_predefined_role_reachability(cursor)
        _exclude_native_private_fact_privileges(cursor,providers)
        _verify_native_profile_caller(cursor,selected.profile)
        return result.value
    from truss.psycopg_host import _HostPairReservation
    with _HostPairReservation(caller_host,executor_host):
        return caller_host._run_operation(caller_transaction,capture)
