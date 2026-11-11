# SPDX-License-Identifier: MIT OR Apache-2.0
"""Held temporal reads: owner recompilation, actual capture, guarded SQL, recheck.

The compiler enrollment is intentionally absent until its real reviewed bytes
are available. No ordinary compiler or native ABI is a fallback for this route.
"""
from collections.abc import Mapping
from hashlib import sha256
import json

from .execution import Error,Ok
from .query import QueryAbsent,QueryPage,QueryPageCursor,QueryRows,QueryRefused,QueryUnavailable
from .contracts import LocalTimestampValue,TextValue
from ._query_runtime import _immutable_metadata
from ._owner_evidence_json import decode_owner_evidence_json
from ._temporal_compiler import compiler
from ._temporal_profiles import abi
from ._temporal_query_runtime import BACKEND,_parameters
from ._temporal_query_values import decode_rows


def selected(original):
    if type(original) is not str:return False
    try:
        if len(original.encode())>4194304:return False
        value=decode_owner_evidence_json(original.encode())
        return isinstance(value,dict) and value.get('version') in (
            'umf.engine-catalog/0.4','weft.engine-read/0.4','weft.engine-page/0.4')
    except (ValueError,UnicodeError):return False


def _original(original,*,page=False):
    wrapper=decode_owner_evidence_json(original.encode())
    if (set(wrapper)!={'version','programJson','parameters','outputs','stageOne','catalogDigest'}
            or wrapper['version']!='umf.engine-catalog/0.4' or type(wrapper['programJson']) is not str
            or len(wrapper['programJson'].encode())>4194304):
        raise ValueError('Whole original engine0.4 wrapper required')
    from umf_access.native_program import canonical_json
    content={k:v for k,v in wrapper.items() if k!='catalogDigest'}
    if wrapper['catalogDigest']!=sha256(canonical_json(content).encode()).hexdigest():
        raise ValueError('Original wrapper digest required')
    program=decode_owner_evidence_json(wrapper['programJson'].encode())
    if program['compiler']!='truss-runtime-temporal' or program['version']!=('weft.engine-page/0.4' if page else 'weft.engine-read/0.4'):
        raise ValueError('Explicit original temporal engine selector required')
    if page and program['after'] is not None:raise ValueError('Original initial page required')
    return wrapper['programJson'],program


def _current_parameters(original,values):
    from umf_access.values import temporal_token
    ordinary=original['parameters'];temporal=original['temporalParameters']
    if not isinstance(values,Mapping) or set(values)!=set(ordinary)|set(temporal):
        raise ValueError('Complete original parameter map membership required')
    current_ordinary={name:values[name] for name in ordinary}
    current_temporal={name:{'kind':entry['kind'],'value':temporal_token(entry['kind'],values[name])}
                      for name,entry in temporal.items()}
    ordinary_values,temporal_values=_parameters(current_ordinary,current_temporal)
    if any(ordinary_values[name]['family']!=ordinary[name]['family'] for name in ordinary):
        raise ValueError('Original ordinary parameter kinds required')
    return {**original,'parameters':ordinary_values,'temporalParameters':temporal_values}


