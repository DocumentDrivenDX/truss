"""Truss-owned catalog composition/execution; Weft owns all SQL interpretation."""
from decimal import Decimal
import re
import base64
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping
from .execution import Error, Ok, ExecutionFailure
from .contracts import TextValue
from .query import QueryAbsent, QueryRelatedKeys, QueryRows, QueryDiagnostic, QueryRefused, QueryUnavailable, QueryPage, QueryPageCursor, QueryReadPosition, QueryCatalogSources

BACKEND = {'backendId': 'truss.postgresql.runtime', 'backendVersion': '0.4.41',
           'targetProfile': 'truss-runtime-pg18.6/0.5', 'interfaceVersion': 'weft-backend/0.2.7'}


def compiler(*, engine_catalog=False, engine_pages=False):
    try:
        import weft
        related_candidate = weft.__version__ == '0.4.42-dev.0' and all(callable(getattr(weft,name,None)) for name in (
            'compile_truss_runtime_json','compile_truss_runtime_page_json',
            'compile_engine_read_json','check_engine_read_json',
            'compile_engine_page_json','check_engine_page_json'))
        if weft.__version__ not in ('0.4.41','0.4.42') and not related_candidate and not (weft.__version__ == '0.4.41-dev.0' and callable(getattr(weft,'compile_engine_export_json',None))):
            return None
        if engine_catalog and not callable(getattr(weft,'check_engine_read_json',None)):return None
        if engine_pages and not callable(getattr(weft,'check_engine_page_json',None)):return None
        return weft.compile_truss_runtime_json
    except (ImportError, AttributeError):
        return None


def _date_token(value):
    if type(value) is not str or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        raise ValueError('Canonical Gregorian date required')
    date.fromisoformat(value)
    return value


def _decode_scalar(value, family):
    if family == 'string' and type(value) is str:
        return value
    if family == 'boolean' and type(value) is bool:
        return value
    if family == 'decimal' and type(value) is str:
        result=Decimal(value)
        if not result.is_finite():raise ValueError('Finite exact decimal result required')
        return result
    if family == 'integer' and type(value) is str:
        if not re.fullmatch(r'-?(0|[1-9][0-9]*)', value):
            raise ValueError('Canonical integer carrier required')
        result = int(Decimal(value))
        return result
    raise ValueError('Exact selected scalar result required')


def _relationship_key_types(types,maximum=128):
    if not types or len(types)>maximum:raise ValueError('Bounded complete key types required')
    for t in types:
        if t.get('nullable') is not False or set(t)!= {'family','facets','nullable'}:raise ValueError('Required key types required')
        family,facets=t['family'],t['facets']
        valid=(family in ('string','boolean') and facets=={} or family=='integer' and facets in ({},{'integerWidth':{'bits':64,'signed':True}}) or family=='decimal' and facets in ({'precision':18,'scale':4},{'precision':18,'scale':2},{'precision':12,'scale':2}))
        if not valid:raise ValueError('Supported exact relationship key required')
    return types

def _decode_key_tuple(item,types):
    if type(item) is not list or len(item)!=len(types):raise ValueError('Complete relationship key tuple required')
    return tuple(_decode_scalar(value,t['family']) for value,t in zip(item,types,strict=True))


def _page_key_token(value,t):
    family=t['family']
    if family=='string' and type(value) is str:token=value
    elif family=='boolean' and type(value) is bool:token='true' if value else 'false'
    elif family=='integer' and type(value) is int:token=str(Decimal(value))
    elif family=='decimal' and type(value) is Decimal and value.is_finite():token=format(value,'f')
    else:raise ValueError('Exact typed continuation key required')
    if len(token.encode('utf8'))>65536:raise ValueError('Bounded continuation key required')
    return token


