# SPDX-License-Identifier: MIT OR Apache-2.0
"""Profile-bound PV1 reads; shared object/history native engines, no fallback."""
import json
from .contracts import BooleanValue,TextValue,ProfilePin
from .execution import Error,Ok
from .object_read import ObjectNotFound,ObjectReadInvalid,ObjectReadRefused,ObjectReadUnavailable
from ._temporal_profiles import profiles,abi
from ._temporal_values import logical_object_cell

_OBJECT_FIELDS={'profile','releaseId','releaseSha256','documentId','moduleId','recordId','id','typeId',
                'definitionPin','version','catalogRevision','recordRevision','createdAt','updatedAt','values','retained','valueProfile','queryAbi'}


def decode_object(raw,manifest,digest):
    from . import temporal as dto
    from .groups import OwnedOwnership,StoredObjectReference
    from ._group_runtime import _identity
    from ._owner_evidence_json import decode_owner_evidence_json
    value=decode_owner_evidence_json(bytes(raw))
    owned=value.get('profile')=='truss-python-temporal-logical-object/0.1'
    if (value.get('profile') not in ('truss-python-temporal-scalar-object/0.1','truss-python-temporal-logical-object/0.1')
        or set(value)!=_OBJECT_FIELDS|({'root'} if owned else set())
        or value['releaseId']!=manifest['releaseId'] or value['releaseSha256']!=digest
        or value['valueProfile']!=profiles()['valueProfile'] or value['queryAbi']!=abi()):
        raise ValueError('Closed actual selected temporal object envelope required')
    object_type=dto.LogicalObject if owned else dto.ScalarObject
    extra={'ownership':OwnedOwnership(root=StoredObjectReference(identity=_identity(value['root'])))} if owned else {}
    return dto.ObjectFound(object=object_type(**extra,document_id=value['documentId'],module_id=value['moduleId'],record_id=value['recordId'],
        id=int(value['id']),type_id=int(value['typeId']),definition_pin=value['definitionPin'],version=int(value['version']),
        catalog_revision=int(value['catalogRevision']),record_revision=int(value['recordRevision']),created_at=value['createdAt'],updated_at=value['updatedAt'],
        values=tuple((name,logical_object_cell(cell,local=True)) for name,cell in value['values']),
        retained=tuple((name,logical_object_cell(cell,local=False)) for name,cell in value['retained'])))


def _valid_selection(args, names):
    try:return all(type(args[k]) is str and 1<=len(args[k].encode())<=4096 and '\0' not in args[k] for k in names)
    except UnicodeError:return False


def _result(assembly,result):
    from .catalog_runtime import _admission_refused
    if _admission_refused(result):return Ok(ObjectReadRefused())
    if isinstance(result,Error) and result.error.code=='execution_obligation':
        state=result.error.sql_state
        if state=='22023':return Ok(ObjectReadInvalid(code='selection'))
        reason={'0A000':'profile','42883':'profile','3F000':'profile','54000':'resource','55P03':'observation','P1002':'context'}.get(state)
        if reason:return Ok(ObjectReadUnavailable(reason=reason))
    return result


