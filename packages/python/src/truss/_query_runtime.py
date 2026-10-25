# SPDX-License-Identifier: MIT OR Apache-2.0
"""Truss-owned catalog composition/execution; Weft owns all SQL interpretation."""
from decimal import Decimal
import re
import base64
from datetime import date, datetime, timezone
from hashlib import sha256
from importlib.resources import files
import json
from types import MappingProxyType
from typing import Mapping
from .execution import Error, Ok, ExecutionFailure
from .contracts import TextValue, LocalTimestampValue, validate_local_timestamp_text
from ._query_cache import compile_response, binding_hint, remember_binding
from .reader_catalog import ReaderCatalog, ReaderCatalogSnapshot, ReaderCatalogUnchanged
from .query import QueryDocument, QueryCatalogRead, QueryColumnDescriptor, QueryEntityProjection
from .query import QueryAbsent, QueryRelatedKeys, QueryRows, QueryDiagnostic, QueryRefused, QueryUnavailable, QueryPage, QueryPageCursor, QueryReadPosition, QueryCatalogSources

BACKEND = {'backendId': 'truss.postgresql.runtime', 'backendVersion': '0.4.43',
           'targetProfile': 'truss-runtime-pg18.6/0.6', 'interfaceVersion': 'weft-backend/0.2.9'}
TEMPORAL_BACKEND = {'backendId': 'truss.postgresql.runtime', 'backendVersion': '0.4.47',
                    'targetProfile': 'truss-runtime-pg18.6/0.7-temporal-candidate',
                    'interfaceVersion': 'weft-backend/0.2.10'}
TEMPORAL_QUERY_ABI_SHA256 = '479a0ba01bf21e61163a0709c1a3b4dbaeb9d5db1a03791d2044857ae2de588d'
TEMPORAL_ENGINE_PROFILE = 'umf.weft-binding-temporal/0.2'


def _checked_temporal_engine_program(engine_program):
    """Select only the explicit engine0.4/profile0.2 program shape."""
    if engine_program is None:
        return None
    try:
        program=json.loads(engine_program)
    except (TypeError,ValueError,UnicodeError):
        raise ValueError('Original engine program JSON required') from None
    if type(program) is not dict:
        raise ValueError('Original engine program object required')
    version=program.get('version')
    selected=version in ('weft.engine-read/0.4','weft.engine-page/0.4')
    marked=(program.get('compiler')=='truss-runtime-temporal'
            or program.get('temporalProfile')==TEMPORAL_ENGINE_PROFILE)
    if not selected:
        if marked:
            raise ValueError('Native temporal engine version/profile mismatch')
        return None
    request=program.get('request')
    if (program.get('status')!='compiled' or program.get('compiler')!='truss-runtime-temporal'
        or program.get('temporalProfile')!=TEMPORAL_ENGINE_PROFILE or type(request)is not dict
        or request.get('interfaceVersion')!='weft-compile/0.2.10'
        or request.get('temporalProfile')!=TEMPORAL_ENGINE_PROFILE
        or type(request.get('target')) is not dict
        or request['target'].get('backendVersion')!=TEMPORAL_BACKEND['backendVersion']
        or request['target'].get('targetProfile')!=TEMPORAL_BACKEND['targetProfile']
        or type(request.get('temporalParameters')) is not dict):
        raise ValueError('Closed original native temporal engine program required')
    return program


def _temporal_parameter_value(kind, value):
    """Canonicalize a value under its owner-selected kind, never tz-awareness inference."""
    if kind=='date':
        if type(value)is not date:
            raise ValueError('Selected date parameter requires Python date')
        token=value.isoformat()
        return _date_token(token)
    if kind=='local':
        if type(value)is LocalTimestampValue:
            validate_local_timestamp_text(value.text)
            return value.text
        if type(value)is not datetime or value.tzinfo is not None or value.fold!=0:
            raise ValueError('Selected local parameter requires naive local datetime')
        token=value.isoformat(timespec='microseconds')
        validate_local_timestamp_text(token)
        return token
    if kind=='instant':
        if type(value)is not datetime or value.tzinfo is None:
            raise ValueError('Selected instant parameter requires aware datetime')
        offset=value.utcoffset()
        if offset is None:
            raise ValueError('Selected instant parameter requires known offset')
        utc=value.astimezone(timezone.utc)
        delta=utc-datetime(1970,1,1,tzinfo=timezone.utc)
        micros=(delta.days*86400+delta.seconds)*1_000_000+delta.microseconds
        return str(micros)
    raise ValueError('Unknown selected temporal parameter kind')


def _bind_temporal_parameters(request, parameters, values, exact_values):
    """Move explicitly selected temporal model fields into Weft's third map."""
    selected=request.get('temporalParameters')
    if type(selected)is not dict:
        raise ValueError('Closed original temporal parameter map required')
    if not selected:
        return {}
    names=set(selected)
    if names & (set(request.get('parameters',{})) | set(request.get('exactParameters',{}))):
        raise ValueError('Original temporal parameter names collide with legacy maps')
    result={}
    for name,descriptor in selected.items():
        if (type(name)is not str or not name or type(descriptor)is not dict
            or set(descriptor)!={'kind','value'} or descriptor.get('kind') not in ('date','instant','local')
            or type(descriptor.get('value')) is not str or name not in parameters):
            raise ValueError('Closed original temporal parameter declaration required')
        value=parameters[name]
        result[name]={'kind':descriptor['kind'],'value':_temporal_parameter_value(descriptor['kind'],value)}
        values.pop(name,None)
        exact_values.pop(name,None)
    return result