def _decode_value(value, descriptor_id, descriptors):
    descriptor = next(d for d in descriptors if d['identity'] == descriptor_id)
    optional = descriptor.get('availability') == 'absent-allowed'
    if optional:
        if value == {'state': 'absent'}:
            return QueryAbsent()
        if value == {'state': 'null'}:
            return None
        if type(value) is not dict or set(value) != {'state', 'value'} or value['state'] != 'value':
            raise ValueError('Exact optional value envelope required')
        value = value['value']
    if descriptor['kind'] == 'scalar':
        return _decode_scalar(value, descriptor['type']['family'])
    if descriptor['kind'] == 'exactScalar':
        kind = descriptor['scalarType']
        if kind not in ('timestamp', 'binary', 'date') or type(value) is not str:
            raise ValueError('Exact timestamp/binary/date token required')
        if kind == 'date':
            _date_token(value)
        return TextValue(kind=kind, text=value)
    if descriptor['kind'] == 'sequence':
        if type(value) is not list:raise ValueError('Complete logical sequence required')
        return tuple(_decode_value(item,descriptor['item'],descriptors) for item in value)
    if descriptor['kind'] == 'map':
        if type(value) is not dict or any(type(key) is not str for key in value):raise ValueError('Complete logical map required')
        return MappingProxyType({key:_decode_value(value[key],descriptor['item'],descriptors) for key in sorted(value)})
    if descriptor['kind'] == 'record':
        members = descriptor['members']
        if type(value) is not dict or set(value) != {m['name'] for m in members}:
            raise ValueError('Complete logical record required')
        return MappingProxyType({m['name']: _decode_value(value[m['name']], m['identity'], descriptors) for m in members})
    raise ValueError('Unsupported query result shape')


def _decode_rows(raw_rows, artifact, maximum_rows, maximum_bytes):
    columns = artifact['columns']
    if len(raw_rows) > maximum_rows:
        return QueryRefused(code='limits')
    total = 0
    rows = []
    graph = artifact['logicalPlan']['typeGraph']
    for raw_row in raw_rows:
        if len(raw_row) != len(columns):
            raise ValueError('Exact compiled result shape required')
        decoded = []
        for raw, column in zip(raw_row, columns, strict=True):
            if type(raw) is not str:
                raise ValueError('Exact nonnull text query carrier required')
            total += len(raw.encode('utf8'))
            if total > maximum_bytes:
                return QueryRefused(code='limits')
            representation = column['representation']
            if representation['kind'] == 'scalar':
                family = representation['logicalType']['family']
                value = raw == 'true' if family == 'boolean' else raw
                if family == 'boolean' and raw not in ('true', 'false'):
                    raise ValueError('Exact boolean result required')
                decoded.append(_decode_scalar(value, family))
            elif representation['kind'] == 'value':
                decoded.append(_decode_value(json.loads(raw), representation['descriptor'], graph))
            elif representation['kind'] == 'nativeMetadata':
                metadata = representation['metadata']
                family = 'integer' if metadata == 'version' else 'string'
                nullable = metadata in ('originalAuthor', 'originalAt', 'loadId')
                if metadata not in ('version', 'createdBy', 'updatedBy', 'createdAt', 'updatedAt', 'originalAuthor', 'originalAt', 'loadId') or representation['logicalType'] != {'family': family, 'facets': {}, 'nullable': nullable} or representation['carrier'] != 'text' or representation['decoder'] != ('exact-integer' if family == 'integer' else 'text'):
                    raise ValueError('Exact native metadata descriptor required')
                value = json.loads(raw)
                if value is None:
                    if not nullable:
                        raise ValueError('Required native metadata missing')
                    decoded.append(None)
                else:
                    exact = _decode_scalar(value, family)
                    if metadata == 'version' and exact < 1:
                        raise ValueError('Positive exact record version required')
                    if metadata in ('createdAt','updatedAt'):
                        if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z',exact):
                            raise ValueError('Canonical native UTC timestamp required')
                        datetime.fromisoformat(exact)
                    decoded.append(exact)
            elif representation['kind'] == 'completeRelatedKeys':
                value=json.loads(raw);key=representation['key'];types=_relationship_key_types(key['types']);bound=representation['bound']
                if type(bound) is not int or not 1<=bound<=100 or len(key['fields'])!=len(types) or type(value) is not list or len(value)>bound:raise ValueError('Complete relationship list required')
                decoded.append(tuple(_decode_scalar(item,types[0]['family']) for item in value) if len(types)==1 else tuple(_decode_key_tuple(item,types) for item in value))
            elif representation['kind'] == 'relatedKeys':
                value=json.loads(raw);key=representation['key'];bound=representation['bound'];types=_relationship_key_types(key['types'])
                if type(bound) is not int or not 1<=bound<=1000 or len(key['fields'])!=len(types):raise ValueError('Exact bounded key metadata required')
                if type(value) is not dict or set(value)!={'items','truncated'} or type(value['items']) is not list or type(value['truncated']) is not bool or len(value['items'])>bound or (value['truncated'] and len(value['items'])!=bound):raise ValueError('Exact bounded relationship key result required')
                decoded.append(QueryRelatedKeys(items=tuple(_decode_key_tuple(item,types) for item in value['items']),truncated=value['truncated']))
            else:
                raise ValueError('Unknown compiled representation refused')
        rows.append(tuple(decoded))
    return QueryRows(columns=tuple(c['outputName'] for c in columns), rows=tuple(rows), catalog_revision=0)


