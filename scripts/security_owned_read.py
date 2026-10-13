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
    paths=[tool,ROOT/'scripts/security-named-source-fixture.ts',ROOT/'scripts/security-named-subject.sql',ROOT/'docs/helix/04-build/evidence/security-named-source-profile/document.json',ROOT/'docs/helix/04-build/evidence/security-named-source-profile/mapping-request.json']+[ROOT/'docs/helix/04-build/evidence'/base/(name+'.json') for base in ('security-identity-requirements','security-named-source-profile') for name in ('policy','resolution','transport')]+[p for p in (owner/'src').rglob('*') if p.is_file() and p.suffix in ('.ts','.json')]+[owner/'tests/security/fixture.ts']
    return _OwnedEvaluatorSourcePins(tool,tuple((p,hashlib.sha256(p.read_bytes()).digest()) for p in paths))


def _read_owned_evaluator_receipt(text):
    """Closed publication shape only; UMF owns domains and field semantics."""
    def refuse(*args):raise ValueError('Original fixture publication refused')
    def pairs(entries):
        result={}
        for key,value in entries:
            if key in result:refuse()
            result[key]=value
        return result
    try:receipt=json.loads(text,object_pairs_hook=pairs,parse_constant=refuse)
    except (ValueError,RecursionError):refuse()
    if type(receipt) is not dict or set(receipt)!={'decision','identities'}:refuse()
    decision=receipt['decision']
    if (type(decision) is not dict or set(decision)!={'decision','output'}
            or decision['decision'] not in ('permit','deny')
            or type(decision['output']) is not list or len(decision['output'])>256):refuse()
    if decision['decision']=='deny' and decision['output']:refuse()
    for cell in decision['output']:
        if type(cell) is not dict:refuse()
        disposition=cell.get('disposition')
        keys={'field','disposition'}
        if disposition in ('original','transformed'):keys.add('value')
        if disposition=='transformed':keys.add('outputType')
        if disposition not in ('original','transformed','withheld','absent') or set(cell)!=keys:refuse()
        for key in ('field','outputType') if disposition=='transformed' else ('field',):
            ref=cell[key]
            if (type(ref) is not dict or set(ref)!={'documentId','moduleId','elementId'}
                    or any(type(value) is not str or not 1<=len(value)<=4096 for value in ref.values())):refuse()
    return decision


