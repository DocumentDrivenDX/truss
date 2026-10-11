"""Executable rollback-only fresh layout construction, never installed readiness.

The private installer supplies an exclusively owned idle administrative session.
Selected namespace descriptors and direct ACLs are observed, not a complete dependency or
effective-authority inventory. Production installation/publication is unfinished.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
from ._installation_statement_release import STATEMENTS_SHA256,SOURCE_MANIFEST_SHA256


@dataclass(frozen=True,slots=True)
class ProvisionalCatalogConstruction:
    original_statements: bytes
    original_target: bytes
    namespace_observation: bytes
    statement_count: str
    rollback_confirmed: bool
    scope: str = 'rollback_only_fresh_layout_construction'
    installation_ready: bool = False


class CatalogConstructionFailure(RuntimeError):
    def __init__(self,primary,cleanup,original_statements,original_target,rollback_confirmed,connection,attempt):
        self.original_connection=connection;self.original_attempt=attempt
        self.primary_failure=primary;self.cleanup_failure=cleanup
        self.original_statements=original_statements;self.original_target=original_target
        self.rollback_confirmed=rollback_confirmed
        super().__init__('Provisional catalog construction failed')


def _statements():
    original=files('truss').joinpath('_installation/statements.json').read_bytes()
    if not 1<=len(original)<=4194304 or sha256(original).hexdigest()!=STATEMENTS_SHA256:
        raise ValueError('Original owner statement inventory required')
    profile=json.loads(original)
    source=files('truss').joinpath('_installation/manifest.json').read_bytes()
    if sha256(source).hexdigest()!=SOURCE_MANIFEST_SHA256:
        raise ValueError('Original development source definition required')
    definition=json.loads(source)
    if (definition['qualified'] is not False or definition['executable'] is not False
        or profile['modelSha256']!=next(r['sha256'] for r in definition['resources'] if r['role']=='model')
        or profile['ownerExportSha256']!=next(r['sha256'] for r in definition['resources'] if r['role']=='owner_export')):
        raise ValueError('Original model and owner export correspondence required')
    if (profile['interfaceVersion']!='truss-provisional-installation-statements/0.1.0'
        or profile['completeInstalledProfile'] is not False or profile['installationReady'] is not False
        or profile['scope']!='original_owner_statement_units_rollback_only_construction'):
        raise ValueError('Provisional construction profile required')
    statements=profile['statements']
    if type(statements) is not list or not 1<=len(statements)<=512:
        raise ValueError('Complete bounded statement membership required')
    total=0
    for index,statement in enumerate(statements):
        raw=statement['sql'].encode('utf8')
        if (statement['position']!=str(index) or type(statement['byteLength']) is not int
            or not 1<=len(raw)<=1048576 or statement['byteLength']!=len(raw)
            or sha256(raw).hexdigest()!=statement['sha256']):
            raise ValueError('Original ordered owner statement bytes required')
        total+=len(raw)
    if total>4194304:raise ValueError('Construction statement aggregate bound exceeded')
    return original,statements


def _native_text(connection,sql):
    rows=connection.run(sql)
    if len(rows)!=1 or len(rows[0])!=1 or type(rows[0][0]) is not str:
        raise ValueError('Original single native text observation required')
    value=rows[0][0].encode('utf8')
    if len(value)>16777216:raise ValueError('Construction observation retention exceeded')
    return value


_TARGET="""SELECT pg_catalog.jsonb_build_object('database',pg_catalog.current_database(),
 'databaseOid',(SELECT oid::pg_catalog.text FROM pg_catalog.pg_database WHERE datname OPERATOR(pg_catalog.=) pg_catalog.current_database()),
 'sessionUser',session_user::pg_catalog.text,'actingUser',current_user::pg_catalog.text,
 'backendPid',pg_catalog.pg_backend_pid()::pg_catalog.text,'version',pg_catalog.current_setting('server_version_num'))::pg_catalog.text"""

_NAMESPACE="SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname OPERATOR(pg_catalog.=) 'truss'::pg_catalog.name)::pg_catalog.text"

_OBSERVATION="""SELECT pg_catalog.jsonb_build_object(
 'namespace',(SELECT pg_catalog.to_jsonb(n) FROM pg_catalog.pg_namespace n WHERE nspname='truss'),
 'relations',(SELECT COALESCE(jsonb_agg(to_jsonb(c) ORDER BY c.oid),'[]'::jsonb) FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
 'columns',(SELECT COALESCE(jsonb_agg(to_jsonb(a) ORDER BY a.attrelid,a.attnum),'[]'::jsonb) FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid=a.attrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
 'defaults',(SELECT COALESCE(jsonb_agg(jsonb_build_object('native',to_jsonb(a),'definition',pg_catalog.pg_get_expr(a.adbin,a.adrelid,false)) ORDER BY a.oid),'[]'::jsonb) FROM pg_catalog.pg_attrdef a JOIN pg_catalog.pg_class c ON c.oid=a.adrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
 'sequences',(SELECT COALESCE(jsonb_agg(to_jsonb(s) ORDER BY s.seqrelid),'[]'::jsonb) FROM pg_catalog.pg_sequence s JOIN pg_catalog.pg_class c ON c.oid=s.seqrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
 'types',(SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY t.oid),'[]'::jsonb) FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid=t.typnamespace WHERE n.nspname='truss'),
 'rules',(SELECT COALESCE(jsonb_agg(jsonb_build_object('native',to_jsonb(r),'definition',pg_catalog.pg_get_ruledef(r.oid,false)) ORDER BY r.oid),'[]'::jsonb) FROM pg_catalog.pg_rewrite r JOIN pg_catalog.pg_class c ON c.oid=r.ev_class JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
 'constraints',(SELECT COALESCE(jsonb_agg(jsonb_build_object('native',to_jsonb(c),'definition',pg_catalog.pg_get_constraintdef(c.oid)) ORDER BY c.oid),'[]'::jsonb) FROM pg_catalog.pg_constraint c JOIN pg_catalog.pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='truss'),
 'indexes',(SELECT COALESCE(jsonb_agg(jsonb_build_object('native',to_jsonb(i),'definition',pg_catalog.pg_get_indexdef(i.indexrelid)) ORDER BY i.indexrelid),'[]'::jsonb) FROM pg_catalog.pg_index i JOIN pg_catalog.pg_class c ON c.oid=i.indrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
 'routines',(SELECT COALESCE(jsonb_agg(jsonb_build_object('native',to_jsonb(p),'definition',pg_catalog.pg_get_functiondef(p.oid)) ORDER BY p.oid),'[]'::jsonb) FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss'),
 'triggers',(SELECT COALESCE(jsonb_agg(jsonb_build_object('native',to_jsonb(t),'definition',pg_catalog.pg_get_triggerdef(t.oid)) ORDER BY t.oid),'[]'::jsonb) FROM pg_catalog.pg_trigger t JOIN pg_catalog.pg_class c ON c.oid=t.tgrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
 'policies',(SELECT COALESCE(jsonb_agg(to_jsonb(p) ORDER BY p.oid),'[]'::jsonb) FROM pg_catalog.pg_policy p JOIN pg_catalog.pg_class c ON c.oid=p.polrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'))::text"""


def construct_provisional_catalog_layout(connection):
    """Run actual exact-source construction and always roll back its own transaction.

    No caller runtime transaction is adopted. No COMMIT, marker publication,
    namespace repair or retry path exists. Bounds cover retained data only.
    """
    original,statements=_statements()
    if getattr(connection,'_transaction_status',None)!=b'I':
        raise ValueError('Original idle installer-owned administrative connection required')
    target=_native_text(connection,_TARGET)
    begun=False;primary=None;cleanup=None;observed=b'';restored=False;prior_namespace=None
    attempt={'phase':'target_observed','submitted_statements':[], 'rollback_submitted':False,'rollback_reply_observed':False}
    try:
        # Treat an uncertain BEGIN as cleanup-required as well.
        begun=True;attempt['phase']='begin_submitted';connection.run('BEGIN')
        connection.run('SET LOCAL search_path = pg_catalog, pg_temp')
        attempt['phase']='construction'
        connection.run('SELECT pg_catalog.pg_advisory_xact_lock(1953658227,1)')
        prior_namespace=_native_text(connection,_NAMESPACE)
        if prior_namespace not in (b'true',b'false'):raise ValueError('Exact namespace absence observation required')
        if prior_namespace!=b'false':raise ValueError('Fresh namespace required')
        for statement in statements:
            attempt['submitted_statements'].append(statement['position'])
            connection.run(statement['sql'])
        for sql in ('REVOKE ALL ON SCHEMA truss FROM PUBLIC',
                    'REVOKE ALL ON ALL TABLES IN SCHEMA truss FROM PUBLIC',
                    'REVOKE ALL ON ALL SEQUENCES IN SCHEMA truss FROM PUBLIC',
                    'REVOKE ALL ON ALL FUNCTIONS IN SCHEMA truss FROM PUBLIC'):
            connection.run(sql)
        observed=_native_text(connection,_OBSERVATION)
    except BaseException as error:
        primary=error
    finally:
        if begun:
            try:
                attempt['phase']='rollback_submitted';attempt['rollback_submitted']=True
                connection.run('ROLLBACK')
                attempt['rollback_reply_observed']=True
                if getattr(connection,'_transaction_status',None)!=b'I':raise ValueError('Original idle rollback completion required')
                # A preexisting namespace refusal must preserve that namespace.
                restored=prior_namespace is not None and _native_text(connection,_NAMESPACE)==prior_namespace
                if not restored:raise ValueError('Original namespace prestate not restored')
            except BaseException as error:cleanup=error
    if primary is not None or cleanup is not None:
        raise CatalogConstructionFailure(primary,cleanup,original,target,restored,connection,attempt) from primary
    return ProvisionalCatalogConstruction(original,target,observed,str(len(statements)),restored)