def run_query(host, transaction, *, sql, document_ids, parameters, maximum_rows,
              maximum_scan_rows, maximum_bytes, manifest, digest, pin_cursor, read_profile, page_size=None, page_cursor=None, engine_program=None, capture_catalog=False):
    try:
        valid = type(sql) is str and 1 <= len(sql.encode('utf8')) <= 1048576 and '\0' not in sql
        valid = valid and type(document_ids) is tuple and 1 <= len(document_ids) <= 32 and len(set(document_ids)) == len(document_ids)
        valid = valid and all(type(d) is str and 1 <= len(d.encode('utf8')) <= 4096 and '\0' not in d for d in document_ids)
        valid = valid and isinstance(parameters, Mapping) and len(parameters) <= 1024
        valid = valid and all(type(k) is str and 1 <= len(k.encode('utf8')) <= 4096 and '\0' not in k and type(v) in (str, int, bool, Decimal, TextValue) for k, v in parameters.items())
        valid = valid and all(type(v) is not str or len(v.encode('utf8')) <= 1048576 and '\0' not in v for v in parameters.values())
    except (UnicodeError, TypeError, ValueError):
        valid = False
    valid=valid and (read_profile is None or type(read_profile) is str and read_profile in ('entity-page','related-entity-page','count-summary','complete-entity'))
    if not valid:
        return Ok(QueryRefused(code='invalid_query'))
    if any(type(n) is not int for n in (maximum_rows, maximum_scan_rows, maximum_bytes)) or not 1 <= maximum_rows <= 10000 or not 1 <= maximum_scan_rows <= 10000 or not 1 <= maximum_bytes <= 16777216:
        return Ok(QueryRefused(code='limits'))
    page_state = None
    if page_size is not None:
        if type(page_size) is not int or not 1 <= page_size <= 999 or read_profile is not None:
            return Ok(QueryRefused(code='limits'))
        if page_cursor is not None:
            if type(page_cursor) is not QueryPageCursor or type(page_cursor.original_bytes) is not bytes or not 1 <= len(page_cursor.original_bytes) <= 65536:
                return Ok(QueryRefused(code='invalid_query'))
            try:
                page_state = json.loads(page_cursor.original_bytes)
                if type(page_state) is not dict or set(page_state) != {'profile','context','after'} or page_state['profile'] != 'truss-query-page/0.2' or type(page_state['context']) is not str or type(page_state['after']) is not list or not page_state['after'] or any(type(v) is not str for v in page_state['after']):
                    return Ok(QueryRefused(code='invalid_query'))
            except (ValueError, UnicodeError):
                return Ok(QueryRefused(code='invalid_query'))
    if type(capture_catalog) is not bool or engine_program is not None and (type(engine_program) is not str or len(engine_program.encode("utf8")) > 4194304) or capture_catalog and (page_size is not None or read_profile is not None) or engine_program is not None and read_profile is not None:
        return Ok(QueryRefused(code="invalid_query"))
    compile_query = compiler(engine_catalog=engine_program is not None,engine_pages=page_size is not None and engine_program is not None)
    if compile_query is None:
        return Ok(QueryUnavailable(reason='compiler'))
    if page_size is not None:
        try:
            import weft
            compile_query = weft.compile_truss_runtime_page_json
        except (ImportError, AttributeError):
            return Ok(QueryUnavailable(reason='compiler'))
    values={}
    exact_values={}
    for name,value in parameters.items():
        if type(value) is TextValue:
            if value.kind not in ('binary','timestamp','date') or type(value.text) is not str or len(value.text) > 1048576:
                return Ok(QueryRefused(code='invalid_query'))
            try:
                if value.kind == 'date': _date_token(value.text)
                decoded = base64.b64decode(value.text, validate=True) if value.kind=='binary' else None
                if decoded is not None and base64.b64encode(decoded).decode('ascii') != value.text:
                    return Ok(QueryRefused(code='invalid_query'))
            except (ValueError, UnicodeError):
                return Ok(QueryRefused(code='invalid_query'))
            exact_values[name]={'scalarType':value.kind,'value':value.text}
            continue
        if type(value) is Decimal:
            if not value.is_finite():return Ok(QueryRefused(code='invalid_query'))
            parts=value.as_tuple();exponent=parts.exponent;digits=len(parts.digits)
            size=(digits+exponent if exponent>=0 else digits+1 if digits+exponent>0 else 2-exponent)+parts.sign
            if size>1048576:return Ok(QueryRefused(code='limits'))
            token=format(value,'f');family='decimal'
        elif type(value) is int:token=str(Decimal(value));family='integer'
        elif type(value) is bool:token='true' if value else 'false';family='boolean'
        else:token=value;family='string'
        if len(token.encode('utf8'))>1048576:return Ok(QueryRefused(code='limits'))
        values[name]={'family':family,'value':token}
    def execute(cursor, observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.query_binding(%s::pg_catalog.jsonb,%s,%s,%s,%s,%s)',
            (json.dumps(document_ids), maximum_scan_rows, maximum_rows, maximum_bytes, manifest['releaseId'], digest), prepare=False)
        bundle = json.loads(bytes(cursor.fetchone()[0]))
        binding_json = bundle['bindingJson']
        binding = json.loads(binding_json)
        if binding != bundle['binding'] or binding['releaseId'] != manifest['releaseId'] or binding['releaseSha256'] != digest:
            raise ValueError('Exact installed query binding required')
        binding_sha = sha256(binding_json.encode('utf8')).hexdigest()
        request = {'interfaceVersion': 'weft-compile/0.2.7', 'dialect': 'weft-sql/0.2.0', 'sql': sql,
                   'timestampComparisonProfile':'umf-rfc3339-exact-instant/1.0.0', 'modules': bundle['modules'], 'parameters': values, 'exactParameters': exact_values, 'options': {'allowCandidate': True},
                   'target': {'backendId': BACKEND['backendId'], 'backendVersion': BACKEND['backendVersion'],
                              'targetProfile': BACKEND['targetProfile'], 'bindingJson': binding_json, 'bindingSha256': binding_sha}}
        if read_profile is not None:request['readProfile']={'version':'weft-truss-entity-read/0.3.0' if read_profile=='complete-entity' else 'weft-application-read/0.2.0','subset':read_profile}
        page_metadata = None
        if page_size is not None:
            # Each page composes and reauthorizes the current accepted catalog.
            context = sha256(json.dumps({'sql':sql,'parameters':values,'exactParameters':exact_values,'documents':document_ids,
                'binding':binding,'actorOid':bundle['actorOid'],'pageSize':page_size},sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf8')).hexdigest()
            if page_state is not None and page_state['context'] != context:
                return QueryRefused(code='stale_context')
            response = json.loads(compile_query(json.dumps(request,ensure_ascii=False),page_size,None if page_state is None else page_state['after']))
            if response.get('status') == 'compiled':
                if response.get('interfaceVersion') != 'weft-sql-page/0.2' or set(response) != {'interfaceVersion','status','artifact','page'}:
                    raise ValueError('Exact owner page response required')
                artifact, page_metadata = response['artifact'], response['page']
            else:
                artifact = response
        else:
            artifact = json.loads(compile_query(json.dumps(request, ensure_ascii=False)))
        if artifact['status'] != 'compiled':
            cursor.execute('SELECT truss.query_scope(%s::pg_catalog.jsonb)', (binding_json,), prepare=False)
            diagnostics = tuple(QueryDiagnostic(code=d['code'], message=d['message']) for d in artifact.get('diagnostics', ()))
            unsupported = any(d.code in ('WFT-CAPABILITY', 'WFT-TYPE', 'WFT-PROFILE') for d in diagnostics)
            return QueryRefused(code='unsupported_query' if unsupported else 'invalid_query', diagnostics=diagnostics)
        if artifact['interfaceVersion'] != request['interfaceVersion'] or artifact['dialect'] != request['dialect'] or artifact['logicalPlan']['irVersion'] != 'weft-ir/0.2.7':
            raise ValueError('Exact selected compile/dialect/IR versions required')
        if artifact['backend'] != BACKEND or artifact['bindingSha256'] != binding_sha or artifact['modelPins'] != [m['pin'] for m in bundle['modules']]:
            raise ValueError('Original compiled binding/model/backend required')
        if page_size is not None and page_cursor is not None and page_cursor.sort_values is not None:
            types = _relationship_key_types(artifact['logicalPlan']['pageKey']['types'],maximum=1024)
            if type(page_cursor.sort_values) is not tuple or len(types)!=len(page_cursor.sort_values):
                return QueryRefused(code='invalid_query')
            try:
                if [_page_key_token(value,t) for value,t in zip(page_cursor.sort_values,types,strict=True)] != page_state['after']:
                    return QueryRefused(code='stale_context')
            except (ValueError,UnicodeError):return QueryRefused(code='invalid_query')
        if engine_program is not None:
            import weft
            checked = json.loads(weft.check_engine_read_json(engine_program, json.dumps(request, ensure_ascii=False)) if page_size is None else weft.check_engine_page_json(engine_program, json.dumps(request, ensure_ascii=False), json.dumps(None if page_state is None else page_state["after"])))
            profile_pair=(checked.get('compiler'),checked.get('version'))
            profile_kind='read' if page_size is None else 'page'
            if (checked.get("status") != "compiled" or profile_pair not in (
                    ('truss-runtime','weft.engine-'+profile_kind+'/0.1'),
                    ('truss-runtime-binary','weft.engine-'+profile_kind+'/0.2')) or checked.get("artifact") != artifact
                or page_size is not None and (checked.get("pageSize") != page_size or checked.get("page") != page_metadata)):
                cursor.execute('SELECT truss.query_scope(%s::pg_catalog.jsonb)', (binding_json,), prepare=False)
                return QueryRefused(code='stale_context')
        if capture_catalog:
            cursor.execute('SELECT truss.query_scope(%s::pg_catalog.jsonb)', (binding_json,), prepare=False)
            return QueryCatalogSources(request_json=json.dumps(request, ensure_ascii=False, separators=(',', ':')))
        if not artifact['obligations'] or any(o['id'] != 'truss.runtime.context/0.1' or o['owner'] != 'host' for o in artifact['obligations']):
            raise ValueError('Every compiled obligation must have an installed handler')
        slots = artifact['parameters']
        if [s['position'] for s in slots] != list(range(1, len(slots) + 1)) or any(type(s['value']) is not str for s in slots):
            raise ValueError('Original native parameter slots required')
        cursor.execute("SELECT pg_catalog.current_setting('search_path')", prepare=False)
        original_path = cursor.fetchone()[0]
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog,pg_temp',true)", prepare=False)
        # Fixed context handler and source functions independently recheck all owners.
        cursor.execute('SELECT truss.query_scope(%s::pg_catalog.jsonb)', (binding_json,), prepare=False)
        for slot in slots:
            logical_type=slot['logicalType']
            if logical_type == {'kind':'exactScalar','scalarType':'binary'}:
                token=slot['value']
                if len(token)>1048576 or base64.b64encode(base64.b64decode(token,validate=True)).decode('ascii')!=token:
                    raise ValueError('Canonical binary parameter slot required')
                continue
            if logical_type == {'kind':'exactScalar','scalarType':'date'}:
                _date_token(slot['value'])
                continue
            if logical_type == {'kind':'exactScalar','scalarType':'timestamp'}:
                cursor.execute('SELECT truss.query_timestamp_instant_key(%s,%s)',(slot['value'],'umf-rfc3339-exact-instant/1.0.0'),prepare=False)
                cursor.fetchone()
                continue
            if type(logical_type) is not dict or set(logical_type)!={'family','facets','nullable'}:
                raise ValueError('Closed atomic or exact binary parameter type required')
            family=logical_type['family']
            if family in ('integer','decimal'):
                cursor.execute('SELECT truss.query_numeric_value(%s,%s)',(slot['value'],family),prepare=False)
                if cursor.fetchone()!=(True,):
                    cursor.execute('SELECT truss.query_scope(%s::pg_catalog.jsonb)',(binding_json,),prepare=False)
                    cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
                    if cursor.fetchone()!=(original_path,):raise ValueError('Caller path restoration required')
                    return QueryRefused(code='native_domain')
        # The following READ COMMITTED query can include newer commits. This is
        # a captured lower bound, never its exact snapshot or a receipt token.
        cursor.execute('SELECT pg_catalog.pg_snapshot_xmin(pg_catalog.pg_current_snapshot())::pg_catalog.text,pg_catalog.to_char(pg_catalog.clock_timestamp() AT TIME ZONE \'UTC\',\'YYYY-MM-DD"T"HH24:MI:SS.US"Z"\'),pg_catalog.pg_current_xact_id_if_assigned()::pg_catalog.text',prepare=False)
        lower_bound, captured_at, caller_xid = cursor.fetchone()
        if type(lower_bound) is not str or not re.fullmatch(r'[1-9][0-9]{0,19}',lower_bound) or int(lower_bound)>18446744073709551615 or type(captured_at) is not str or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z',captured_at) or caller_xid is not None and (type(caller_xid) is not str or not re.fullmatch(r'[1-9][0-9]{0,19}',caller_xid) or int(caller_xid)>18446744073709551615):
            raise ValueError('Exact native read-bound observation required')
        captured_at = datetime.fromisoformat(captured_at).astimezone(timezone.utc)
        position_data = {'profile':'truss-query-read-position/0.1','installationId':binding['installationId'],
            'releaseSha256':binding['releaseSha256'],'catalogRevision':binding['catalogRevision'],
            'actorOid':bundle['actorOid'],'documents':binding['documents'],'completedBeforeXid':lower_bound,
            'at':captured_at.isoformat(timespec='microseconds'),'callerXidAssigned':caller_xid is not None}
        position_bytes=json.dumps(position_data,ensure_ascii=False,separators=(',',':')).encode('utf8')
        if len(position_bytes)>65536:
            cursor.execute('SELECT truss.query_scope(%s::pg_catalog.jsonb)',(binding_json,),prepare=False)
            cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
            if cursor.fetchone()!=(original_path,):raise ValueError('Caller path restoration required')
            return QueryRefused(code='limits')
        position=QueryReadPosition(value='truss-read-position-v1:'+base64.urlsafe_b64encode(position_bytes).decode('ascii').rstrip('='),at=captured_at,caller_xid_assigned=caller_xid is not None)
        from psycopg import RawCursor
        from psycopg.rows import tuple_row
        from .psycopg_host import _GuardedCursor
        with RawCursor(cursor.connection,row_factory=tuple_row) as original_raw:
            raw=_GuardedCursor(original_raw,cursor._deadline)
            pin_cursor(raw)
            raw.execute(artifact['sql'], tuple(s['value'] for s in slots), prepare=False)
            if raw.description is None or [(c.name, c.type_code) for c in raw.description] != [(c['outputName'], 25) for c in artifact['columns']]:
                raise ValueError('Original result column labels and text carriers required')
            result = _decode_rows(raw.fetchmany(maximum_rows + 1), artifact, maximum_rows, maximum_bytes)
        cursor.execute('SELECT truss.query_scope(%s::pg_catalog.jsonb)', (binding_json,), prepare=False)
        cursor.execute('SELECT oid::text FROM pg_roles WHERE rolname=session_user', prepare=False)
        if cursor.fetchone() != (bundle['actorOid'],):
            raise ValueError('Original query actor required')
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)", (original_path,), prepare=False)
        if cursor.fetchone() != (original_path,):
            raise ValueError('Caller search path restoration required')
        if isinstance(result, QueryRows) and page_metadata is not None:
            visible = page_metadata['visibleOutputs']
            keys = page_metadata['keyOutputs']
            if type(visible) is not int or visible < 1 or type(keys) is not list or not keys or keys != list(range(visible,len(result.columns))) or page_metadata['pageSize'] != page_size or len(result.rows)>page_size+1:
                raise ValueError('Exact owner page output positions and lookahead required')
            key_types = _relationship_key_types(artifact['logicalPlan']['pageKey']['types'],maximum=1024)
            if len(keys)!=len(key_types):raise ValueError('Complete authored continuation key required')
            try:
                lexical_keys=[[_page_key_token(row[index],t) for index,t in zip(keys,key_types,strict=True)] for row in result.rows]
            except (ValueError,UnicodeError):return QueryRefused(code='limits')
            retained = result.rows[:page_size]
            next_cursor = None
            if len(result.rows)>page_size:
                token = json.dumps({'profile':'truss-query-page/0.2','context':context,'after':lexical_keys[len(retained)-1]},ensure_ascii=False,separators=(',',':')).encode('utf8')
                if len(token)>65536:return QueryRefused(code='limits')
                next_cursor = QueryPageCursor(original_bytes=token)
            return QueryPage(columns=result.columns[:visible],rows=tuple(row[:visible] for row in retained),catalog_revision=binding['catalogRevision'],next_cursor=next_cursor,as_of=position,next_sort_values=None if next_cursor is None else tuple(retained[-1][index] for index in keys))
        if isinstance(result, QueryRows):
            return QueryRows(columns=result.columns, rows=result.rows, catalog_revision=binding['catalogRevision'],as_of=position)
        return result
    result = host._run_operation(transaction, execute)
    if isinstance(result, Error) and result.error.code=='execution_obligation':
        state = result.error.sql_state
        if state == '42501':
            return Ok(QueryRefused(code='unauthorized'))
        if state=='22003':return Ok(QueryRefused(code='native_domain'))
        if state in ('0A000', '54000', '55P03'):
            return Ok(QueryRefused(code={'0A000': 'unsupported_query', '54000': 'limits', '55P03': 'stale_context'}[state]))
    return result