def _run_owned_identity_read(host, transaction, epoch, requirements, sources, delegated=False, caller_database=None, evaluator_sources=None, *, resource_list=False, source_profile='legacy', native_subject=None, original_inspector=None):
    if type(source_profile) is not str or source_profile not in ('legacy','named'):raise ValueError('Exact original fixture source profile required')
    if type(sources) is not _OriginalFactSources:raise ValueError('Original fixture sources required')
    sources=_OriginalFactSources(sources.policy,sources.resolution)
    base=ROOT/'docs/helix/04-build/evidence'/('security-named-source-profile' if source_profile=='named' else 'security-identity-requirements')
    if sources.policy!=(base/'policy.json').read_bytes() or sources.resolution!=(base/'resolution.json').read_bytes():
        raise ValueError('Exact selected original fixture source bytes required')
    digest=hashlib.sha256(requirements).hexdigest()
    _inspect_original_fact_sources(requirements,digest,sources)
    selected,providers=_epoch_dependency_recipe(epoch,digest,sources)
    profile=json.loads(selected.profile)
    if profile['kind'] not in ('truss-flat-fact-provider-fixture/0.2','truss-flat-fact-provider-fixture/0.3','truss-flat-fact-provider-fixture/0.4','truss-flat-fact-provider-fixture/0.5'):
        raise ValueError('Original source-bound fixture profile required')
    if profile['kind'].endswith(('/0.4','/0.5'))!=delegated:
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
    observe_subject=None
    subject_source=None
    if native_subject is not None:
        from dataclasses import replace
        from truss._psycopg_subject_observation import _SubjectSelection,_prepare_subject_operation
        from truss._umf_key_tuples import encode_literal_key_tuple
        if (source_profile!='named' or profile['kind']!='truss-flat-fact-provider-fixture/0.3' or delegated or type(native_subject) is not _SubjectSelection
                or native_subject.original_document!=(base/'document.json').read_bytes()
                or native_subject.original_request!=(base/'mapping-request.json').read_bytes()
                or (native_subject.module,native_subject.record,native_subject.key,native_subject.columns,native_subject.schema,native_subject.routine,native_subject.actor_carrier)!=('m','Staff','pk',('staff_id',),'truss','named_subject_current','text')):
            raise ValueError('Exact shared named fixture subject source required')
        native_subject=replace(native_subject)
        sql_path=ROOT/'scripts/security-named-subject.sql'
        sql_bytes=sql_path.read_bytes()
        if hashlib.sha256(sql_bytes).digest()!=pins[sql_path]:raise ValueError('Prepared named subject SQL changed')
        subject_source=sql_bytes.decode('utf8').split('AS $$',1)[1].split('$$;',1)[0]
        def produce_subject(observation):
            texts=tuple(json.dumps({'string':value}) for value in observation.values)
            return encode_literal_key_tuple(native_subject.original_document,observation.identity,texts,bun_executable='/opt/homebrew/bin/bun')
        observe_subject=_prepare_subject_operation(host,native_subject,original_inspector,produce_subject,(('read_committed','read_write'),))
    def execute(cursor):
        caller=profile.get('caller')
        if caller_database is not None:
            cursor.execute('SELECT oid::pg_catalog.text FROM pg_catalog.pg_database WHERE datname OPERATOR(pg_catalog.=) pg_catalog.current_database()',prepare=False,binary=False)
            if cursor.description is None or len(cursor.description)!=1 or cursor.description[0].type_code!=25 or cursor.fetchmany(2)!=[caller_database]:
                raise ValueError('Original caller/executor database correspondence required')
        _verify_native_profile_caller(cursor,json.dumps({'caller':profile['executor']}).encode() if delegated else selected.profile)
        if observe_subject is not None:
            _verify_named_subject_helper(cursor,providers,expected_source=subject_source)
            # This cursor already holds the selected source and complete declared fact cuts.
            observed_key=observe_subject(cursor,host._observe(cursor))
            selected_key=encode_literal_key_tuple(native_subject.original_document,('m','Staff','pk'),
                tuple(json.dumps(value) for value in caller['subjectKey']),bun_executable='/opt/homebrew/bin/bun')
            if observed_key.tuple_bytes!=selected_key.tuple_bytes:
                raise ValueError('Original native subject/profile key correspondence required')
            _verify_native_profile_caller(cursor,selected.profile)
        cells=_capture_dependency_relation_cells(cursor,groups)
        captured=[asdict(c) for c in cells]
        if resource_list and caller is None:raise ValueError('Original bound subject required for resource listing')
        payload=json.dumps({'cells':captured,'subjectKey':caller['subjectKey'],'resultMode':'resources'} if resource_list else (captured if caller is None else {'cells':captured,'subjectKey':caller['subjectKey']}))
        if len(payload.encode('utf8'))>1048576:raise ValueError('Bounded semantic fixture input required')
        try:
            result=subprocess.run(['/opt/homebrew/bin/bun',str(tool)]+(['--named-source'] if source_profile=='named' else []),cwd=ROOT,input=payload,capture_output=True,text=True,timeout=4)
        except subprocess.TimeoutExpired:
            raise TimeoutError('Original evaluator deadline expired') from None
        if result.returncode or len(result.stdout.encode('utf8'))>65536:raise ValueError('Original UMF fixture evaluation refused')
        if any(hashlib.sha256(p.read_bytes()).digest()!=h for p,h in pins.items()):raise ValueError('Original evaluator sources changed')
        if observe_subject is not None:_verify_native_profile_caller(cursor,selected.profile)
        decision=_read_owned_resource_receipt(result.stdout) if resource_list else _read_owned_evaluator_receipt(result.stdout)
        # No raw cells, private fact identities or evaluator diagnostics leave
        # this owned operation. Dispositions remain original UMF output.
        return decision
    return _run_dependency_fact_operation(host,transaction,selected,requirements,digest,providers,execute)


