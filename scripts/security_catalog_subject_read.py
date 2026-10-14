"""Native ordinary subject -> private accepted-source executor fixture.

Issuer/helper authenticity, cluster uniqueness and exclusive host use are
premises. No protected endpoint, role/DDL closure or authority is issued.
"""
from pathlib import Path
from dataclasses import replace
import hashlib,json
from truss._psycopg_subject_observation import _SubjectSelection,_prepare_subject_operation
from truss._security_mapping import PreparedSecurityMapping,_pin_cursor
from truss._umf_key_tuples import encode_literal_key_tuple
from truss.execution import Ok
from truss.psycopg_host import PsycopgHost,_prepare_synchronous_publisher
from security_catalog_read import run_owned_catalog_resource_read,BASE
ROOT=Path(__file__).resolve().parent.parent


def _verify_helpers(cursor,source,*,expected_callers=None):
    from truss._security_catalog_subject_helpers import verify_catalog_subject_helpers_with_cursor
    return verify_catalog_subject_helpers_with_cursor(cursor,source,expected_callers=expected_callers)



def derive_catalog_source_epoch_profile(mapping,fact_relations,barrier,*,subject_source=None):
    from truss._security_catalog_source_binding import derive_catalog_source_epoch_profile as bind,_snapshot_source_binding
    mapping,fact_relations,barrier=_snapshot_source_binding(mapping,fact_relations,barrier)
    if subject_source is None:subject_source=(ROOT/'scripts/security-catalog-subject.sql').read_bytes()
    return bind(mapping,fact_relations,barrier,subject_source=subject_source)


