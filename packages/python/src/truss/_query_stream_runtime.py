# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original Truss portal execution; compiler owns SQL, native scope owns admission."""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from uuid import uuid4
from time import monotonic
from weakref import WeakKeyDictionary
from .execution import Ok,Error
from .query import QueryRows, QueryRefused
from .query_stream import QueryStreamHandle, QueryStreamRefused, QueryStreamBatch, QueryStreamTimedOut
from ._query_runtime import _decode_rows, _relationship_key_types, _page_key_token

@dataclass
class _State:
    assembly: object
    transaction: object
    name: str
    program: str
    request: dict
    export: dict
    actor: str
    active: bool = True
    pending: tuple = ()

_streams = WeakKeyDictionary()

def _value(outcome,deadline=None):
    if isinstance(outcome,Error) and outcome.error.code=="cancelled" and deadline is not None and monotonic()>=deadline:
        raise QueryStreamTimedOut(outcome)
    if not isinstance(outcome, Ok) or isinstance(outcome.value, QueryRefused):
        raise QueryStreamRefused(outcome)
    return outcome.value

def _current(cursor, state, pin_cursor):
    """One guarded native call retains complete original request correspondence."""
    pin_cursor(cursor)
    request=state.request
    binding=json.loads(request['target']['bindingJson'])
    documents=tuple(dict.fromkeys(module['pin']['documentId'] for module in request['modules']))
    cursor.execute('SELECT truss.person_query_binding(%s::pg_catalog.jsonb,%s,%s,%s,%s,%s)',
        (json.dumps(documents),binding['maximumScanRows'],binding['maximumResultRows'],binding['maximumBytes'],binding['releaseId'],binding['releaseSha256']),prepare=False)
    bundle=json.loads(bytes(cursor.fetchone()[0]))
    binding_json=bundle['bindingJson']
    if json.loads(binding_json) != bundle['binding']:
        raise ValueError('Complete original native binding correspondence required')
    current=dict(request,modules=bundle['modules'],target=dict(request['target'],bindingJson=binding_json,bindingSha256=sha256(binding_json.encode()).hexdigest()))
    if current != request or state.actor and state.actor != bundle['actorOid']:
        raise QueryStreamRefused(QueryRefused('stale_context'))
    state.actor=bundle['actorOid']
    import weft
    export=json.loads(weft.compile_engine_export_json(state.program,json.dumps(current,ensure_ascii=False)))
    if export.get('status') != 'compiled' or export.get('compiler') != 'truss-runtime-cursor':
        raise QueryStreamRefused(export)
    return export

def _admit(cursor, state, pin_cursor):
    pin_cursor(cursor)
    cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog,pg_temp',true)",prepare=False)
    cursor.fetchone()
    cursor.execute('SELECT truss.person_query_scope(%s::pg_catalog.jsonb)',(state.request['target']['bindingJson'],),prepare=False)
    cursor.execute('SELECT oid::pg_catalog.text FROM pg_catalog.pg_roles WHERE rolname=session_user',prepare=False)
    if cursor.fetchone() != (state.actor,):
        raise ValueError('Original stream actor changed')