def _artifact(program,request,binding,*,page=False):
    artifact=program['artifact'];checks=artifact['sourceDomainChecks'];slots=artifact['parameters']
    expected_context={name:binding[name] for name in ('queryAbi','releaseId','releaseSha256','installationId','catalogRevision')}
    if (program['request']!=request or artifact['status']!='compiled'
            or artifact['interfaceVersion']!='weft-compile/0.2.10' or artifact['backend']!=BACKEND
            or artifact['modelPins']!=[m['pin'] for m in request['modules']]
            or artifact['bindingSha256']!=request['target']['bindingSha256']
            or artifact['targetContext']!=expected_context
            or set(checks)!={'version','mode','queryAbi','maxScanRows','maxBytes','sources'}
            or checks['version']!='weft.truss-temporal-domain-checks/0.2' or checks['mode']!='native-validated-source'
            or checks['queryAbi']!=abi() or checks['maxScanRows']!=binding['maximumScanRows']
            or checks['maxBytes']!=binding['maximumBytes'] or type(checks['sources']) is not list
            or len(checks['sources'])!=1 or type(slots) is not list or not 2<=len(slots)<=1024):
        raise ValueError('Whole current program/native source correspondence required')
    for index,slot in enumerate(slots,1):
        if (set(slot)!={'position','logicalType','value','origin'} or type(slot['position']) is not int
                or slot['position']!=index or type(slot['value']) is not str or '\0' in slot['value']
                or len(slot['value'].encode())>4194304):
            raise ValueError('Complete original native parameter slots required')
    source=checks['sources'][0]
    if (set(source)!={'record','bindingParameter','requirementsParameter','sourceFunction','selectedKey'}
            or source['sourceFunction']!=('truss.person_query_temporal_page_objects(jsonb,int,text,jsonb)' if page
                                        else 'truss.person_query_temporal_objects(jsonb,int,jsonb)')
            or source['selectedKey']!=(program['selectedKey'] if page else None)):
        raise ValueError('Exact installed temporal read source required')
    positions=(source['bindingParameter'],source['requirementsParameter'])
    if any(type(p) is not int or not 1<=p<=len(slots) for p in positions) or positions[0]==positions[1]:
        raise ValueError('Distinct original source argument slots required')
    if slots[positions[0]-1]['value']!=request['target']['bindingJson']:
        raise ValueError('Source must consume exact actual native binding string')
    requirements=decode_owner_evidence_json(slots[positions[1]-1]['value'].encode())
    if (set(requirements)!={'version','record','fields'} or requirements['version']!='truss.temporal-source-guard/0.2'
            or requirements['record']!=source['record']):
        raise ValueError('Original complete owner requirements required')
    if artifact['obligations']!=[{'id':'truss.runtime.temporal-source/0.2','owner':'host','failureCode':'WFT-OBLIGATION',
            'parameters':{'source':'complete-buffered-statement-snapshot','authority':'fresh-capture-and-final-recheck',
                          'maximumResultRows':binding['maximumResultRows']}}]:
        raise ValueError('Exact installed temporal source obligation required')
    if type(artifact['sql']) is not str or not 1<=len(artifact['sql'].encode())<=1048576:
        raise ValueError('Bounded whole owner SQL required')
    return artifact


def _page_metadata(program):
    """Compare closed owner metadata; never resolve a Key or parse ordering."""
    metadata=program['page'];outputs=program['outputs']
    if (type(metadata) is not dict or set(metadata)!={'version','selectedKey','visibleOutputPositions','keyOutputPositions','sort'}
            or metadata['version']!='weft.engine-temporal-page/0.2' or metadata['selectedKey']!=program['selectedKey']):
        raise ValueError('Complete original temporal page metadata required')
    for name in ('visibleOutputPositions','keyOutputPositions'):
        values=metadata[name]
        if (type(values) is not list or not values
                or any(type(p) is not int or not 1<=p<=len(outputs) for p in values)
                or len(set(values))!=len(values)):
            raise ValueError('Exact unique original output positions required')
    if type(metadata['sort']) is not list or not metadata['sort']:raise ValueError('Complete ordering required')
    used=set(metadata['visibleOutputPositions']+metadata['keyOutputPositions'])
    for slot in metadata['sort']:
        if (type(slot) is not dict or set(slot)!={'field','direction','nulls','kind','outputPosition'}
                or slot['direction'] not in ('asc','desc') or slot['nulls'] not in ('first','last')
                or slot['kind'] not in ('string','date','instant','local')
                or type(slot['outputPosition']) is not int or not 1<=slot['outputPosition']<=len(outputs)):
            raise ValueError('Closed original temporal sort slot required')
        output=outputs[slot['outputPosition']-1]
        if slot['field']!=output['source'] or slot['kind']!=output['carrier']:
            raise ValueError('Original ordering source and carrier required')
        used.add(slot['outputPosition'])
    for position in metadata['keyOutputPositions']:
        output=outputs[position-1]
        if output['carrier']!='string' or output['nullable'] is not False or output['missing'] is not False:
            raise ValueError('Complete required string Key inventory required')
    if used!=set(range(1,len(outputs)+1)):raise ValueError('Unaccounted hidden output')
    return metadata