def run_owned_native_catalog_resource_read(caller_host,caller_transaction,executor_host,executor_transaction,mapping,selection,original_inspector,*,fact_relations=None,publisher=None,source_cut=None,registered_subjects=None,role_catalog_cut=False):
    if (type(mapping) is not PreparedSecurityMapping or type(selection) is not _SubjectSelection
            or type(caller_host) is not PsycopgHost or type(executor_host) is not PsycopgHost):raise ValueError('Exact native caller and accepted mapping required')
    if publisher is not None and (not callable(publisher) or fact_relations is None):
        raise ValueError('Original guarded publication context required')
    if publisher is not None:publisher=_prepare_synchronous_publisher(publisher)
    mapping=replace(mapping);selection=replace(selection)
    if type(role_catalog_cut) is not bool or (role_catalog_cut and registered_subjects is None):raise ValueError('Exact registered role cut context required')
    expected_callers=None
    if registered_subjects is not None:
        from truss._security_catalog_subject_installation import snapshot_catalog_subjects
        registered_subjects=snapshot_catalog_subjects(registered_subjects)
        if source_cut is None or fact_relations is None:raise ValueError('Mandatory registered Subject source/fact cuts required')
        expected_callers=tuple(oid for oid,key in registered_subjects.bindings)
    if (selection.original_request!=mapping.original_request or selection.original_document!=(BASE/'document.json').read_bytes()
            or (selection.module,selection.record,selection.key,selection.schema,selection.routine,selection.columns,selection.actor_carrier)!=('m','Staff','pk','truss','catalog_subject_current',('staff_id',),'text')):
        raise ValueError('Exact shared named catalog Subject selection required')
    if source_cut is not None:
        from truss._psycopg_epoch_cut import _EpochComparison,_DDLBarrierComparison
        if (fact_relations is None or type(source_cut) is not tuple or len(source_cut)!=2
                or type(source_cut[0]) is not _EpochComparison or type(source_cut[1]) is not _DDLBarrierComparison):
            raise ValueError('Exact guarded source epoch and DDL barrier required')
        source_cut=(replace(source_cut[0]),replace(source_cut[1]))
    qualify=None;executor_relations=None;subject_cursor=[None]
    if fact_relations is not None:
        from truss._psycopg_fact_cut import _FactRelationComparison,_FactColumnComparison,_prepare_fenced_fact_cut
        if (type(fact_relations) is not tuple or len(fact_relations)!=2
                or any(type(r) is not _FactRelationComparison for r in fact_relations)
                or {(r.schema,r.name) for r in fact_relations}!={('truss','object'),('truss','catalog_subject_map')}):
            raise ValueError('Exact caller object and Subject map fact cuts required')
        if any(type(r.columns) is not tuple or len(r.columns)>1600
                or any(type(c) is not _FactColumnComparison for c in r.columns) for r in fact_relations):
            raise ValueError('Exact bounded caller fact column comparisons required')
        fact_relations=tuple(replace(r,columns=tuple(replace(c) for c in r.columns)) for r in fact_relations)
        qualify=_prepare_fenced_fact_cut(fact_relations,lambda c:None,existing_locks=True)
        executor_relations=tuple(r for r in fact_relations if r.name=='object')
    source_path=ROOT/'scripts/security-catalog-subject.sql';source_bytes=source_path.read_bytes();source=source_bytes.decode();source_pin=hashlib.sha256(source_bytes).digest()
    if source_cut is not None:
        expected_profile=derive_catalog_source_epoch_profile(mapping,fact_relations,source_cut[1],subject_source=source_bytes)
        if (type(source_cut[0].profile) is not bytes or source_cut[0].profile!=expected_profile
                or type(source_cut[0].evidence) is not bytes or source_cut[0].evidence!=mapping.accepted_catalog_assessment):
            raise ValueError('Original catalog source profile and evidence binding required')
    def produce(observed):
        if qualify is not None:qualify(subject_cursor[0])
        key=encode_literal_key_tuple(selection.original_document,observed.identity,tuple(json.dumps({'string':v}) for v in observed.values),bun_executable='/opt/homebrew/bin/bun')
        return observed.values[0],key.tuple_bytes
    observe=_prepare_subject_operation(caller_host,selection,original_inspector,produce,(('read_committed','read_write'),))
    def qualify_source():
        from truss._psycopg_epoch_cut import _run_ddl_fenced_epoch_operation
        def audience(c):
            _pin_cursor(c)
            if role_catalog_cut:
                from truss._security_catalog_subject_installation import acquire_registered_role_catalog_cut_with_cursor
                acquire_registered_role_catalog_cut_with_cursor(c)
            c.execute('SELECT installation_id::pg_catalog.text FROM truss.catalog_runtime_installation WHERE singleton',prepare=False,binary=False)
            if c.description is None or len(c.description)!=1 or c.description[0].type_code!=25:
                raise ValueError('Exact source epoch installation TEXT descriptor required')
            if c.fetchmany(2)!=[(source_cut[0].installation,)]:
                raise ValueError('Original source epoch installation correspondence required')
            from truss._security_catalog_source_installation import verify_catalog_source_archive_with_cursor
            verify_catalog_source_archive_with_cursor(c,mapping,source_cut[0].installation)
            if registered_subjects is not None:
                from truss._psycopg_fact_cut import _prepare_fenced_fact_cut
                from truss._security_catalog_subject_installation import verify_registered_catalog_subjects_with_cursor
                def verify_registered(current):
                    verify_registered_catalog_subjects_with_cursor(current,registered_subjects,source_bytes)
                _prepare_fenced_fact_cut(fact_relations,verify_registered)(c)
        result=_run_ddl_fenced_epoch_operation(executor_host,executor_transaction,*source_cut,audience)
        if not isinstance(result,Ok):raise ValueError('Original executor source epoch and DDL barrier refused')
    def execute(cursor,observed):
        if source_cut is not None:qualify_source()
        subject_cursor[0]=cursor
        _pin_cursor(cursor);_verify_helpers(cursor,source,expected_callers=expected_callers)
        subject,key=observe(cursor,observed)
        cursor.execute('SELECT * FROM truss.catalog_subject_context(SESSION_USER::pg_catalog.text)',prepare=False,binary=False)
        if cursor.description is None or tuple(d.name for d in cursor.description)!=('installation_id','database_oid','role_oid') or any(d.type_code!=25 for d in cursor.description):raise ValueError('Exact native Subject context descriptors required')
        context=cursor.fetchmany(2)
        if len(context)!=1 or any(type(v) is not str for v in context[0]):raise ValueError('Unique native Subject installation required')
        if registered_subjects is not None and (context[0][0]!=registered_subjects.installation_id
                or (int(context[0][2]),subject) not in registered_subjects.bindings):
            raise ValueError('Original registered native caller Subject required')
        def environment(c,o):
            _pin_cursor(c)
            c.execute("SELECT i.installation_id::pg_catalog.text,(SELECT d.oid::pg_catalog.text FROM pg_catalog.pg_database d WHERE d.datname OPERATOR(pg_catalog.=) pg_catalog.current_database()) FROM truss.catalog_runtime_installation i WHERE i.singleton",prepare=False,binary=False)
            if c.description is None or len(c.description)!=2 or any(d.type_code!=25 for d in c.description):raise ValueError('Exact executor installation descriptors required')
            if c.fetchmany(2)!=[context[0][:2]]:raise ValueError('Original caller/executor installation correspondence required')
        qualified=executor_host._run_operation(executor_transaction,environment)
        if not isinstance(qualified,Ok):raise ValueError('Original caller/executor installation correspondence required')
        if executor_relations is None:result=run_owned_catalog_resource_read(executor_host,executor_transaction,mapping,subject)
        else:result=run_owned_catalog_resource_read(executor_host,executor_transaction,mapping,subject,fact_relations=executor_relations)
        if not isinstance(result,Ok):raise ValueError('Original native Subject catalog evaluation refused')
        _pin_cursor(cursor);_verify_helpers(cursor,source,expected_callers=expected_callers)
        if observe(cursor,caller_host._observe(cursor))!=(subject,key):raise ValueError('Original native Subject changed during delegated evaluation')
        if source_cut is not None:qualify_source()
        if hashlib.sha256(source_path.read_bytes()).digest()!=source_pin:raise ValueError('Original catalog Subject source changed')
        if publisher is not None:return json.dumps(result.value,separators=(',',':'),ensure_ascii=False).encode('utf8')
        return result.value
    if publisher is not None:return caller_host._run_published_operation(caller_transaction,execute,publisher)
    return caller_host._run_operation(caller_transaction,execute)