def query_temporal_abi():
    """Return the packaged ABI 1.3 descriptor only when its immutable pin matches."""
    raw = files('truss').joinpath('_catalog_runtime/query-temporal-abi.json').read_bytes()
    if sha256(raw).hexdigest() != TEMPORAL_QUERY_ABI_SHA256:
        raise ValueError('Original temporal query ABI descriptor required')
    descriptor = json.loads(raw)
    if (type(descriptor) is not dict or descriptor.get('identity') != 'truss-postgresql-logical-query'
        or descriptor.get('version') != '1.3' or descriptor.get('bindingInterfaceVersion') != 'truss-runtime-binding/0.5'):
        raise ValueError('Closed temporal query ABI descriptor required')
    return descriptor


def compiler(*, engine_catalog=False, engine_pages=False, entity_projection=False, engine_temporal=False):
    try:
        import weft
        if engine_temporal:
            if (getattr(weft,'__version__',None)!='0.4.51'
                or not callable(getattr(weft,'compile_engine_read_json',None))
                or not callable(getattr(weft,'check_engine_temporal_read_shape_json',None))
                or not callable(getattr(weft,'check_engine_temporal_page_shape_json',None))
                or not callable(getattr(weft,'check_engine_temporal_read_json',None))
                or not callable(getattr(weft,'check_engine_temporal_page_json',None))):
                return None
            candidate=getattr(weft,'compile_engine_read_json',None)
            return candidate if callable(candidate) else None
        if weft.__version__ != '0.4.51' or not callable(getattr(weft,'compile_truss_runtime_json',None)):
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


def _temporal_cursor_envelope(row, slot):
    """Build one typed ordered-page cursor value from compiler-owned hidden slots."""
    value_index=slot.get('valueOutput');state_index=slot.get('stateOutput')
    if (type(value_index)is not int or type(state_index)is not int
        or value_index<0 or state_index<0 or value_index>=len(row) or state_index>=len(row)):
        raise ValueError('Exact hidden ordered-page output positions required')
    state=row[state_index]
    value=row[value_index]
    if state=='missing':
        if not isinstance(value, QueryAbsent):raise ValueError('Missing page state must have an absent value envelope')
        return {'state':'missing'}
    if state=='null':
        if value is not None:raise ValueError('Null page state must have a null value envelope')
        return {'state':'null'}
    if state!='present':raise ValueError('Closed ordered-page hidden state required')
    if value is None or isinstance(value, QueryAbsent):raise ValueError('Present page state must have a present value envelope')
    carrier=slot.get('carrier')
    temporal=slot.get('temporal')
    if temporal is not None:
        kind={'date':'date','instant':'instant','local':'local'}.get(temporal)
        if kind is None or carrier!={'date':'date','instant':'timestamp','local':'localTimestamp'}[kind]:
            raise ValueError('Exact selected temporal ordered-page carrier required')
        if kind=='date' and type(value)is TextValue and value.kind=='date':
            _date_token(value.text);cursor_value=value.text
        elif kind=='local' and type(value)is LocalTimestampValue:
            validate_local_timestamp_text(value.text);cursor_value=value.text
        elif kind=='instant' and type(value)is TextValue and value.kind=='timestamp':
            cursor_value=_canonical_epoch_micros(value.text)
        else:raise ValueError('Exact typed hidden temporal value required')
        return {'state':'temporal','kind':kind,'value':cursor_value}
    if carrier not in ('string','boolean','integer','decimal'):
        raise ValueError('Exact ordered-page scalar carrier required')
    if carrier=='string':token=value if type(value)is str else None
    elif carrier=='boolean':token='true' if value is True else 'false' if value is False else None
    elif carrier=='integer':token=str(value) if type(value)is int else None
    else:token=format(value,'f') if type(value)is Decimal and value.is_finite() else None
    if token is None:raise ValueError('Exact ordered-page scalar value required')
    if carrier=='boolean':
        if token not in ('true','false'):raise ValueError('Exact boolean cursor required')
    else:_decode_scalar(token,carrier)
    return {'state':'present','carrier':carrier,'value':token}


def _temporal_cursor_result_value(row,slot):
    value_index=slot.get('valueOutput');state_index=slot.get('stateOutput')
    if (type(value_index)is not int or type(state_index)is not int or value_index<0 or state_index<0
        or value_index>=len(row) or state_index>=len(row)):
        raise ValueError('Exact hidden ordered-page output positions required')
    state=row[state_index]
    value=row[value_index]
    if state=='missing':
        if not isinstance(value, QueryAbsent):raise ValueError('Missing page state must have an absent value envelope')
        return QueryAbsent()
    if state=='null':
        if value is not None:raise ValueError('Null page state must have a null value envelope')
        return None
    if state!='present':raise ValueError('Closed ordered-page hidden state required')
    if value is None or isinstance(value, QueryAbsent):raise ValueError('Present page state must have a present value envelope')
    return value


def _temporal_cursor_typed_value(value,slot):
    if isinstance(value,QueryAbsent):return {'state':'missing'}
    if value is None:return {'state':'null'}
    return _temporal_cursor_envelope((value,'present'),dict(slot,valueOutput=0,stateOutput=1))