def open_stream(assembly, transaction, *, engine_program, parameters, operation_deadline, pin_cursor):
    import weft
    if not callable(getattr(weft,'compile_engine_export_json',None)):
        raise ValueError('Explicit original cursor compiler unavailable')
    if type(engine_program) is not str or len(engine_program.encode()) > 4194304 or type(parameters) is not dict or len(parameters)>1024:
        raise ValueError('Bounded complete stream originals required')
    original=json.loads(engine_program)
    request=original['request']
    values={}
    for name,value in parameters.items():
        if type(value) is str:family,token='string',value
        elif type(value) is bool:family,token='boolean','true' if value else 'false'
        elif type(value) is int:family,token='integer',str(Decimal(value))
        elif type(value) is Decimal and value.is_finite():
            parts=value.as_tuple();exponent=parts.exponent;digits=len(parts.digits)
            size=(digits+exponent if exponent>=0 else digits+1 if digits+exponent>0 else 2-exponent)+parts.sign
            if size>1048576:raise ValueError('Bounded exact decimal parameter required')
            family,token='decimal',format(value,'f')
        else:raise ValueError('Exact non-temporal scalar stream parameter required')
        if type(name) is not str or len(token.encode())>1048576 or '\0' in token:raise ValueError('Bounded original scalar parameter required')
        values[name]={'family':family,'value':token}
    request=dict(request,parameters=values)
    export=json.loads(weft.compile_engine_export_json(engine_program,json.dumps(request,ensure_ascii=False)))
    if export.get('status') != 'compiled':raise QueryStreamRefused(export)
    artifact=export['artifact']
    if (artifact['backend'] != {'backendId':'truss.postgresql.runtime','backendVersion':'0.4.44','targetProfile':'truss-runtime-pg18.6-export/0.2','interfaceVersion':'weft-backend/0.2.9'}
        or artifact['bindingSha256'] != sha256(request['target']['bindingJson'].encode()).hexdigest()
        or artifact['logicalPlan']['limit'] is not None
        or [o['id'] for o in artifact['obligations']] != ['truss.runtime.context/0.1','truss.runtime.cursor-export/0.1']
        or any(o['owner'] != 'host' for o in artifact['obligations'])):
        raise ValueError('Closed original cursor profile and installed obligations required')
    if any(s.assembly is assembly and s.transaction is transaction and s.active for s in _streams.values()):
        raise ValueError('Only one original stream may own the transaction')
    state=_State(assembly,transaction,'truss_export_'+uuid4().hex,engine_program,request,export,'')
    def execute(cursor, observed):
        pin_cursor(cursor)
        if _current(cursor,state,pin_cursor) != export:raise QueryStreamRefused(QueryRefused('stale_context'))
        _admit(cursor,state,pin_cursor)
        slots=artifact['parameters']
        if [slot['position'] for slot in slots]!=list(range(1,len(slots)+1)):
            raise ValueError('Original ordered parameter slots required')
        for slot in slots:
            family=slot['logicalType'].get('family')
            if family not in ('string','boolean','integer','decimal') or type(slot['value']) is not str:
                raise ValueError('Original non-temporal scalar slot required')
            if family in ('integer','decimal'):
                cursor.execute('SELECT truss.query_numeric_value(%s,%s)',(slot['value'],family),prepare=False)
                if cursor.fetchone()!=(True,):raise QueryStreamRefused(QueryRefused('native_domain'))
        from psycopg import RawCursor, sql
        from psycopg.rows import tuple_row
        from .psycopg_host import _GuardedCursor
        with RawCursor(cursor.connection,row_factory=tuple_row) as original:
            raw=_GuardedCursor(original,cursor._deadline);pin_cursor(raw)
            raw.execute(sql.SQL('DECLARE {} NO SCROLL INSENSITIVE CURSOR WITHOUT HOLD FOR ').format(sql.Identifier(state.name))+sql.SQL(artifact['sql']),tuple(s['value'] for s in artifact['parameters']),prepare=False)
        _admit(cursor,state,pin_cursor)
        if _current(cursor,state,pin_cursor) != export:raise QueryStreamRefused(QueryRefused('stale_context'))
        return True
    _value(assembly._host._run_operation(transaction,execute,operation_deadline=operation_deadline),operation_deadline)
    handle=QueryStreamHandle();_streams[handle]=state
    return handle

def _state(assembly,transaction,handle):
    state=_streams.get(handle) if type(handle) is QueryStreamHandle else None
    if state is None or state.assembly is not assembly or state.transaction is not transaction or not state.active:
        raise ValueError('Original live stream custody required')
    return state