def run_guarded_native_catalog_resource_read(caller_host,caller_transaction,executor_host,executor_transaction,mapping,selection,original_inspector,fact_relations):
    """Explicit guarded fixture; omitted guard never downgrades to legacy mode."""
    if fact_relations is None:raise ValueError('Mandatory native caller fact cuts required')
    return run_owned_native_catalog_resource_read(caller_host,caller_transaction,executor_host,executor_transaction,mapping,selection,original_inspector,fact_relations=fact_relations)


def publish_guarded_native_catalog_resource_read(caller_host,caller_transaction,executor_host,executor_transaction,mapping,selection,original_inspector,fact_relations,publisher):
    """Private immutable historical publication; trusted bounded sink premise.

    Original issuer/source and continuous selected cut lifetime remain premises.
    Not a public protected query endpoint or reusable authority capability.
    """
    if fact_relations is None or not callable(publisher):
        raise ValueError('Mandatory guarded publication context required')
    return run_owned_native_catalog_resource_read(caller_host,caller_transaction,executor_host,executor_transaction,mapping,selection,original_inspector,fact_relations=fact_relations,publisher=publisher)


def publish_ddl_epoch_guarded_native_catalog_resource_read(caller_host,caller_transaction,executor_host,executor_transaction,mapping,selection,original_inspector,fact_relations,source_cut,publisher):
    """Private selected DDL/epoch composition, not complete source admission.

    Independently installed issuer/barrier lifetime and trusted private executor
    remain premises. Selected epoch cuts survive through receiver completion in
    the executor's outer transaction. Shared roles/config/admin bypass are open.
    """
    if fact_relations is None or source_cut is None or not callable(publisher):
        raise ValueError('Mandatory source-guarded publication context required')
    return run_owned_native_catalog_resource_read(caller_host,caller_transaction,executor_host,executor_transaction,mapping,selection,original_inspector,fact_relations=fact_relations,publisher=publisher,source_cut=source_cut)


def publish_registered_ddl_epoch_guarded_native_catalog_resource_read(caller_host,caller_transaction,executor_host,executor_transaction,mapping,selection,original_inspector,fact_relations,source_cut,registered_subjects,publisher):
    from truss._security_catalog_subject_installation import PendingCatalogSubjects
    if type(registered_subjects) is not PendingCatalogSubjects or fact_relations is None or source_cut is None or not callable(publisher):
        raise ValueError('Mandatory original registered Subject publication required')
    return run_owned_native_catalog_resource_read(caller_host,caller_transaction,executor_host,executor_transaction,mapping,selection,original_inspector,fact_relations=fact_relations,publisher=publisher,source_cut=source_cut,registered_subjects=registered_subjects)


def publish_role_fenced_registered_catalog_resource_read(caller_host,caller_transaction,executor_host,executor_transaction,mapping,selection,original_inspector,fact_relations,source_cut,registered_subjects,publisher):
    """Explicit privileged role catalog cut; not an admitted public backend profile."""
    from truss._security_catalog_subject_installation import PendingCatalogSubjects
    if type(registered_subjects) is not PendingCatalogSubjects or fact_relations is None or source_cut is None or not callable(publisher):
        raise ValueError('Mandatory role-fenced registered publication required')
    return run_owned_native_catalog_resource_read(caller_host,caller_transaction,executor_host,executor_transaction,mapping,selection,original_inspector,fact_relations=fact_relations,publisher=publisher,source_cut=source_cut,registered_subjects=registered_subjects,role_catalog_cut=True)