def _temporal_page_result(result,page_metadata,page_size,context,catalog_revision,as_of):
    visible=page_metadata.get('visibleOutputs');slots=page_metadata.get('sortSlots');key_slots=page_metadata.get('keySlots')
    if (type(visible)is not int or not 1<=visible<=len(result.columns)
        or type(slots)is not list or not slots or type(key_slots)is not list or not key_slots
        or any(type(i)is not int or i<0 or i>=len(slots) for i in key_slots)
        or len(set(key_slots))!=len(key_slots) or page_metadata.get('version')!='weft.engine-cursor/0.4'
        or page_metadata.get('pageSize')!=page_size or len(result.rows)>page_size+1):
        raise ValueError('Exact native temporal page slots and lookahead required')
    cursor_rows=[]
    for row in result.rows:
        if len(row)!=len(result.columns):raise ValueError('Full hidden temporal page row required')
        sort_values=[_temporal_cursor_envelope(row,slot) for slot in slots]
        cursor_rows.append({'key':[sort_values[index] for index in key_slots],'sortValues':sort_values})
    retained=result.rows[:page_size];next_cursor=None;next_values=None
    if len(result.rows)>page_size:
        token=json.dumps({'profile':'truss-engine-page/0.4','context':context,
            'after':cursor_rows[len(retained)-1]},ensure_ascii=False,separators=(',',':')).encode('utf8')
        if len(token)>65536:raise ValueError('Bounded temporal page cursor required')
        next_cursor=QueryPageCursor(original_bytes=token)
        next_values=tuple(_temporal_cursor_result_value(retained[-1],slots[index]) for index in key_slots)
    return QueryPage(columns=result.columns[:visible],rows=tuple(row[:visible] for row in retained),
        catalog_revision=catalog_revision,next_cursor=next_cursor,as_of=as_of,
        next_sort_values=next_values,column_descriptors=result.column_descriptors[:visible])


def _validate_temporal_cursor_value(value):
    if type(value)is not dict or type(value.get('state'))is not str:
        return False
    state=value['state']
    if state in ('null','missing'):
        return set(value)=={'state'}
    if state=='temporal':
        if set(value)!={'state','kind','value'} or value.get('kind') not in ('date','instant','local') or type(value.get('value'))is not str:
            return False
        try:
            if value['kind']=='date':_date_token(value['value'])
            elif value['kind']=='local':validate_local_timestamp_text(value['value'])
            else:_validate_epoch_micros_cursor(value['value'])
        except (ValueError,TypeError,UnicodeError):return False
        return True
    if state=='present':
        if set(value)!={'state','carrier','value'} or value.get('carrier') not in ('string','boolean','integer','decimal'):
            return False
        if value['carrier']=='boolean':return type(value['value'])is str and value['value'] in ('true','false')
        try:_decode_scalar(value['value'],value['carrier'])
        except (ValueError,TypeError,UnicodeError):return False
        return True
    return False


def _validate_instant_cursor_text(value):
    if type(value)is not str or len(value)>128:
        raise ValueError('Bounded exact instant cursor required')
    match=re.fullmatch(r'([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]{1,128}))?(Z|[+-][0-9]{2}:[0-9]{2})',value)
    if match is None:raise ValueError('Known-offset exact instant cursor required')
    fraction=match.group(2) or ''
    if len(fraction)>6 and any(ch!='0' for ch in fraction[6:]):
        raise ValueError('Nonrepresentable exact instant cursor precision')
    offset=match.group(3)
    if offset!='Z' and (int(offset[1:3])>23 or int(offset[4:6])>59):
        raise ValueError('Valid exact instant offset required')
    token=value[:-1]+'+00:00' if value.endswith('Z') else value
    parsed=datetime.fromisoformat(token)
    if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.fold!=0:
        raise ValueError('Known-offset exact instant cursor required')
    from umf_access.values import temporal_token
    temporal_token('instant',parsed)
    return value


def _canonical_epoch_micros(value):
    _validate_instant_cursor_text(value)
    token=value[:-1]+'+00:00' if value.endswith('Z') else value
    instant=datetime.fromisoformat(token).astimezone(timezone.utc)
    delta=instant-datetime(1970,1,1,tzinfo=timezone.utc)
    return str((delta.days*86400+delta.seconds)*1_000_000+delta.microseconds)


def _validate_epoch_micros_cursor(value):
    if (type(value)is not str or not re.fullmatch(r'-?(0|[1-9][0-9]*)',value)
        or value=='-0' or len(value)>19):
        raise ValueError('Canonical epoch-microsecond instant cursor required')
    if not -62135596800000000<=int(value)<=253402300799999999:
        raise ValueError('Instant cursor outside supported Gregorian range')
    return value


def _descriptor_identity_key(identity):
    return json.dumps(identity, sort_keys=True, ensure_ascii=False, separators=(',',':'))


def _index_value_descriptors(descriptors):
    indexed = {}
    for descriptor in descriptors:
        key = _descriptor_identity_key(descriptor['identity'])
        if key in indexed:
            raise ValueError('Unique logical value descriptor identity required')
        indexed[key] = descriptor
    return indexed


def _artifact_type_graph(artifact):
    logical=artifact.get('logicalPlan') if type(artifact)is dict else None
    if type(logical)is not dict:raise ValueError('Original compiler type graph required')
    graph=logical.get('typeGraph')
    if graph is None and type(logical.get('base'))is dict:
        graph=logical['base'].get('typeGraph')
    if type(graph)is not list:raise ValueError('Original compiler type graph required')
    return graph


def _decode_value(value, descriptor_id, descriptors_by_identity):
    descriptor = descriptors_by_identity[_descriptor_identity_key(descriptor_id)]
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
        if kind == 'localTimestamp' and type(value) is str:
            validate_local_timestamp_text(value)
            return LocalTimestampValue(text=value)
        if kind not in ('timestamp', 'binary', 'date') or type(value) is not str:
            raise ValueError('Exact timestamp/binary/date token required')
        if kind == 'date':
            _date_token(value)
        return TextValue(kind=kind, text=value)
    if descriptor['kind'] == 'sequence':
        if type(value) is not list:raise ValueError('Complete logical sequence required')
        return tuple(_decode_value(item,descriptor['item'],descriptors_by_identity) for item in value)
    if descriptor['kind'] == 'map':
        if type(value) is not dict or any(type(key) is not str for key in value):raise ValueError('Complete logical map required')
        return MappingProxyType({key:_decode_value(value[key],descriptor['item'],descriptors_by_identity) for key in sorted(value)})
    if descriptor['kind'] == 'record':
        members = descriptor['members']
        if type(value) is not dict or set(value) != {m['name'] for m in members}:
            raise ValueError('Complete logical record required')
        return MappingProxyType({m['name']: _decode_value(value[m['name']], m['identity'], descriptors_by_identity) for m in members})
    raise ValueError('Unsupported query result shape')


