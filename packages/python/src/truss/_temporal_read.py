# SPDX-License-Identifier: MIT OR Apache-2.0
"""Profile-bound PV1 reads; shared object/history native engines, no fallback."""
import base64
import json
from .contracts import BooleanValue,TextValue,ProfilePin
from .execution import Error,Ok
from .object_read import ObjectNotFound,ObjectReadInvalid,ObjectReadRefused,ObjectReadUnavailable
from ._temporal_profiles import profiles,abi
from ._temporal_values import logical_object_cell

_OBJECT_FIELDS={'profile','releaseId','releaseSha256','documentId','moduleId','recordId','id','typeId',
                'definitionPin','version','catalogRevision','recordRevision','createdAt','updatedAt','values','retained','valueProfile','queryAbi'}
_INT32_MAX=2147483647
_INT64_MAX=9223372036854775807


def _decimal_string(value,maximum,field):
    """Admit the exact native positive decimal string BEFORE conversion."""
    bound=str(maximum)
    if (type(value) is not str or not value or value[0]=='0' or not value.isascii() or not value.isdecimal()
            or len(value)>len(bound) or len(value)==len(bound) and value>bound):
        raise ValueError('Canonical positive bounded native decimal string required: '+field)
    return int(value)


def decode_cursor(value,manifest,digest):
    from . import temporal as dto
    if (type(value) is not dict or set(value)!={'profile','installationId','sourceEpoch','releaseSha256',
            'documentId','moduleId','recordId','typeId','definitionPin','catalogRevision','afterId','valueProfile','queryAbi','originalCursorBase64'}
            or value['profile']!='truss-python-temporal-object-page/0.1' or value['releaseSha256']!=digest
            or value['valueProfile']!=profiles()['valueProfile'] or value['queryAbi']!=abi()):
        raise ValueError('Whole actual selected native cursor required')
    encoded=value['originalCursorBase64']
    if type(encoded) is not str:raise ValueError('Exact native cursor base64 required')
    original=base64.b64decode(encoded,validate=True)
    if not 1<=len(original)<=65536 or base64.b64encode(original).decode('ascii')!=encoded:
        raise ValueError('Canonical lossless bounded native cursor base64 required')
    # Custody comparison only: the native provider verifies its seal and person.
    # Never regenerate these bytes from this metadata or claim Python admission.
    from ._owner_evidence_json import decode_owner_evidence_json
    envelope=decode_owner_evidence_json(original)
    metadata={k:v for k,v in value.items() if k!='originalCursorBase64'}
    if (type(envelope) is not dict or set(envelope)!={'payload','digest'}
            or type(envelope['payload']) is not dict or envelope['payload'].get('metadata')!=metadata):
        raise ValueError('Original native cursor and metadata correspondence required')
    return dto.ObjectPageCursor(original_bytes=original,installation_id=value['installationId'],source_epoch=value['sourceEpoch'],
        release_sha256=value['releaseSha256'],document_id=value['documentId'],module_id=value['moduleId'],record_id=value['recordId'],
        type_id=_decimal_string(value['typeId'],_INT32_MAX,'cursor.typeId'),definition_pin=value['definitionPin'],
        catalog_revision=_decimal_string(value['catalogRevision'],_INT32_MAX,'cursor.catalogRevision'),
        after_id=_decimal_string(value['afterId'],_INT64_MAX,'cursor.afterId'),
        value_profile=ProfilePin(**value['valueProfile']),query_abi=ProfilePin(**value['queryAbi']))


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
    if owned:
        _decimal_string(value['root']['id'],_INT64_MAX,'root.id')
        _decimal_string(value['root']['typeId'],_INT32_MAX,'root.typeId')
    extra={'ownership':OwnedOwnership(root=StoredObjectReference(identity=_identity(value['root'])))} if owned else {}
    return dto.ObjectFound(object=object_type(**extra,document_id=value['documentId'],module_id=value['moduleId'],record_id=value['recordId'],
        id=_decimal_string(value['id'],_INT64_MAX,'object.id'),type_id=_decimal_string(value['typeId'],_INT32_MAX,'object.typeId'),
        definition_pin=value['definitionPin'],version=_decimal_string(value['version'],_INT64_MAX,'object.version'),
        catalog_revision=_decimal_string(value['catalogRevision'],_INT32_MAX,'object.catalogRevision'),
        record_revision=_decimal_string(value['recordRevision'],_INT32_MAX,'object.recordRevision'),created_at=value['createdAt'],updated_at=value['updatedAt'],
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
        if type(cursor.original_bytes) is not bytes or not 1<=len(cursor.original_bytes)<=65536:
            return Ok(ObjectReadInvalid(code='cursor'))
        value={key:_wire(getattr(cursor,name)) for key,name in (
            ('profile','profile'),('installationId','installation_id'),('sourceEpoch','source_epoch'),
            ('releaseSha256','release_sha256'),('documentId','document_id'),('moduleId','module_id'),
            ('recordId','record_id'),('typeId','type_id'),('definitionPin','definition_pin'),
            ('catalogRevision','catalog_revision'),('afterId','after_id'),('valueProfile','value_profile'),('queryAbi','query_abi'))}
        for key,maximum in (('typeId',_INT32_MAX),('catalogRevision',_INT32_MAX),('afterId',_INT64_MAX)):
            if type(value[key]) is not int or not 1<=value[key]<=maximum:return Ok(ObjectReadInvalid(code='cursor'))
            value[key]=str(value[key])
        value['originalCursorBase64']=base64.b64encode(cursor.original_bytes).decode('ascii')
        try:decode_cursor(value,manifest,digest)
        except (ValueError,TypeError,KeyError,AttributeError):return Ok(ObjectReadInvalid(code='cursor'))
        original=cursor.original_bytes
    def observe(native_cursor,observed):
        pin_cursor(native_cursor)
        native_cursor.execute('SELECT truss.person_page_temporal_objects(%s,%s,%s,%s,%s,%s,%s,%s)',
            (args['document_id'],args['module_id'],args['record_id'],args['limit'],args['maximum_bytes'],original,manifest['releaseId'],digest),prepare=False)
        raw=native_cursor.fetchone()[0]
        if raw is None:return ObjectNotFound()
        from ._owner_evidence_json import decode_owner_evidence_json
        value=decode_owner_evidence_json(bytes(raw))
        if (set(value)!={'profile','catalogRevision','objects','continuation','valueProfile','queryAbi'}
            or value['profile']!='truss-python-temporal-object-page/0.1'
            or value['valueProfile']!=profiles()['valueProfile'] or value['queryAbi']!=abi()):
            raise ValueError('Closed actual temporal object page required')
        # Unlike object/cursor wire fields, the frozen page envelope carries a
        # JSON integer revision. Preserve that type and its actual native range.
        if type(value['catalogRevision']) is not int or not 1<=value['catalogRevision']<=_INT32_MAX:
            raise ValueError('Exact native page revision required')
        following=None if value['continuation'] is None else decode_cursor(value['continuation'],manifest,digest)
        return dto.ObjectPage(objects=tuple(decode_object(json.dumps(obj).encode(),manifest,digest).object for obj in value['objects']),
                              catalog_revision=value['catalogRevision'],continuation=following)
    return _result(assembly,assembly._host._run_operation(args['transaction'],observe,function_call=True))