def _after(program,original,*,expected_values=None):
    """Native-decoded packet framing and tuple custody; owner checks semantics."""
    value=decode_owner_evidence_json(original.encode());metadata=_page_metadata(program)
    if (type(value) is not dict or set(value)!={'version','selectedKey','sortValues','keyValues'}
            or value['version']!='weft.engine-temporal-after/0.2' or value['selectedKey']!=metadata['selectedKey']
            or type(value['sortValues']) is not list or len(value['sortValues'])!=len(metadata['sort'])
            or type(value['keyValues']) is not list or len(value['keyValues'])!=len(metadata['keyOutputPositions'])
            or any(type(k) is not str for k in value['keyValues'])):
        raise ValueError('Whole native continuation tuple required')
    for state,slot in zip(value['sortValues'],metadata['sort'],strict=True):
        if (type(state) is not dict or not (state=={'state':'missing'} or state=={'state':'null'}
                or set(state)=={'state','value'} and state['state']=='present' and type(state['value']) is str)):
            raise ValueError('Closed original continuation state required')
        output=program['outputs'][slot['outputPosition']-1]
        if state['state']=='missing' and not output['missing'] or state['state']=='null' and not output['nullable']:
            raise ValueError('Original output presence required')
    for position,key in zip(metadata['keyOutputPositions'],value['keyValues'],strict=True):
        corresponding=[state for state,slot in zip(value['sortValues'],metadata['sort'],strict=True)
                       if slot['outputPosition']==position]
        if not corresponding or any(state!={'state':'present','value':key} for state in corresponding):
            raise ValueError('Complete Key and full sort tuple must agree')
    if expected_values is not None and (type(expected_values) is not tuple or tuple(value['sortValues'])!=expected_values):
        raise ValueError('Opaque native token and supplied whole tuple differ')
    return value


def _row_after(program,row):
    metadata=_page_metadata(program)
    if len(row)!=len(program['outputs']):raise ValueError('Whole hidden native row required')
    states=[]
    for slot in metadata['sort']:
        value=row[slot['outputPosition']-1]
        if type(value) is QueryAbsent:state={'state':'missing'}
        elif value is None:state={'state':'null'}
        else:
            if slot['kind']=='string':
                if type(value) is not str:raise ValueError('Exact string continuation required')
                token=value
            elif slot['kind']=='local':
                if type(value) is not LocalTimestampValue:raise ValueError('Selected local continuation required')
                token=value.text
            else:
                if type(value) is not TextValue or value.kind!=('date' if slot['kind']=='date' else 'timestamp'):
                    raise ValueError('Selected guarded temporal continuation required')
                token=value.text
            state={'state':'present','value':token}
        states.append(state)
    keys=[row[p-1] for p in metadata['keyOutputPositions']]
    if any(type(v) is not str for v in keys):raise ValueError('Required complete string Key values required')
    return {'version':'weft.engine-temporal-after/0.2','selectedKey':metadata['selectedKey'],'sortValues':states,'keyValues':keys}