def execute_read(assembly,operation,args):
    from .catalog_runtime import _release,_pin_cursor
    if operation in ('page_history_in_transaction','reconstruct_in_transaction'):
        from .history import HistoryUnavailable
        version=None if operation=='page_history_in_transaction' else args['version']
        if version is not None and (type(version) is not int or not 1<=version<=9223372036854775807):
            return Ok(HistoryUnavailable(reason='context'))
        return assembly._read_history(args['transaction'],args['entity'],args.get('cursor'),version,
                                      args['maximum_events'],args['maximum_bytes'],temporal=True)
    if not _valid_selection(args,('document_id','module_id','record_id')):return Ok(ObjectReadInvalid(code='selection'))
    if type(args['maximum_bytes']) is not int or not 1<=args['maximum_bytes']<=16777216:return Ok(ObjectReadInvalid(code='limits'))
    manifest,digest,_=_release()
    if operation=='get_object_in_transaction':
        if type(args['object_id']) is not int or not 1<=args['object_id']<=9223372036854775807:return Ok(ObjectReadInvalid(code='selection'))
        command='SELECT truss.person_get_temporal_object(%s,%s,%s,%s,%s,%s,%s)'
        parameters=(args['document_id'],args['module_id'],args['record_id'],args['object_id'],args['maximum_bytes'],manifest['releaseId'],digest)
    elif operation=='lookup_key_in_transaction':
        if not _valid_selection(args,('key_id',)):return Ok(ObjectReadInvalid(code='selection'))
        from ._group_runtime import _wire
        values=args['values']
        try:
            if type(values) is not tuple or not 1<=len(values)<=1024 or not all(
                type(v) is str and '\0' not in v or type(v) is BooleanValue or
                type(v) is TextValue and v.kind in ('string','integer','decimal','binary') and '\0' not in v.text for v in values):
                return Ok(ObjectReadInvalid(code='key_values'))
            encoded=json.dumps([{'kind':'string','text':v} if type(v) is str else _wire(v) for v in values],ensure_ascii=True).encode()
        except (ValueError,TypeError,UnicodeError):return Ok(ObjectReadInvalid(code='key_values'))
        if len(encoded)>1048576:return Ok(ObjectReadUnavailable(reason='resource'))
        document=args['original_document']
        if document is not None and (type(document) is not bytes or not 1<=len(document)<=1048576):return Ok(ObjectReadInvalid(code='source'))
        command='SELECT truss.person_lookup_temporal_key(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        parameters=(args['document_id'],args['module_id'],args['record_id'],args['key_id'],document,encoded,None,args['maximum_bytes'],manifest['releaseId'],digest)
    else:
        return _page(assembly,args,manifest,digest,_pin_cursor)
    def observe(cursor,observed):
        _pin_cursor(cursor)
        cursor.execute(command,parameters,prepare=False)
        raw=cursor.fetchone()[0]
        return ObjectNotFound() if raw is None else decode_object(raw,manifest,digest)
    return _result(assembly,assembly._host._run_operation(args['transaction'],observe,function_call=True))


def _page(assembly,args,manifest,digest,pin_cursor):
    from . import temporal as dto
    from ._group_runtime import _wire
    if type(args['limit']) is not int or not 1<=args['limit']<=1000:return Ok(ObjectReadInvalid(code='limits'))
    cursor=args['cursor'];original=None
    if cursor is not None:
        if type(cursor) is not dto.ObjectPageCursor:return Ok(ObjectReadInvalid(code='cursor'))
        if (cursor.document_id,cursor.module_id,cursor.record_id)!=(args['document_id'],args['module_id'],args['record_id']):
            return Ok(ObjectReadInvalid(code='cursor_selection'))
        if _wire(cursor.value_profile)!=profiles()['valueProfile'] or _wire(cursor.query_abi)!=abi():return Ok(ObjectReadInvalid(code='cursor'))
        value=_wire(cursor)
        for key in ('typeId','catalogRevision','afterId'):
            if type(value[key]) is not int or value[key]<=0:return Ok(ObjectReadInvalid(code='cursor'))
            value[key]=str(value[key])
        original=json.dumps(value,ensure_ascii=True).encode()
        if len(original)>65536:return Ok(ObjectReadInvalid(code='cursor'))
    def observe(native_cursor,observed):
        pin_cursor(native_cursor)
        native_cursor.execute('SELECT truss.person_page_temporal_objects(%s,%s,%s,%s,%s,%s,%s,%s)',
            (args['document_id'],args['module_id'],args['record_id'],args['limit'],args['maximum_bytes'],original,manifest['releaseId'],digest),prepare=False)
        raw=native_cursor.fetchone()[0]
        if raw is None:return ObjectNotFound()
        value=json.loads(bytes(raw))
        if (set(value)!={'profile','catalogRevision','objects','continuation','valueProfile','queryAbi'}
            or value['profile']!='truss-python-temporal-object-page/0.1'
            or value['valueProfile']!=profiles()['valueProfile'] or value['queryAbi']!=abi()):
            raise ValueError('Closed actual temporal object page required')
        following=value['continuation']
        if following is not None:
            following=dto.ObjectPageCursor(installation_id=following['installationId'],source_epoch=following['sourceEpoch'],
                release_sha256=following['releaseSha256'],document_id=following['documentId'],module_id=following['moduleId'],record_id=following['recordId'],
                type_id=int(following['typeId']),definition_pin=following['definitionPin'],catalog_revision=int(following['catalogRevision']),after_id=int(following['afterId']),
                value_profile=ProfilePin(**following['valueProfile']),query_abi=ProfilePin(**following['queryAbi']))
        return dto.ObjectPage(objects=tuple(decode_object(json.dumps(obj).encode(),manifest,digest).object for obj in value['objects']),
                              catalog_revision=value['catalogRevision'],continuation=following)
    return _result(assembly,assembly._host._run_operation(args['transaction'],observe,function_call=True))