def _immutable_metadata(value):
    if type(value) is dict:
        return MappingProxyType({k:_immutable_metadata(v) for k,v in value.items()})
    if type(value) is list:
        return tuple(_immutable_metadata(v) for v in value)
    return value


def _column_descriptors(artifact):
    original_graph=_artifact_type_graph(artifact)
    _index_value_descriptors(original_graph)
    graph=tuple(_immutable_metadata(d) for d in original_graph)
    indexed={_descriptor_identity_key(d['identity']):frozen for d,frozen in zip(original_graph,graph,strict=True)}
    result=[]
    for position,column in enumerate(artifact['columns'],1):
        if (type(column.get('position')) is not int or column['position']!=position
            or type(column.get('outputName')) is not str or type(column.get('nullable')) is not bool
            or type(column.get('representation')) is not dict or type(column.get('sourceIdentities')) is not list
            or any(type(identity) is not dict for identity in column['sourceIdentities'])):
            raise ValueError('Original compiler column metadata required')
        original=_immutable_metadata(column);representation=original['representation']
        descriptor=None
        if representation['kind']=='value':
            descriptor=indexed[_descriptor_identity_key(column['representation']['descriptor'])]
        logical_type=representation.get('logicalType')
        if logical_type is None and descriptor is not None and descriptor['kind']=='scalar':
            logical_type=descriptor['type']
        result.append(QueryColumnDescriptor(position=position,output_name=column['outputName'],
            representation=representation,source_identities=original['sourceIdentities'],
            sql_nullable=column['nullable'],logical_type=logical_type,value_descriptor=descriptor,
            type_graph=graph,original=original))
    return tuple(result)


def _decode_rows(raw_rows, artifact, maximum_rows, maximum_bytes):
    columns = artifact['columns']
    if len(raw_rows) > maximum_rows:
        return QueryRefused(code='limits')
    total = 0
    rows = []
    graph = _artifact_type_graph(artifact)
    descriptors_by_identity = None
    if any(column['representation']['kind'] == 'value' for column in columns):
        descriptors_by_identity = _index_value_descriptors(graph)
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
                decoded.append(_decode_value(json.loads(raw), representation['descriptor'], descriptors_by_identity))
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
    return QueryRows(columns=tuple(c['outputName'] for c in columns), rows=tuple(rows), catalog_revision=0,
        column_descriptors=_column_descriptors(artifact))


