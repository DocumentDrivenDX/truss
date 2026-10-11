"""Executable rollback-only fresh layout construction, never installed readiness.

The private installer supplies an exclusively owned idle administrative session.
Selected namespace descriptors and direct ACLs are observed, not a complete dependency or
effective-authority inventory. Production installation/publication is unfinished.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
from types import MappingProxyType
from ._construction_recovery import ConstructionOriginal,ProvisionalConstructionRecovery
from ._installation_definition_release import DEFINITIONS_SHA256,DEFINITION_QUERY_SHA256
from ._installation_statement_release import STATEMENTS_SHA256,SOURCE_MANIFEST_SHA256
from ._installation_metadata import prepare_metadata,execute_metadata,validate_metadata_preflight


@dataclass(frozen=True,slots=True)
class ProvisionalCatalogConstruction:
    original_statements: bytes
    original_target: bytes
    namespace_observation: bytes
    statement_count: str
    rollback_confirmed: bool
    scope: str = 'rollback_only_fresh_layout_construction'
    installation_ready: bool = False
    original_definition_baseline: bytes = b''
    definition_observation: bytes = b''
    recovery: object = None
    recovery_reference: object = None
    metadata_observation: bytes = b''


class CatalogConstructionFailure(RuntimeError):
    def __init__(self,primary,cleanup,original_statements,original_target,rollback_confirmed,connection,attempt):
        self.original_connection=connection
        self.original_attempt=MappingProxyType({**attempt,'submitted_statements':tuple(attempt['submitted_statements'])})
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
    if (profile['nativeMajor']!='16' or profile['interfaceVersion']!='truss-provisional-installation-statements/0.1.0'
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


def _definition_baseline(original_statements):
    original=files('truss').joinpath('_installation/definitions.json').read_bytes()
    query=files('truss').joinpath('_installation/definitions.sql').read_bytes()
    if not 1<=len(original)<=4194304 or sha256(original).hexdigest()!=DEFINITIONS_SHA256 or sha256(query).hexdigest()!=DEFINITION_QUERY_SHA256:
        raise ValueError('Independent original definition baseline required')
    profile=json.loads(original);statements=json.loads(original_statements)
    if (profile['interface']!='truss-selected-native-definition-baseline/0.1.0' or profile['installationReady'] is not False
        or profile['independentRollbackConfirmed'] is not True or profile['nativeVersion']!='170011'
        or profile['statementReleaseSha256']!=sha256(original_statements).hexdigest()
        or profile['modelSha256']!=statements['modelSha256'] or profile['ownerExportSha256']!=statements['ownerExportSha256']
        or profile['querySha256']!=sha256(query).hexdigest()):
        raise ValueError('Independent baseline release correspondence required')
    return original,query,profile


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
 'columnDefinitions',(SELECT COALESCE(jsonb_agg(jsonb_build_object('table',c.relname,'column',a.attname,'type',tn.nspname||'.'||t.typname,'modifier',a.atttypmod::text,'dimensions',a.attndims::text,'notNull',a.attnotnull,'generated',a.attgenerated,'identity',a.attidentity,'hasDefault',a.atthasdef,'collation',cn.nspname||'.'||co.collname) ORDER BY c.relname,a.attnum),'[]'::jsonb) FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid=a.attrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_type t ON t.oid=a.atttypid JOIN pg_catalog.pg_namespace tn ON tn.oid=t.typnamespace LEFT JOIN pg_catalog.pg_collation co ON co.oid=a.attcollation LEFT JOIN pg_catalog.pg_namespace cn ON cn.oid=co.collnamespace WHERE n.nspname='truss' AND c.relkind IN ('r','p') AND a.attnum>0 AND NOT a.attisdropped),
 'defaults',(SELECT COALESCE(jsonb_agg(jsonb_build_object('native',to_jsonb(a),'definition',pg_catalog.pg_get_expr(a.adbin,a.adrelid,false)) ORDER BY a.oid),'[]'::jsonb) FROM pg_catalog.pg_attrdef a JOIN pg_catalog.pg_class c ON c.oid=a.adrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
 'sequences',(SELECT COALESCE(jsonb_agg(to_jsonb(s) ORDER BY s.seqrelid),'[]'::jsonb) FROM pg_catalog.pg_sequence s JOIN pg_catalog.pg_class c ON c.oid=s.seqrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
 'sequenceParameters',(SELECT COALESCE(jsonb_agg(jsonb_build_object('name',c.relname,'type',tn.nspname||'.'||t.typname,'increment',s.seqincrement::text,'minimum',s.seqmin::text,'maximum',s.seqmax::text,'start',s.seqstart::text,'cache',s.seqcache::text,'cycle',s.seqcycle) ORDER BY c.relname),'[]'::jsonb) FROM pg_catalog.pg_sequence s JOIN pg_catalog.pg_class c ON c.oid=s.seqrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_type t ON t.oid=s.seqtypid JOIN pg_catalog.pg_namespace tn ON tn.oid=t.typnamespace WHERE n.nspname='truss'),
 'types',(SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY t.oid),'[]'::jsonb) FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid=t.typnamespace WHERE n.nspname='truss'),
 'rules',(SELECT COALESCE(jsonb_agg(jsonb_build_object('native',to_jsonb(r),'definition',pg_catalog.pg_get_ruledef(r.oid,false)) ORDER BY r.oid),'[]'::jsonb) FROM pg_catalog.pg_rewrite r JOIN pg_catalog.pg_class c ON c.oid=r.ev_class JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
 'constraints',(SELECT COALESCE(jsonb_agg(jsonb_build_object('native',to_jsonb(c),'definition',pg_catalog.pg_get_constraintdef(c.oid)) ORDER BY c.oid),'[]'::jsonb) FROM pg_catalog.pg_constraint c JOIN pg_catalog.pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='truss'),
 'indexes',(SELECT COALESCE(jsonb_agg(jsonb_build_object('native',to_jsonb(i),'definition',pg_catalog.pg_get_indexdef(i.indexrelid)) ORDER BY i.indexrelid),'[]'::jsonb) FROM pg_catalog.pg_index i JOIN pg_catalog.pg_class c ON c.oid=i.indrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
 'routines',(SELECT COALESCE(jsonb_agg(jsonb_build_object('native',to_jsonb(p),'language',(SELECT l.lanname FROM pg_catalog.pg_language l WHERE l.oid=p.prolang),'inputTypes',(SELECT COALESCE(jsonb_agg(tn.nspname||'.'||t.typname ORDER BY args.ordinality),'[]'::jsonb) FROM unnest(p.proargtypes::oid[]) WITH ORDINALITY args(typeoid,ordinality) JOIN pg_catalog.pg_type t ON t.oid=args.typeoid JOIN pg_catalog.pg_namespace tn ON tn.oid=t.typnamespace),'definition',pg_catalog.pg_get_functiondef(p.oid)) ORDER BY p.oid),'[]'::jsonb) FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss'),
 'triggers',(SELECT COALESCE(jsonb_agg(jsonb_build_object('native',to_jsonb(t),'definition',pg_catalog.pg_get_triggerdef(t.oid)) ORDER BY t.oid),'[]'::jsonb) FROM pg_catalog.pg_trigger t JOIN pg_catalog.pg_class c ON c.oid=t.tgrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
 'policies',(SELECT COALESCE(jsonb_agg(to_jsonb(p) ORDER BY p.oid),'[]'::jsonb) FROM pg_catalog.pg_policy p JOIN pg_catalog.pg_class c ON c.oid=p.polrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'))::text"""