def fetch_stream(assembly,transaction,handle,*,count,validate,operation_deadline,final_bound,pin_cursor):
    state=_state(assembly,transaction,handle)
    if type(count) is not int or not 1 <= count <= state.export['cursor']['batchSize'] or not callable(validate) or type(final_bound) is not bool:
        raise ValueError('Original bounded fetch and typed validator required')
    try:
        def execute(cursor,observed):
            if _current(cursor,state,pin_cursor) != state.export:raise QueryStreamRefused(QueryRefused('stale_context'))
            _admit(cursor,state,pin_cursor)
            from psycopg import sql
            native_count=count+(0 if final_bound else 1)-len(state.pending)
            artifact=state.export['artifact']
            raw_rows=()
            if native_count:
                cursor.execute(sql.SQL('FETCH FORWARD {} FROM {}').format(sql.Literal(native_count),sql.Identifier(state.name)),prepare=False)
                if cursor.description is None or [(c.name,c.type_code) for c in cursor.description] != [(c['outputName'],25) for c in artifact['columns']]:
                    raise ValueError('Complete native cursor text signature required')
                raw_rows=tuple(cursor.fetchmany(native_count+1))
            # A retained lookahead is the original text row, so its bytes and
            # codecs count again in the complete next-page validation. FETCH0
            # is deliberately absent: PostgreSQL would return its current row.
            combined_raw=state.pending+raw_rows
            result=_decode_rows(combined_raw,artifact,count+(0 if final_bound else 1),json.loads(state.request['target']['bindingJson'])['maximumBytes'])
            if not isinstance(result,QueryRows):raise QueryStreamRefused(result)
            combined=result.rows
            exhausted=len(combined)<count+(0 if final_bound else 1)
            retained=combined[:count]
            pending=combined_raw[count:]
            if len(pending)>1:raise ValueError('Only one original lookahead row may be retained')
            metadata=state.export['cursor'];visible=metadata['visibleOutputs'];keys=metadata['keyOutputs']
            if keys != list(range(visible,len(result.columns))) or not keys:
                raise ValueError('Original complete hidden Key signature required')
            types=_relationship_key_types(artifact['logicalPlan']['pageKey']['types'],maximum=1024)
            for row in combined:
                for index,t in zip(keys,types,strict=True):_page_key_token(row[index],t)
            _admit(cursor,state,pin_cursor)
            if _current(cursor,state,pin_cursor) != state.export:raise QueryStreamRefused(QueryRefused('stale_context'))
            rows=QueryRows(columns=result.columns[:visible],rows=tuple(row[:visible] for row in retained),catalog_revision=json.loads(state.request['target']['bindingJson'])['catalogRevision'],column_descriptors=result.column_descriptors[:visible])
            validated=tuple(validate(rows))
            if len(validated)!=len(retained):raise ValueError('DTO validation must preserve native row count')
            _admit(cursor,state,pin_cursor)
            if _current(cursor,state,pin_cursor) != state.export:raise QueryStreamRefused(QueryRefused('stale_context'))
            state.pending=pending
            return QueryStreamBatch(validated,exhausted)
        result=_value(assembly._host._run_operation(transaction,execute,operation_deadline=operation_deadline),operation_deadline)
        return result
    except BaseException:
        # The cursor position is not rewound by host savepoint rollback. Its
        # transaction must be terminal; the explicit lease owns outer cleanup.
        state.active=False
        raise

def close_stream(assembly,transaction,handle,*,pin_cursor):
    state=_streams.get(handle) if type(handle) is QueryStreamHandle else None
    if state is None or state.assembly is not assembly or state.transaction is not transaction:
        raise ValueError('Original stream cleanup custody required')
    try:
        def execute(cursor,observed):
            from psycopg import sql
            pin_cursor(cursor)
            cursor.execute(sql.SQL('CLOSE {}').format(sql.Identifier(state.name)),prepare=False)
            return True
        _value(assembly._host._run_operation(transaction,execute))
    finally:
        state.active=False
        _streams.pop(handle,None)
