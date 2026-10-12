"""Private complete fixture dependency cuts; comparisons do not confer authority.

UMF owns semantic traversal. This composes original dependency coverage with
native recipes, not authenticated mapping/decoder qualification or policy execution.
"""
from dataclasses import dataclass
from ._security_fact_coverage import _FactBindingDeclaration, _inspect_fact_coverage, _OriginalFactSources, _inspect_original_fact_sources
from ._psycopg_fact_cut import _FactColumnComparison, _FactRelationComparison, _run_fenced_fact_operation


@dataclass(frozen=True)
class _DependencyFactProvider:
    kind: str
    reference: tuple
    relation: _FactRelationComparison
    column: _FactColumnComparison | None = None


def _run_dependency_fact_operation(host, transaction, epoch, original_bytes,
                                   expected_sha256, providers, callback):
    if type(providers) is not tuple or not 1<=len(providers)<=8192:
        raise ValueError('Bounded original dependency provider tuple required')
    declarations=[]; relations={}
    for index,provider in enumerate(providers):
        if type(provider) is not _DependencyFactProvider:
            raise ValueError('Exact dependency provider comparison required')
        kind,reference,relation,column=provider.kind,provider.reference,provider.relation,provider.column
        if type(relation) is not _FactRelationComparison or type(relation.columns) is not tuple or len(relation.columns)>1600:
            raise ValueError('Exact original fact relation required')
        if kind=='field':
            if type(column) is not _FactColumnComparison:raise ValueError('Field column comparison required')
        elif kind=='association':
            if column is not None:raise ValueError('Association table presence comparison required')
        else:raise ValueError('Original dependency kind required')
        declarations.append(_FactBindingDeclaration(kind,reference,str(index)))
        # Copy comparison primitives before any host/native invocation. No issuer
        # or semantic relationship is inferred from relation/column names.
        base=(relation.schema,relation.name,relation.oid,relation.owner_oid,relation.guard_source)
        columns=relation.columns+((column,) if column is not None else ())
        copied=[]
        for c in columns:
            if type(c) is not _FactColumnComparison:raise ValueError('Exact original field descriptor required')
            copied.append(_FactColumnComparison(c.name,c.number,c.type_oid,c.type_modifier,c.not_null,c.collation_oid,c.generated,c.identity))
        if type(base[2]) is not int:raise ValueError('Exact native relation identity required')
        prior=relations.get(base[2])
        if prior is not None and prior[0]!=base:raise ValueError('Conflicting original relation comparisons')
        combined=(() if prior is None else prior[1])+tuple(copied)
        unique=[]
        for c in combined:
            if c not in unique:unique.append(c)
        relations[base[2]]=(base,tuple(unique))
    coverage=_inspect_fact_coverage(original_bytes,expected_sha256,tuple(declarations))
    if coverage.missing:raise ValueError('Incomplete original semantic dependency provider coverage')
    recipe=tuple(_FactRelationComparison(*base,columns) for base,columns in relations.values())
    return _run_fenced_fact_operation(host,transaction,epoch,recipe,callback)