def prepare_provisional_catalog_construction(connection,recovery,*,metadata=False):
    """Retain original attempt and return its handle before any BEGIN submission."""
    recovery.check_available(connection)
    if type(metadata) is not bool:raise ValueError('Exact metadata branch selection required')
    original,statements=_statements()
    definitions,query,profile=_definition_baseline(original)
    if getattr(connection,'_transaction_status',None)!=b'I':
        raise ValueError('Original idle installer-owned administrative connection required')
    target=_native_text(connection,_TARGET)
    if json.loads(target)['version']!=profile['nativeVersion']:
        raise ValueError('Selected PostgreSQL17.11 source compilation profile required')
    recipe,input_bytes=prepare_metadata(target) if metadata else (b'',b'')
    return recovery.reserve(ConstructionOriginal(connection,original,target,definitions,
        recipe,input_bytes,160 if metadata else 128))


def construct_provisional_catalog_layout(connection,*,metadata=False):
    recovery=ProvisionalConstructionRecovery()
    try:
        reference=prepare_provisional_catalog_construction(connection,recovery,metadata=metadata)
        return execute_provisional_catalog_construction(recovery,reference)
    except BaseException as error:
        # The exception retains custody even when ordinary result publication fails.
        references=recovery.references()
        if references:
            error.recovery=recovery;error.recovery_reference=references[-1]
        raise


def _construction_attempt(definitions):
    return {'original_definition_baseline':definitions,'phase':'target_observed','submitted_statements':[],
            'rollback_submitted':False,'rollback_reply_observed':False}


