"""Truss-owned catalog composition/execution; Weft owns all SQL interpretation."""
from decimal import Decimal
import re
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping
from .execution import Error, Ok, ExecutionFailure
from .query import QueryAbsent, QueryRelatedKeys, QueryRows, QueryDiagnostic, QueryRefused, QueryUnavailable

BACKEND = {'backendId': 'truss.postgresql.runtime', 'backendVersion': '0.4.3',
           'targetProfile': 'truss-runtime-pg18.6/0.4', 'interfaceVersion': 'weft-backend/0.2.0'}


def compiler():
    try:
        import weft
        if weft.__version__ != '0.1.0':
            return None
        return weft.compile_truss_runtime_json
    except (ImportError, AttributeError):
        return None


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
            elif representation['kind'] == 'relatedKeys':
                value=json.loads(raw);key=representation['key'];bound=representation['bound'];types=key['types']
                if type(bound) is not int or not 1<=bound<=1000 or not types or len(key['fields'])!=len(types) or any(t['family']!='string' or t['facets']!={} or t['nullable'] for t in types):
                    raise ValueError('Original string relationship key metadata required')
                if type(value) is not dict or set(value)!={'items','truncated'} or type(value['items']) is not list or type(value['truncated']) is not bool or len(value['items'])>bound or (value['truncated'] and len(value['items'])!=bound):
                    raise ValueError('Exact bounded relationship key result required')
                if any(type(item) is not list or len(item)!=len(types) or any(type(v) is not str for v in item) for item in value['items']):
                    raise ValueError('Exact relationship key tuple required')
                decoded.append(QueryRelatedKeys(items=tuple(tuple(item) for item in value['items']),truncated=value['truncated']))
            else:
                raise ValueError('Unknown compiled representation refused')
        rows.append(tuple(decoded))
    return QueryRows(columns=tuple(c['outputName'] for c in columns), rows=tuple(rows), catalog_revision=0)


def run_query(host, transaction, *, sql, document_ids, parameters, maximum_rows,
              maximum_scan_rows, maximum_bytes, manifest, digest, pin_cursor, read_profile):
    try:
        valid = type(sql) is str and 1 <= len(sql.encode('utf8')) <= 1048576 and '\0' not in sql
        valid = valid and type(document_ids) is tuple and 1 <= len(document_ids) <= 32 and len(set(document_ids)) == len(document_ids)
        valid = valid and all(type(d) is str and 1 <= len(d.encode('utf8')) <= 4096 and '\0' not in d for d in document_ids)
        valid = valid and isinstance(parameters, Mapping) and len(parameters) <= 1024
        valid = valid and all(type(k) is str and 1 <= len(k.encode('utf8')) <= 4096 and '\0' not in k and type(v) in (str, int, bool, Decimal) for k, v in parameters.items())
        valid = valid and all(type(v) is not str or len(v.encode('utf8')) <= 1048576 and '\0' not in v for v in parameters.values())
    except (UnicodeError, TypeError, ValueError):
        valid = False
    valid=valid and (read_profile is None or type(read_profile) is str and read_profile in ('entity-page','related-entity-page','count-summary'))
    if not valid:
        return Ok(QueryRefused(code='invalid_query'))
    if any(type(n) is not int for n in (maximum_rows, maximum_scan_rows, maximum_bytes)) or not 1 <= maximum_rows <= 10000 or not 1 <= maximum_scan_rows <= 10000 or not 1 <= maximum_bytes <= 16777216:
        return Ok(QueryRefused(code='limits'))
    compile_query = compiler()
    if compile_query is None:
        return Ok(QueryUnavailable(reason='compiler'))
    values={}
    for name,value in parameters.items():
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
        request = {'interfaceVersion': 'weft-compile/0.2.0', 'dialect': 'weft-sql/0.2.0', 'sql': sql,
                   'modules': bundle['modules'], 'parameters': values, 'options': {'allowCandidate': True},
                   'target': {'backendId': BACKEND['backendId'], 'backendVersion': BACKEND['backendVersion'],
                              'targetProfile': BACKEND['targetProfile'], 'bindingJson': binding_json, 'bindingSha256': binding_sha}}
        if read_profile is not None:request['readProfile']={'version':'weft-application-read/0.2.0','subset':read_profile}
        artifact = json.loads(compile_query(json.dumps(request, ensure_ascii=False)))
        if artifact['status'] != 'compiled':
            cursor.execute('SELECT truss.query_scope(%s::pg_catalog.jsonb)', (binding_json,), prepare=False)
            diagnostics = tuple(QueryDiagnostic(code=d['code'], message=d['message']) for d in artifact.get('diagnostics', ()))
            unsupported = any(d.code in ('WFT-CAPABILITY', 'WFT-TYPE', 'WFT-PROFILE') for d in diagnostics)
            return QueryRefused(code='unsupported_query' if unsupported else 'invalid_query', diagnostics=diagnostics)
        if artifact['backend'] != BACKEND or artifact['bindingSha256'] != binding_sha or artifact['modelPins'] != [m['pin'] for m in bundle['modules']]:
            raise ValueError('Original compiled binding/model/backend required')
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
            family=slot['logicalType']['family']
            if family in ('integer','decimal'):
                cursor.execute('SELECT truss.query_numeric_value(%s,%s)',(slot['value'],family),prepare=False)
                if cursor.fetchone()!=(True,):
                    cursor.execute('SELECT truss.query_scope(%s::pg_catalog.jsonb)',(binding_json,),prepare=False)
                    cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
                    if cursor.fetchone()!=(original_path,):raise ValueError('Caller path restoration required')
                    return QueryRefused(code='native_domain')
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
        if isinstance(result, QueryRows):
            return QueryRows(columns=result.columns, rows=result.rows, catalog_revision=binding['catalogRevision'])
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