def _epoch_dependency_recipe(epoch, expected_sha256, sources=None):
    """Derive recipes from exact selected native epoch profile bytes.

    Lifecycle issuer, original semantic mapping and decoder/source closure remain
    unqualified. There is no caller provider override and no authority result.
    """
    import json
    from ._psycopg_epoch_cut import _EpochComparison
    if type(epoch) is not _EpochComparison:raise ValueError('Exact original epoch comparison required')
    selected=_EpochComparison(epoch.installation,epoch.epoch,epoch.incarnation,epoch.profile,epoch.evidence)
    raw=selected.profile
    if type(raw) is not bytes or not 1<=len(raw)<=65536:raise ValueError('Bounded original provider profile required')
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('Duplicate provider profile member')
            result[k]=v
        return result
    def closed(value,keys):
        if type(value) is not dict or set(value)!=set(keys):raise ValueError('Closed original provider profile required')
        return value
    try:profile=json.loads(raw,object_pairs_hook=unique)
    except (UnicodeError,RecursionError) as error:raise ValueError('Original provider profile JSON required') from error
    if type(profile) is dict and profile.get('kind') in ('truss-flat-fact-provider-fixture/0.2','truss-flat-fact-provider-fixture/0.3','truss-flat-fact-provider-fixture/0.4','truss-flat-fact-provider-fixture/0.5'):
        closed(profile,('kind','requirementsSha256','providers','policyUtf8','resolutionUtf8')+(('caller',) if profile['kind'].endswith(('/0.3','/0.4','/0.5')) else ())+(('executor',) if profile['kind'].endswith(('/0.4','/0.5')) else ()))
        if profile['kind'].endswith(('/0.3','/0.4','/0.5')):
            caller=closed(profile['caller'],('sessionRoleOid','effectiveRoleOid','subjectKey'))
            for value in (caller['sessionRoleOid'],caller['effectiveRoleOid']):
                if type(value) is not str or not value.isascii() or not value.isdigit() or not 0<int(value)<=4294967295:
                    raise ValueError('Original native caller role identities required')
            if type(caller['subjectKey']) is not list or not 1<=len(caller['subjectKey'])<=32:
                raise ValueError('Bounded original subject key carrier required')
        if profile['kind'].endswith(('/0.4','/0.5')):
            executor=closed(profile['executor'],('sessionRoleOid','effectiveRoleOid'))
            for value in executor.values():
                if type(value) is not str or not value.isascii() or not value.isdigit() or not 0<int(value)<=4294967295:
                    raise ValueError('Original native executor identities required')
        if type(sources) is not _OriginalFactSources:
            raise ValueError('Original policy/resolution sources required for source-bound profile')
        for key,original in (('policyUtf8',sources.policy),('resolutionUtf8',sources.resolution)):
            if type(original) is not bytes or not 1<=len(original)<=65536 or type(profile[key]) is not str:
                raise ValueError('Bounded original policy/resolution bytes required')
            if profile[key].encode('utf8')!=original:
                raise ValueError('Exact native profile policy/resolution correspondence required')
    else:
        closed(profile,('kind','requirementsSha256','providers'))
    if profile['kind'] not in ('truss-flat-fact-provider-fixture/0.1','truss-flat-fact-provider-fixture/0.2','truss-flat-fact-provider-fixture/0.3','truss-flat-fact-provider-fixture/0.4','truss-flat-fact-provider-fixture/0.5') or profile['requirementsSha256']!=expected_sha256:
        raise ValueError('Original requirement/profile correspondence required')
    values=profile['providers']
    if type(values) is not list or not 1<=len(values)<=8192:raise ValueError('Bounded original provider list required')
    def column(value):
        keys=('name','number','type_oid','type_modifier','not_null','collation_oid','generated','identity')
        closed(value,keys)
        return _FactColumnComparison(*(value[k] for k in keys))
    providers=[]
    for value in values:
        closed(value,('kind','reference','relation','column'))
        reference=value['reference']
        if type(reference) is not list or len(reference)!=3:raise ValueError('Original qualified provider reference required')
        r=value['relation'];keys=('schema','name','oid','owner_oid','guard_source','columns');closed(r,keys)
        if type(r['columns']) is not list or len(r['columns'])>1600:raise ValueError('Bounded original relation columns required')
        relation=_FactRelationComparison(*(r[k] for k in keys[:-1]),tuple(column(c) for c in r['columns']))
        providers.append(_DependencyFactProvider(value['kind'],tuple(reference),relation,None if value['column'] is None else column(value['column'])))
    # The nested native epoch comparison must match these same exact selected
    # bytes; a caller-supplied replacement cannot match the installed original.
    return selected,tuple(providers)



def _run_epoch_bound_dependency_fact_operation(host, transaction, epoch,
                                               original_bytes, expected_sha256, callback):
    selected,providers=_epoch_dependency_recipe(epoch,expected_sha256)
    return _run_dependency_fact_operation(host,transaction,selected,original_bytes,expected_sha256,providers,callback)


@dataclass(frozen=True)
class _DependencyRelationCells:
    relation: tuple
    fields: tuple
    associations: tuple
    rows: tuple


def _capture_epoch_bound_dependency_cells(host, transaction, epoch, original_bytes, expected_sha256, *, sources=None):
    """Fixed native raw-cell capture, without caller SQL/decoder callback.

    Selected ordinary bool/int8/text columns only. Raw data carries no trusted
    semantic fact, policy decision, final disclosure or authorization capability.
    """
    from psycopg import sql
    if sources is not None:
        if type(sources) is not _OriginalFactSources:
            raise ValueError('Original policy/resolution source bundle required')
        sources=_OriginalFactSources(sources.policy,sources.resolution)
        _inspect_original_fact_sources(original_bytes,expected_sha256,sources)
    selected,providers=_epoch_dependency_recipe(epoch,expected_sha256,sources)
    import json
    if json.loads(selected.profile)['kind'].endswith(('/0.4','/0.5')):
        raise ValueError('Original delegated caller scope required')
    groups={}
    for p in providers:
        group=groups.setdefault(p.relation.oid,{'relation':p.relation,'fields':[],'associations':[]})
        if p.kind=='field':
            c=p.column
            if c is None or c.type_oid not in (16,20,25) or c.generated!='':
                raise ValueError('Selected ordinary bool/int8/text capture column required')
            group['fields'].append((p.reference,c))
        else:group['associations'].append(p.reference)
    if len(groups)>32 or any(len(g['fields'])>32 for g in groups.values()):
        raise ValueError('Bounded selected raw capture profile required')
    def capture(cursor):
        _verify_native_profile_caller(cursor,selected.profile)
        return _capture_dependency_relation_cells(cursor,groups)
    return _run_dependency_fact_operation(host,transaction,selected,original_bytes,expected_sha256,providers,capture)