def execute_provisional_catalog_construction(recovery,reference):
    """Run actual exact-source construction and always roll back its own transaction.

    No caller runtime transaction is adopted. No COMMIT, marker publication,
    namespace repair or retry path exists. Bounds cover retained data only.
    """
    acquired=False
    try:
        connection=recovery.acquire(reference)
        acquired=True
        retained=recovery.inspect(reference).original
        original=retained.statements;statements=json.loads(original)['statements']
        definitions,definition_query,definition_profile=_definition_baseline(original)
        if definitions!=retained.definition_baseline:raise ValueError('Original retained definition baseline required')
        if retained.metadata_recipe:validate_metadata_preflight(retained)
        if getattr(connection,'_transaction_status',None)!=b'I':
            raise ValueError('Original idle installer-owned administrative connection required')
        target=retained.target
        version=json.loads(target)['version']
        if type(version) is not str or not version.isascii() or not version.isdigit() or version!=definition_profile['nativeVersion']:
            raise ValueError('Selected PostgreSQL17.11 source compilation profile required')
        begun=False;primary=None;cleanup=None;observed=b'';restored=False;prior_namespace=None
        definition_observed=b'';metadata_observed=b''
        attempt=_construction_attempt(definitions)
    except BaseException as error:
        if acquired:recovery.fail_preflight(reference,error)
        raise
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
        attempt['namespace_observation']=observed
        compare_source_membership(json.loads(original)['membership'],json.loads(observed))
        definition_observed=_native_text(connection,definition_query.decode('utf8'))
        attempt['definition_observation']=definition_observed
        if json.loads(definition_observed)!=json.loads(definition_profile['compiledOriginal']):
            raise ValueError('Independent release definition correspondence mismatch')
        if retained.metadata_recipe:
            metadata_observed=execute_metadata(connection,retained,definition_observed,attempt)
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
    recovery.settle(reference,rollback_confirmed=restored,primary=primary,cleanup=cleanup)
    if primary is not None or cleanup is not None:
        failure=CatalogConstructionFailure(primary,cleanup,original,target,restored,retained.connection,attempt)
        failure.recovery=recovery;failure.recovery_reference=reference
        raise failure from primary
    return ProvisionalCatalogConstruction(original,target,observed,str(len(statements)),restored,original_definition_baseline=definitions,definition_observation=definition_observed,recovery=recovery,recovery_reference=reference,metadata_observation=metadata_observed)


def compare_source_membership(expected,observed):
    """Original declaration membership only; definitions and authority unresolved."""
    relations=observed['relations']
    if any(r['relkind'] not in ('r','p','S','i','I') for r in relations):
        raise ValueError('Unaccounted original relation kind')
    by_oid={r['oid']:r for r in relations}
    tables=[r for r in relations if r['relkind'] in ('r','p')]
    actual={r['relname']:r for r in tables}
    if len(actual)!=len(tables) or set(actual)!={t['name'] for t in expected['tables']}:
        raise ValueError('Original table membership mismatch')
    for table in expected['tables']:
        relation=actual[table['name']]
        columns=sorted((a for a in observed['columns'] if a['attrelid']==relation['oid'] and a['attnum']>0),key=lambda a:a['attnum'])
        if (relation['relkind']!=table['kind'] or any(a['attisdropped'] for a in columns)
            or [(a['attname'],str(a['attnum'])) for a in columns]!=[(a['name'],a['ordinal']) for a in table['columns']]):
            raise ValueError('Original ordered column membership mismatch')
    sequences=[r['relname'] for r in relations if r['relkind']=='S']
    if sorted(sequences)!=sorted(s['name'] for s in expected['sequences']):
        raise ValueError('Original sequence membership mismatch')
    constraint_indexes={c['native']['conindid'] for c in observed['constraints'] if c['native']['contype'] in ('p','u','x')}
    indexes=[]
    for entry in observed['indexes']:
        native=entry['native'];relation=by_oid[native['indexrelid']]
        identity=(by_oid[native['indrelid']]['relname'],relation['relname'])
        if native['indexrelid'] not in constraint_indexes:indexes.append(identity)
    if sorted(indexes)!=sorted((i['table'],i['name']) for i in expected['indexes']):
        raise ValueError('Original standalone index membership mismatch')
    routines=[(r['native']['proname'],r['native']['prokind'],tuple(r['inputTypes'])) for r in observed['routines']]
    if sorted(routines)!=sorted((r['name'],r['kind'],tuple(r['inputs'])) for r in expected['routines']):
        raise ValueError('Original routine overload membership mismatch')

    sequence_parameters={s['name']:{k:v for k,v in s.items() if k!='name'} for s in observed['sequenceParameters']}
    if len(sequence_parameters)!=len(observed['sequenceParameters']) or sequence_parameters!={s['name']:s['parameters'] for s in expected['sequences']}:
        raise ValueError('Original sequence parameters mismatch')
    expected_routines={(r['name'],r['kind'],tuple(r['inputs'])):r['execution'] for r in expected['routines']}
    for entry in observed['routines']:
        native=entry['native'];identity=(native['proname'],native['prokind'],tuple(entry['inputTypes']))
        fields={'language':entry['language'],'body':native['prosrc'],'security':native['prosecdef'],'volatility':native['provolatile'],
                'parallel':native['proparallel'],'strict':native['proisstrict'],'leakproof':native['proleakproof'],'settings':native['proconfig'] or []}
        if fields!=expected_routines[identity]:raise ValueError('Original routine execution definition mismatch')

    column_definitions={(c['table'],c['column']):{k:v for k,v in c.items() if k not in ('table','column')} for c in observed['columnDefinitions']}
    original_definitions={(t['name'],c['name']):c['definition'] for t in expected['tables'] for c in t['columns']}
    if len(column_definitions)!=len(observed['columnDefinitions']) or column_definitions!=original_definitions:
        raise ValueError('Original column definition fields mismatch')