def _verify_named_subject_helper(cursor,providers,*,expected_source=None):
    """Exact selected native definition snapshot; no DDL/handler/role lifetime proof."""
    staff=[p for p in providers if p.kind=='field' and p.reference==('domain','m','staffId')]
    if (len(staff)!=1 or (staff[0].relation.schema,staff[0].relation.name)!=('truss','sec_staff')
            or staff[0].column is None or (staff[0].column.name,staff[0].column.type_oid)!=('staff_id',25)):
        raise ValueError('Declared named subject read home required')
    source=expected_source if expected_source is not None else (ROOT/'scripts/security-named-subject.sql').read_text().split('AS $$',1)[1].split('$$;',1)[0]
    if type(source) is not str or not 1<=len(source.encode('utf8'))<=65536:
        raise ValueError('Bounded selected named subject source required')
    cursor.execute("SELECT p.proowner::pg_catalog.text,l.lanname::pg_catalog.text,p.prokind::pg_catalog.text,"
        "p.pronargs::pg_catalog.text,p.proargtypes::pg_catalog.text,p.prorettype::pg_catalog.text,"
        "p.proretset::pg_catalog.text,p.proisstrict::pg_catalog.text,p.prosecdef::pg_catalog.text,"
        "p.provolatile::pg_catalog.text,p.proparallel::pg_catalog.text,p.proleakproof::pg_catalog.text,"
        "p.prosupport::pg_catalog.oid::pg_catalog.text,pg_catalog.to_jsonb(p.proconfig)::pg_catalog.text,p.prosrc,"
        "pg_catalog.to_jsonb(p.proargnames)::pg_catalog.text,pg_catalog.to_jsonb(p.proargmodes)::pg_catalog.text,"
        "pg_catalog.to_jsonb(p.proallargtypes)::pg_catalog.text,(p.prosqlbody IS NULL)::pg_catalog.text "
        "FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace "
        "JOIN pg_catalog.pg_language l ON l.oid OPERATOR(pg_catalog.=) p.prolang "
        "WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND p.proname OPERATOR(pg_catalog.=) 'named_subject_current' AND p.proargtypes OPERATOR(pg_catalog.=) '25'::pg_catalog.oidvector",
        prepare=False,binary=False)
    if cursor.description is None or len(cursor.description)!=19 or any(d.type_code!=25 for d in cursor.description):
        raise ValueError('Exact named subject helper TEXT descriptors required')
    expected=(str(staff[0].relation.owner_oid),'sql','f','1','25','25','true','false','false','v','u','false','0',
        '["search_path=pg_catalog"]',source,'["actor", "staff_id"]','["i", "t"]','["25", "25"]','true')
    actual=cursor.fetchmany(2)
    if actual!=[expected]:raise ValueError('Exact installed named subject helper snapshot required')


def _read_owned_resource_receipt(text):
    # Structural carrier checks only; original UMF owns key and disclosure semantics.
    from truss._owner_evidence_json import decode_owner_evidence_json
    receipt=decode_owner_evidence_json(text.encode('utf8'))
    if (type(receipt) is not dict or set(receipt)!={'kind','rows'}
            or receipt['kind']!='owned-resource-list-fixture/0.1'
            or type(receipt['rows']) is not list or len(receipt['rows'])>100):
        raise ValueError('Closed bounded original resource receipt required')
    for row in receipt['rows']:
        if (type(row) is not dict or set(row)!={'key','output'}
                or type(row['key']) is not list or not 1<=len(row['key'])<=32):
            raise ValueError('Original resource key/output carrier required')
        _read_owned_evaluator_receipt(json.dumps({'decision':{'decision':'permit','output':row['output']},'identities':[]}))
    return receipt


def run_owned_resource_read(host, transaction, epoch, requirements, sources, *, source_profile='legacy'):
    """Fixed-source multi-resource fixture; no generic compiler/native admission."""
    return _run_owned_identity_read(host,transaction,epoch,requirements,sources,resource_list=True,source_profile=source_profile)


def run_named_subject_resource_read(host, transaction, epoch, requirements, sources, selection, original_inspector):
    """Fresh native subject + original encoding/evaluation fixture, not authority."""
    from truss._psycopg_subject_observation import _SubjectSelection
    if type(selection) is not _SubjectSelection:
        raise ValueError('Required exact native subject selection')
    return _run_owned_identity_read(host,transaction,epoch,requirements,sources,resource_list=True,
        source_profile='named',native_subject=selection,original_inspector=original_inspector)


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
    if not json.loads(selected.profile)['kind'].endswith(('/0.4','/0.5')):raise ValueError('Original delegated profile required')
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