def _capture_dependency_relation_cells(cursor, groups):
    from psycopg import sql
    results=[];total_rows=0;total_bytes=0
    for oid,group in sorted(groups.items()):
        r=group['relation'];fields=group['fields']
        terms=[sql.SQL('COALESCE(pg_catalog.octet_length({}::pg_catalog.text),0)').format(sql.Identifier(c.name)) for _,c in fields]
        size=sql.SQL(' OPERATOR(pg_catalog.+) ').join(terms) if terms else sql.SQL('0')
        overflow=sql.SQL('({}) OPERATOR(pg_catalog.>) 65536').format(size)
        columns=[sql.SQL('CASE WHEN {} THEN NULL ELSE {}::pg_catalog.text END AS {}').format(overflow,sql.Identifier(c.name),sql.Identifier('f'+str(i))) for i,(_,c) in enumerate(fields)]
        columns.append(sql.SQL('({})::pg_catalog.text AS oversize').format(overflow))
        cursor.execute(sql.SQL('SELECT {} FROM ONLY {} LIMIT 101').format(sql.SQL(',').join(columns),sql.Identifier(r.schema,r.name)),prepare=False,binary=False)
        if (cursor.description is None or tuple(d.name for d in cursor.description)!=tuple('f'+str(i) for i in range(len(fields)))+('oversize',)
                or any(d.type_code!=25 for d in cursor.description)):
            raise ValueError('Original native raw-cell text descriptors required')
        rows=cursor.fetchmany(101)
        if len(rows)>100:raise ValueError('Bounded complete raw relation capture required')
        total_rows+=len(rows)
        if total_rows>512:raise ValueError('Bounded complete raw fixture capture required')
        captured=[]
        for row in rows:
            if type(row) is not tuple or len(row)!=len(fields)+1 or row[-1]!='false':
                raise ValueError('Oversize or malformed native raw row refuses capture')
            values=row[:-1]
            for value,(_,c) in zip(values,fields):
                if value is None:
                    if c.not_null:raise ValueError('Original non-null native value required')
                elif type(value) is not str:raise ValueError('Original native text cell required')
                else:total_bytes+=len(value.encode('utf8'))
            if total_bytes>1048576:raise ValueError('Bounded complete raw payload capture required')
            captured.append(tuple(values))
        results.append(_DependencyRelationCells((r.schema,r.name,oid),tuple((ref,c.number,c.type_oid) for ref,c in fields),tuple(group['associations']),tuple(captured)))
    return tuple(results)


def _verify_native_profile_caller(cursor, profile_bytes):
    import json
    caller=json.loads(profile_bytes).get('caller')
    if caller is None:return
    cursor.execute("SELECT s.oid::pg_catalog.text AS session_role_oid,c.oid::pg_catalog.text AS effective_role_oid FROM pg_catalog.pg_roles s CROSS JOIN pg_catalog.pg_roles c WHERE s.rolname OPERATOR(pg_catalog.=) session_user AND c.rolname OPERATOR(pg_catalog.=) current_user",prepare=False,binary=False)
    roles=cursor.fetchmany(2)
    if (cursor.description is None or tuple(d.name for d in cursor.description)!=('session_role_oid','effective_role_oid')
            or any(d.type_code!=25 for d in cursor.description) or roles!=[(caller['sessionRoleOid'],caller['effectiveRoleOid'])]):
        raise ValueError('Original native caller/profile correspondence required')
    if json.loads(profile_bytes).get('kind')=='truss-flat-fact-provider-fixture/0.5':
        _require_native_scram_login(cursor)


def _verify_native_scram_profile_caller(cursor, profile_bytes):
    """Private credential/login check; not subject, endpoint or issuer authority.

    Use only inside the original registered host operation after original profile
    admission. Native authentication survives HBA changes; this check cannot pin
    policy for other connections or establish credential custody.
    """
    import json
    if type(profile_bytes) is not bytes or type(json.loads(profile_bytes).get('caller')) is not dict:
        raise ValueError('Original authenticated caller profile required')
    _verify_native_profile_caller(cursor,profile_bytes)
    _require_native_scram_login(cursor)


def _require_native_scram_login(cursor):
    cursor.execute('SELECT system_user AS authenticated_identity,session_user::pg_catalog.text AS session_role_name',prepare=False,binary=False)
    rows=cursor.fetchmany(2)
    if (cursor.description is None
            or tuple(d.name for d in cursor.description)!=('authenticated_identity','session_role_name')
            or any(d.type_code!=25 for d in cursor.description)
            or len(rows)!=1 or len(rows[0])!=2
            or type(rows[0][0]) is not str or type(rows[0][1]) is not str
            or rows[0][0]!='scram-sha-256:'+rows[0][1]):
        raise ValueError('Original native SCRAM login correspondence required')