def run_query(host, transaction, *, sql, document_ids, parameters, maximum_rows,
              maximum_scan_rows, maximum_bytes, manifest, digest, pin_cursor, read_profile, page_size=None, page_cursor=None, engine_program=None, capture_catalog=False, temporal_binding=False,
              read_catalog=False,catalog_validator=None,entity_projection=None):
    try:
        temporal_program=_checked_temporal_engine_program(engine_program)
    except ValueError:
        return Ok(QueryRefused(code='invalid_query'))
    engine_temporal=temporal_program is not None
    try:
        valid = type(sql) is str and 1 <= len(sql.encode('utf8')) <= 1048576 and '\0' not in sql
        valid = valid and type(document_ids) is tuple and 1 <= len(document_ids) <= 32 and len(set(document_ids)) == len(document_ids)
        valid = valid and all(type(d) is str and 1 <= len(d.encode('utf8')) <= 4096 and '\0' not in d for d in document_ids)
        valid = valid and isinstance(parameters, Mapping) and len(parameters) <= 1024
        allowed=(str,int,bool,Decimal,TextValue,LocalTimestampValue,date,datetime) if engine_temporal else (str,int,bool,Decimal,TextValue,LocalTimestampValue)
        valid = valid and all(type(k) is str and 1 <= len(k.encode('utf8')) <= 4096 and '\0' not in k and type(v) in allowed for k, v in parameters.items())
        valid = valid and all(type(v) is not str or len(v.encode('utf8')) <= 1048576 and '\0' not in v for v in parameters.values())
    except (UnicodeError, TypeError, ValueError):
        valid = False
    valid=valid and (read_profile is None or type(read_profile) is str and read_profile in ('entity-page','related-entity-page','count-summary','complete-entity'))
    if entity_projection is not None:
        valid=valid and (type(entity_projection) is QueryEntityProjection
            and type(entity_projection.facts) is tuple and len(entity_projection.facts)<=8
            and all(type(f) is str and f in ('version','createdBy','createdAt','updatedBy','updatedAt','originalAuthor','originalAt','loadId') for f in entity_projection.facts)
            and len(set(entity_projection.facts))==len(entity_projection.facts)
            and type(entity_projection.relationships) is bool
            and read_profile is None and engine_program is None and not capture_catalog)
    if not valid:
        return Ok(QueryRefused(code='invalid_query'))
    if type(read_catalog) is not bool or read_catalog and (page_size is not None or capture_catalog or engine_program is not None
            or catalog_validator is not None and (type(catalog_validator) is not str or re.fullmatch(r'[0-9a-f]{64}',catalog_validator) is None)):
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
                if type(page_state) is not dict or set(page_state) != {'profile','context','after'} or type(page_state['context']) is not str:
                    return Ok(QueryRefused(code='invalid_query'))
                if engine_temporal:
                    after=page_state['after']
                    if (page_state['profile']!='truss-engine-page/0.4' or type(after)is not dict
                        or set(after)!={'key','sortValues'} or type(after['key'])is not list
                        or type(after['sortValues'])is not list or not after['key'] or not after['sortValues']
                        or any(not _validate_temporal_cursor_value(v) for v in after['key']+after['sortValues'])):
                        return Ok(QueryRefused(code='invalid_query'))
                    page=temporal_program.get('page')
                    if (temporal_program.get('version')!='weft.engine-page/0.4' or type(page)is not dict
                        or type(page.get('sortSlots'))is not list or type(page.get('keySlots'))is not list
                        or len(after['sortValues'])!=len(page['sortSlots']) or len(after['key'])!=len(page['keySlots'])):
                        return Ok(QueryRefused(code='invalid_query'))
                elif (page_state['profile'] != 'truss-query-page/0.2' or type(page_state['after']) is not list
                      or not page_state['after'] or any(type(v) is not str for v in page_state['after'])):
                    return Ok(QueryRefused(code='invalid_query'))
            except (ValueError, UnicodeError):
                return Ok(QueryRefused(code='invalid_query'))
    if (type(capture_catalog) is not bool or type(temporal_binding) is not bool
        or temporal_binding and not capture_catalog
        or temporal_binding and engine_temporal
        or engine_temporal and capture_catalog
        or engine_program is not None and (type(engine_program) is not str or len(engine_program.encode("utf8")) > 4194304)
        or capture_catalog and (page_size is not None or read_profile is not None)
        or engine_program is not None and read_profile is not None):
        return Ok(QueryRefused(code="invalid_query"))
    compile_query = None if temporal_binding else compiler(engine_catalog=engine_program is not None,engine_pages=page_size is not None and engine_program is not None,
                             entity_projection=entity_projection is not None,engine_temporal=engine_temporal)
    if compile_query is None and not temporal_binding:
        return Ok(QueryUnavailable(reason='compiler'))
    if engine_temporal:
        try:
            import weft
            shape_check=(weft.check_engine_temporal_page_shape_json if temporal_program['version']=='weft.engine-page/0.4'
                         else weft.check_engine_temporal_read_shape_json)
            shaped=json.loads(shape_check(engine_program,json.dumps(temporal_program['request'],ensure_ascii=False,separators=(',',':'))))
        except (ImportError,AttributeError,TypeError,ValueError,UnicodeError):
            return Ok(QueryRefused(code='invalid_query'))
        if shaped.get('status')!='checked':
            return Ok(QueryRefused(code='invalid_query'))
    if page_size is not None:
        try:
            import weft
            compile_query = weft.compile_engine_page_json if engine_temporal else weft.compile_truss_runtime_page_json
        except (ImportError, AttributeError):
            return Ok(QueryUnavailable(reason='compiler'))
    values={}
    exact_values={}
    for name,value in parameters.items():
        if engine_temporal and name in temporal_program['request']['temporalParameters']:
            continue
        if type(value) is LocalTimestampValue:
            try:validate_local_timestamp_text(value.text)
            except ValueError:return Ok(QueryRefused(code='invalid_query'))
            exact_values[name]={'scalarType':'localTimestamp','value':value.text}
            continue
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
    temporal_values={}
    if engine_temporal:
        try:
            temporal_values=_bind_temporal_parameters(temporal_program['request'],parameters,values,exact_values)
        except (ValueError,OverflowError,UnicodeError):
            return Ok(QueryRefused(code='invalid_query'))
    def execute(cursor, observed):
        pin_cursor(cursor)
        cache_key=(digest,document_ids,maximum_scan_rows,maximum_rows,maximum_bytes)
        hint=binding_hint(cache_key)
        if temporal_binding or engine_temporal:
            context_sql='SELECT truss.person_query_temporal_binding(%s::pg_catalog.jsonb,%s,%s,%s,%s,%s)'
            context_parameters=(json.dumps(document_ids),maximum_scan_rows,maximum_rows,maximum_bytes,manifest['releaseId'],digest)
        else:
            context_sql='SELECT truss.person_query_binding_if_changed(%s::pg_catalog.jsonb,%s,%s,%s,%s,%s,%s)'
            context_parameters=(json.dumps(document_ids),maximum_scan_rows,maximum_rows,maximum_bytes,manifest['releaseId'],digest,
                                None if hint is None else hint[0])
        if read_catalog:
            context_sql+=',truss.person_reader_catalog_if_changed(65536,%s,%s,%s,%s)'
            context_parameters+=(maximum_bytes,manifest['releaseId'],digest,catalog_validator)
        cursor.execute(context_sql,context_parameters,prepare=False)
        context_row=cursor.fetchone()
        answer=json.loads(bytes(context_row[0]))
        catalog_observation=None
        if read_catalog:
            catalog_answer=json.loads(bytes(context_row[1]))
            if catalog_answer.get('outcome')=='unchanged' and set(catalog_answer)=={'outcome','validator'} and catalog_answer['validator']==catalog_validator:
                catalog_observation=ReaderCatalogUnchanged(catalog_answer['validator'])
            elif catalog_answer.get('outcome')=='snapshot' and set(catalog_answer)=={'outcome','validator','catalog'}:
                catalog=catalog_answer['catalog']
                catalog_observation=ReaderCatalogSnapshot(ReaderCatalog(catalog['catalogRevision'],catalog['layoutProfile'],tuple(catalog['modules'])),catalog_answer['validator'])
            else:raise ValueError('Exact combined reader catalog observation required')
        if temporal_binding or engine_temporal:
            if type(context_row[0]) is not bytes:
                raise ValueError('Exact explicit temporal query binding required')
            bundle=json.loads(context_row[0])
            if type(bundle) is not dict or set(bundle)!={'binding','bindingJson','modules','actorOid'}:
                raise ValueError('Exact explicit temporal query binding required')
        elif answer.get('outcome')=='unchanged':
            if hint is None or set(answer)!={'outcome','validator'} or answer['validator']!=hint[0]:
                raise ValueError('Original cached query binding required')
            bundle=json.loads(hint[1])
        elif answer.get('outcome')=='snapshot':
            if set(answer)!={'outcome','validator','bundle'} or type(answer['validator']) is not str or re.fullmatch(r'[0-9a-f]{64}',answer['validator']) is None:
                raise ValueError('Exact observed query binding required')
            bundle=answer['bundle']
            remember_binding(cache_key,answer['validator'],json.dumps(bundle,ensure_ascii=False,separators=(',',':')))
        else:
            raise ValueError('Exact conditional query binding result required')
        binding_json = bundle['bindingJson']
        binding = json.loads(binding_json)
        if binding != bundle['binding'] or binding['releaseId'] != manifest['releaseId'] or binding['releaseSha256'] != digest:
            raise ValueError('Exact installed query binding required')
        binding_sha = sha256(binding_json.encode('utf8')).hexdigest()
        selected_backend=TEMPORAL_BACKEND if (temporal_binding or engine_temporal) else BACKEND
        if engine_temporal:
            request=dict(temporal_program['request'])
            request['sql']=sql
            request['modules']=bundle['modules']
            request['parameters']=values
            request['exactParameters']=exact_values
            request['temporalParameters']=temporal_values
            request['target']=dict(request['target'])
            request['target'].update({'backendId':selected_backend['backendId'],
                'backendVersion':selected_backend['backendVersion'],'targetProfile':selected_backend['targetProfile'],
                'bindingJson':binding_json,'bindingSha256':binding_sha})
        else:
            request = {'interfaceVersion': 'weft-compile/0.2.10' if temporal_binding else 'weft-compile/0.2.8',
                       'dialect': 'weft-sql/0.2.0', 'sql': sql,
                       'timestampComparisonProfile':'umf-rfc3339-exact-instant/1.0.0', 'modules': bundle['modules'], 'parameters': values, 'exactParameters': exact_values, 'options': {'allowCandidate': True},
                       'target': {'backendId': selected_backend['backendId'], 'backendVersion': selected_backend['backendVersion'],
                                  'targetProfile': selected_backend['targetProfile'], 'bindingJson': binding_json, 'bindingSha256': binding_sha}}
        if temporal_binding or engine_temporal:
            temporal_abi=query_temporal_abi()
            expected_abi={'identity':temporal_abi['identity'],'version':temporal_abi['version'],'sha256':TEMPORAL_QUERY_ABI_SHA256}
            if binding.get('queryAbi')!=expected_abi:
                raise ValueError('Exact ABI 1.3 binding required')
            request['temporalProfile']=TEMPORAL_ENGINE_PROFILE
            if not engine_temporal:
                request['temporalParameters']={}
        if read_profile is not None:request['readProfile']={'version':'weft-truss-entity-read/0.3.0' if read_profile=='complete-entity' else 'weft-application-read/0.2.0','subset':read_profile}
        if entity_projection is not None:
            request['readProfile']={'version':'weft-truss-entity-read/0.4.0',
                'subset':'complete-entity-page' if page_size is not None else 'complete-entity',
                'entityProjection':{'facts':list(entity_projection.facts),'relationships':entity_projection.relationships}}
        if temporal_binding:
            if exact_values or temporal_values:
                cursor.execute('SELECT truss.person_query_scope(%s::pg_catalog.jsonb)',(binding_json,),prepare=False)
                return QueryRefused(code='invalid_query')
            # This method captures a fresh ABI1.3 source bundle only. The caller
            # must still submit the returned compiler inputs to a selected
            # owner engine compiler; this path never executes business SQL.
            return QueryCatalogSources(request_json=json.dumps(request,ensure_ascii=False,separators=(',',':')))
        page_metadata = None
        if page_size is not None:
            # Each page composes and reauthorizes the current accepted catalog.
            page_scope={'sql':sql,'parameters':values,'exactParameters':exact_values,'documents':document_ids,
                'binding':binding,'actorOid':bundle['actorOid'],'pageSize':page_size,
                'entityProjection':None if entity_projection is None else request['readProfile']}
            if engine_temporal:
                original_temporal_request=json.loads(json.dumps(temporal_program['request']))
                target=original_temporal_request.get('target')
                if type(target)is dict:
                    target.pop('bindingJson',None);target.pop('bindingSha256',None)
                page_scope['temporalProgram']={'version':temporal_program['version'],'profile':temporal_program['temporalProfile'],
                    'request':original_temporal_request,'selectedKey':temporal_program.get('selectedKey')}
            context = sha256(json.dumps(page_scope,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf8')).hexdigest()
            if page_state is not None and page_state['context'] != context:
                return QueryRefused(code='stale_context')
            if engine_temporal:
                packet={'version':'weft.engine-page/0.4','compiler':'truss-runtime-temporal',
                    'temporalProfile':TEMPORAL_ENGINE_PROFILE,'request':request,'pageSize':page_size,
                    'selectedKey':temporal_program.get('selectedKey'),
                    'after':None if page_state is None else page_state['after']}
                try:response=json.loads(compile_query(json.dumps(packet,ensure_ascii=False,separators=(',',':'))))
                except (TypeError,ValueError,UnicodeError):raise ValueError('Exact temporal page compiler response required') from None
                if response.get('status')=='compiled':
                    if (response.get('version')!='weft.engine-page/0.4' or response.get('compiler')!='truss-runtime-temporal'
                        or response.get('temporalProfile')!=TEMPORAL_ENGINE_PROFILE
                        or response.get('request')!=request or response.get('pageSize')!=page_size
                        or response.get('after')!=(None if page_state is None else page_state['after'])):
                        raise ValueError('Exact temporal engine page response required')
                    artifact=response.get('artifact');page_metadata=response.get('page')
                else:artifact=response
            else:
                response = compile_response(compile_query,json.dumps(request,ensure_ascii=False),page_size,None if page_state is None else page_state['after'])
            if not engine_temporal and response.get('status') == 'compiled':
                if response.get('interfaceVersion') != 'weft-sql-page/0.2' or set(response) != {'interfaceVersion','status','artifact','page'}:
                    raise ValueError('Exact owner page response required')
                artifact, page_metadata = response['artifact'], response['page']
            elif not engine_temporal:
                artifact = response
        else:
            if engine_temporal:
                packet={'version':'weft.engine-read/0.4','compiler':'truss-runtime-temporal',
                    'temporalProfile':TEMPORAL_ENGINE_PROFILE,'request':request}
                try:response=json.loads(compile_query(json.dumps(packet,ensure_ascii=False,separators=(',',':'))))
                except (TypeError,ValueError,UnicodeError):raise ValueError('Exact temporal engine compiler response required') from None
                if response.get('status')=='compiled':
                    if (response.get('version')!='weft.engine-read/0.4' or response.get('compiler')!='truss-runtime-temporal'
                        or response.get('temporalProfile')!=TEMPORAL_ENGINE_PROFILE or response.get('request')!=request):
                        raise ValueError('Exact temporal engine response required')
                    artifact=response.get('artifact')
                else:artifact=response
            else:
                artifact = compile_response(compile_query,json.dumps(request, ensure_ascii=False))
        if artifact['status'] != 'compiled':
            cursor.execute('SELECT truss.person_query_scope(%s::pg_catalog.jsonb)', (binding_json,), prepare=False)
            diagnostics = tuple(QueryDiagnostic(code=d['code'], message=d['message']) for d in artifact.get('diagnostics', ()))
            unsupported = any(d.code in ('WFT-CAPABILITY', 'WFT-TYPE', 'WFT-PROFILE') for d in diagnostics)
            return QueryRefused(code='unsupported_query' if unsupported else 'invalid_query', diagnostics=diagnostics)
        if engine_temporal:
            source_checks=response.get('sourceDomainChecks')
            if (type(artifact)is not dict or type(response.get('outputs')) is not list
                or response.get('outputs')!=temporal_program.get('outputs')
                or type(source_checks)is not dict
                or set(source_checks)!={'version','mode','queryAbi','maxScanRows','maxBytes','sources'}
                or source_checks.get('version')!='weft.truss-temporal-domain-checks/0.2'
                or source_checks.get('mode')!='native-validated-source'
                or source_checks.get('queryAbi')!={'identity':'truss-postgresql-logical-query','version':'1.3',
                    'sha256':TEMPORAL_QUERY_ABI_SHA256}
                or source_checks.get('maxScanRows')!=binding['maximumScanRows']
                or source_checks.get('maxBytes')!=binding['maximumBytes']
                or type(source_checks.get('sources')) is not list or len(source_checks['sources'])!=1
                or artifact.get('bindingSha256')!=binding_sha):
                raise ValueError('Exact temporal artifact/source requirements required')
            import weft
            checker=(weft.check_engine_temporal_page_json if page_size is not None
                     else weft.check_engine_temporal_read_json)
            arguments=(engine_program,json.dumps(request,ensure_ascii=False,separators=(',',':')),
                       json.dumps(None if page_state is None else page_state['after'],separators=(',',':'))) if page_size is not None else (
                       engine_program,json.dumps(request,ensure_ascii=False,separators=(',',':')))
            try:checked=json.loads(checker(*arguments))
            except (TypeError,ValueError,UnicodeError):raise ValueError('Full original temporal compiler check required') from None
            checked_program=checked.get('program') if page_size is None else checked
            valid_check=(checked.get('status')=='checked' and type(checked_program)is dict
                and checked_program==response and checked_program.get('sourceDomainChecks')==response['sourceDomainChecks']) if page_size is None else (
                checked.get('status')=='compiled' and type(checked_program)is dict
                and checked_program==response and checked_program.get('sourceDomainChecks')==response['sourceDomainChecks'])
            if not valid_check:
                cursor.execute('SELECT truss.person_query_scope(%s::pg_catalog.jsonb)',(binding_json,),prepare=False)
                return QueryRefused(code='stale_context')
        else:
            if artifact['interfaceVersion'] != request['interfaceVersion'] or artifact['dialect'] != request['dialect'] or artifact['logicalPlan']['irVersion'] != 'weft-ir/0.2.8':
                raise ValueError('Exact selected compile/dialect/IR versions required')
            if artifact['backend'] != BACKEND or artifact['bindingSha256'] != binding_sha or artifact['modelPins'] != [m['pin'] for m in bundle['modules']]:
                raise ValueError('Original compiled binding/model/backend required')
        if page_size is not None and page_cursor is not None and page_cursor.sort_values is not None:
            try:
                if engine_temporal:
                    slots=temporal_program['page']['sortSlots'];key_slots=temporal_program['page']['keySlots']
                    if type(page_cursor.sort_values)is not tuple or len(page_cursor.sort_values)!=len(key_slots):
                        return QueryRefused(code='invalid_query')
                    encoded=[_temporal_cursor_typed_value(value,slots[index]) for value,index in zip(page_cursor.sort_values,key_slots,strict=True)]
                    if encoded!=page_state['after']['key']:return QueryRefused(code='stale_context')
                else:
                    types = _relationship_key_types(artifact['logicalPlan']['pageKey']['types'],maximum=1024)
                    if type(page_cursor.sort_values) is not tuple or len(types)!=len(page_cursor.sort_values):
                        return QueryRefused(code='invalid_query')
                    if [_page_key_token(value,t) for value,t in zip(page_cursor.sort_values,types,strict=True)] != page_state['after']:
                        return QueryRefused(code='stale_context')
            except (ValueError,UnicodeError,KeyError,TypeError):return QueryRefused(code='invalid_query')
        if engine_program is not None and not engine_temporal:
            import weft
            checked = json.loads(weft.check_engine_read_json(engine_program, json.dumps(request, ensure_ascii=False)) if page_size is None else weft.check_engine_page_json(engine_program, json.dumps(request, ensure_ascii=False), json.dumps(None if page_state is None else page_state["after"])))
            profile_pair=(checked.get('compiler'),checked.get('version'))
            profile_kind='read' if page_size is None else 'page'
            if (checked.get("status") != "compiled" or profile_pair not in (
                    ('truss-runtime','weft.engine-'+profile_kind+'/0.1'),
                    ('truss-runtime-binary','weft.engine-'+profile_kind+'/0.2')) or checked.get("artifact") != artifact
                or page_size is not None and (checked.get("pageSize") != page_size or checked.get("page") != page_metadata)):
                cursor.execute('SELECT truss.person_query_scope(%s::pg_catalog.jsonb)', (binding_json,), prepare=False)
                return QueryRefused(code='stale_context')
        if capture_catalog:
            if not temporal_binding:
                cursor.execute('SELECT truss.person_query_scope(%s::pg_catalog.jsonb)', (binding_json,), prepare=False)
            return QueryCatalogSources(request_json=json.dumps(request, ensure_ascii=False, separators=(',', ':')))
        if not artifact['obligations'] or any(o['id'] != 'truss.runtime.context/0.1' or o['owner'] != 'host' for o in artifact['obligations']):
            raise ValueError('Every compiled obligation must have an installed handler')
        slots = artifact['parameters']
        if [s['position'] for s in slots] != list(range(1, len(slots) + 1)) or any(type(s['value']) is not str for s in slots):
            raise ValueError('Original native parameter slots required')
        cursor.execute("WITH prior AS MATERIALIZED (SELECT pg_catalog.current_setting('search_path') AS path) "
            "SELECT path,pg_catalog.set_config('search_path','pg_catalog,pg_temp',true) FROM prior", prepare=False)
        original_path, pinned_path = cursor.fetchone()
        if pinned_path != 'pg_catalog,pg_temp':
            raise ValueError('Fixed query search path required')
        # Fixed context handler and source functions independently recheck all owners.
        cursor.execute('SELECT truss.person_query_scope(%s::pg_catalog.jsonb)', (binding_json,), prepare=False)
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
            if logical_type == {'kind':'exactScalar','scalarType':'localTimestamp'}:
                validate_local_timestamp_text(slot['value'])
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
                    cursor.execute('SELECT truss.person_query_scope(%s::pg_catalog.jsonb)',(binding_json,),prepare=False)
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
            cursor.execute('SELECT truss.person_query_scope(%s::pg_catalog.jsonb)',(binding_json,),prepare=False)
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
        final_sql='SELECT truss.person_query_scope(%s::pg_catalog.jsonb),r.oid::text'
        final_parameters=(binding_json,)
        if read_catalog:
            final_sql+=',truss.reader_catalog_if_changed(65536,%s,%s,%s,%s)'
            final_parameters+=(maximum_bytes,manifest['releaseId'],digest,catalog_observation.validator)
        cursor.execute(final_sql+' FROM pg_catalog.pg_roles r WHERE r.rolname=session_user',final_parameters,prepare=False)
        post_scope = cursor.fetchone()
        if post_scope is None or post_scope[1] != bundle['actorOid']:
            raise ValueError('Original query actor required')
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)", (original_path,), prepare=False)
        if cursor.fetchone() != (original_path,):
            raise ValueError('Caller search path restoration required')
        if read_catalog and json.loads(bytes(post_scope[2]))!={'outcome':'unchanged','validator':catalog_observation.validator}:
            return QueryRefused(code='stale_context')
        if isinstance(result, QueryRows) and page_metadata is not None and engine_temporal:
            if page_state is not None:
                previous=page_state['after']
                if len(previous['key'])!=len(page_metadata.get('keySlots',())) or len(previous['sortValues'])!=len(page_metadata.get('sortSlots',())):
                    return QueryRefused(code='invalid_query')
            try:
                temporal_page=_temporal_page_result(result,page_metadata,page_size,context,binding['catalogRevision'],position)
            except (ValueError,UnicodeError,KeyError,TypeError,IndexError):
                return QueryRefused(code='invalid_query')
            return temporal_page
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
            return QueryPage(columns=result.columns[:visible],rows=tuple(row[:visible] for row in retained),catalog_revision=binding['catalogRevision'],next_cursor=next_cursor,as_of=position,next_sort_values=None if next_cursor is None else tuple(retained[-1][index] for index in keys),column_descriptors=result.column_descriptors[:visible])
        if isinstance(result, QueryRows):
            rows=QueryRows(columns=result.columns,rows=result.rows,catalog_revision=binding['catalogRevision'],as_of=position,column_descriptors=result.column_descriptors)
            if read_catalog:
                documents=tuple(QueryDocument(m['pin']['documentId'],m['pin']['revision'],m['pin']['umfVersion'],m['pin']['sha256'],m['documentJson'].encode('utf8')) for m in bundle['modules'])
                if any(sha256(d.content).hexdigest()!=d.sha256 for d in documents):
                    raise ValueError('Original combined source bytes required')
                return QueryCatalogRead(rows,catalog_observation,documents)
            return rows
        return result
    result = host._run_operation(transaction, execute)
    if isinstance(result, Error) and result.error.code=='execution_obligation':
        state = result.error.sql_state
        if state == 'P1403':
            return Ok(QueryRefused(code='unauthorized'))
        if state=='22003':return Ok(QueryRefused(code='native_domain'))
        if state in ('0A000', '54000', '55P03'):
            return Ok(QueryRefused(code={'0A000': 'unsupported_query', '54000': 'limits', '55P03': 'stale_context'}[state]))
    return result