def _run(host,transaction,*,engine_program,sql,document_ids,parameters,maximum_rows,
         maximum_scan_rows,maximum_bytes,manifest,digest,pin_cursor,operation_deadline=None,
         page_size=None,page_cursor=None):
    page=page_size is not None
    try:
        from ._temporal_program_custody import check_shape,check_current,TemporalProgramRefused,TemporalProgramUnavailable
    except ImportError:
        return Ok(QueryUnavailable(reason='compiler'))
    try:
        original,program=_original(engine_program,page=page);request=program['request']
        if sql!=request['sql'] or document_ids!=tuple(m['pin']['documentId'] for m in request['modules']):
            raise ValueError('Original read/source arguments required')
        binding=decode_owner_evidence_json(request['target']['bindingJson'].encode())
        if (any(type(v) is not int for v in (maximum_rows,maximum_scan_rows,maximum_bytes))
                or (maximum_rows,maximum_scan_rows,maximum_bytes)!=(binding['maximumResultRows'],binding['maximumScanRows'],binding['maximumBytes'])
                or binding['releaseId']!=manifest['releaseId'] or binding['releaseSha256']!=digest
                or binding['queryAbi']!=abi() or manifest['releaseId']!='truss-catalog-runtime/0.76-candidate'):
            raise ValueError('Actual original native release/ABI/caps required')
        owner=compiler()
        if owner is None:return Ok(QueryUnavailable(reason='compiler'))
        shape=check_shape(owner,original,json.dumps(request,ensure_ascii=False,separators=(',',':')),page=page)
        if shape!=program:raise ValueError('Whole original shape-check result required')
        current=_current_parameters(request,parameters)
        current_json=json.dumps(current,ensure_ascii=False,separators=(',',':'))
        if page:
            _page_metadata(program)
            if type(page_size) is not int or not 1<=page_size<=999 or page_size!=program['pageSize']:
                raise ValueError('Original temporal page size required')
            if page_cursor is not None and (type(page_cursor) is not QueryPageCursor
                    or type(page_cursor.original_bytes) is not bytes or not 1<=len(page_cursor.original_bytes)<=65536
                    or type(page_cursor.sort_values) is not tuple):
                raise ValueError('Original opaque token and complete tuple required')
        # All noncursor arguments plus whole original wrapper are native-bound.
        # Opaque bytes are interpreted only by the native person-bound decoder.
        context=json.dumps({'originalSha256':sha256(engine_program.encode()).hexdigest(),
                            'currentRequest':current_json},ensure_ascii=False,separators=(',',':')).encode()
    except TemporalProgramRefused as error:
        # Private SDK dispatch retains the actual refusal object, including
        # .parsed diagnostics and .original raw response. No public query DTO
        # is widened or used to discard original owner diagnostic members.
        return Ok(error)
    except TemporalProgramUnavailable:
        return Ok(QueryUnavailable(reason='compiler'))
    except (ValueError,TypeError,KeyError,UnicodeError):
        return Ok(QueryRefused(code='invalid_query'))
    except ImportError:
        return Ok(QueryUnavailable(reason='compiler'))
    command='SELECT truss.person_query_temporal_binding(%s::pg_catalog.jsonb,%s,%s,%s,%s,%s)'
    args=(json.dumps(document_ids),maximum_scan_rows,maximum_rows,maximum_bytes,manifest['releaseId'],digest)
    def capture(cursor):
        cursor.execute(command,args,prepare=False)
        value=decode_owner_evidence_json(bytes(cursor.fetchone()[0]))
        if (value['bindingJson']!=request['target']['bindingJson'] or value['binding']!=binding
                or value['modules']!=request['modules']):
            return None
        return value
    def execute(cursor,observed):
        pin_cursor(cursor)
        initial=capture(cursor)
        if initial is None:return QueryRefused(code='stale_context')
        after_json='null'
        if page and page_cursor is not None:
            cursor.execute('SELECT truss.person_query_temporal_cursor_decode(%s::jsonb,%s,%s)',
                           (request['target']['bindingJson'],context,page_cursor.original_bytes),prepare=False)
            after_json=cursor.fetchone()[0]
            if type(after_json) is not str:raise ValueError('Native decoded continuation JSON required')
            _after(program,after_json,expected_values=page_cursor.sort_values)
        try:
            checked=check_current(owner,original,current_json,page=page,after_json=after_json)
        except TemporalProgramRefused as error:return error
        except TemporalProgramUnavailable:return QueryUnavailable(reason='compiler')
        artifact=_artifact(checked,current,binding,page=page)
        if page and (checked['page']!=program['page'] or checked['pageSize']!=page_size
                     or checked['after']!=decode_owner_evidence_json(after_json.encode())):
            raise ValueError('Original page metadata and native tuple required')
        from psycopg import RawCursor
        from psycopg.rows import tuple_row
        from .psycopg_host import _GuardedCursor
        cursor.execute("SELECT pg_catalog.current_setting('search_path'),pg_catalog.set_config('search_path','pg_catalog,pg_temp',true)",prepare=False)
        prior,pinned=cursor.fetchone()
        if pinned!='pg_catalog,pg_temp':raise ValueError('Fixed native query path required')
        try:
            with RawCursor(cursor.connection,row_factory=tuple_row) as raw:
                guarded=_GuardedCursor(raw,cursor._deadline);pin_cursor(guarded)
                guarded.execute(artifact['sql'],tuple(slot['value'] for slot in artifact['parameters']),prepare=False)
                rows=[];charged=0
                while len(rows)<=maximum_rows:
                    following=guarded.fetchmany(1)
                    if not following:break
                    row=following[0]
                    if any(type(value) is not str for value in row):raise ValueError('Exact native text row required')
                    charged+=sum(len(value.encode()) for value in row)
                    if charged>maximum_bytes:return QueryRefused(code='limits')
                    rows.append(row)
            result=decode_rows(rows,checked,maximum_rows=maximum_rows,maximum_bytes=maximum_bytes,
                               catalog_revision=binding['catalogRevision'])
            if not isinstance(result,QueryRows):return result
            if page:
                if len(result.rows)>page_size+1:raise ValueError('Owner page lookahead bound exceeded')
                retained=result.rows[:page_size];next_cursor=None;next_values=None
                if len(result.rows)>page_size:
                    after_value=_row_after(checked,retained[-1])
                    cursor.execute('SELECT cursor_bytes,after_json FROM truss.person_query_temporal_cursor_encode(%s::jsonb,%s,%s,%s::jsonb)',
                        (request['target']['bindingJson'],context,json.dumps(after_value,ensure_ascii=False,separators=(',',':')),
                         json.dumps([s['kind'] for s in checked['page']['sort']])),prepare=False)
                    opaque,canonical=cursor.fetchone();opaque=bytes(opaque)
                    if type(canonical) is not str or not 1<=len(opaque)<=65536:
                        raise ValueError('Bounded original native cursor issuance required')
                    continuation=_after(checked,canonical)
                    # The same owner checker validates native canonical tokens
                    # and full tuple before any cursor or row is published.
                    try:next_checked=check_current(owner,original,current_json,page=True,after_json=canonical)
                    except TemporalProgramRefused as error:return error
                    except TemporalProgramUnavailable:return QueryUnavailable(reason='compiler')
                    _artifact(next_checked,current,binding,page=True)
                    if (next_checked['page']!=program['page'] or next_checked['pageSize']!=page_size
                            or next_checked['after']!=continuation):
                        raise ValueError('Whole native issued continuation required')
                    next_values=tuple(_immutable_metadata(s) for s in continuation['sortValues'])
                    next_cursor=QueryPageCursor(original_bytes=opaque,sort_values=next_values)
                visible=checked['page']['visibleOutputPositions']
                result=QueryPage(columns=tuple(result.columns[p-1] for p in visible),
                    rows=tuple(tuple(row[p-1] for p in visible) for row in retained),catalog_revision=result.catalog_revision,
                    next_cursor=next_cursor,next_sort_values=next_values,column_descriptors=result.column_descriptors)
            # The actual business statement above already executes its complete
            # guarded source in one snapshot. This separate final bounded scan
            # releases NO rows: it checks current source/root authority after
            # buffering and is never a preflight substitute for that statement.
            source=artifact['sourceDomainChecks']['sources'][0]
            records=[r for r in binding['records'] if r['identity']==source['record']]
            if len(records)!=1:raise ValueError('Unique original native source mapping required')
            requirements=artifact['parameters'][source['requirementsParameter']-1]['value']
            if page:
                cursor.execute('SELECT pg_catalog.count(*) FROM truss.person_query_temporal_page_objects(%s::jsonb,%s,%s,%s::jsonb)',
                    (request['target']['bindingJson'],int(records[0]['typeId']),program['selectedKey']['key'],requirements),prepare=False)
            else:
                cursor.execute('SELECT pg_catalog.count(*) FROM truss.person_query_temporal_objects(%s::jsonb,%s,%s::jsonb)',
                    (request['target']['bindingJson'],int(records[0]['typeId']),requirements),prepare=False)
            cursor.fetchone()
            final=capture(cursor)
            if final is None or final!=initial:return QueryRefused(code='stale_context')
            return result
        finally:
            cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior,),prepare=False)
            if cursor.fetchone()!=(prior,):raise ValueError('Original caller path restoration required')
    result=host._run_operation(transaction,execute,operation_deadline=operation_deadline)
    if isinstance(result,Error) and result.error.code=='execution_obligation':
        code={'P1403':'unauthorized','0A000':'unsupported_query','54000':'limits','55P03':'stale_context',
              '22023':'native_domain','22003':'native_domain','P1002':'stale_context'}.get(result.error.sql_state)
        if code:return Ok(QueryRefused(code=code))
    return result


def run_read(host,transaction,**arguments):
    return _run(host,transaction,**arguments)


def run_page(host,transaction,*,page_size,page_cursor=None,**arguments):
    if page_size is None:return Ok(QueryRefused(code='invalid_query'))
    return _run(host,transaction,page_size=page_size,page_cursor=page_cursor,**arguments)
