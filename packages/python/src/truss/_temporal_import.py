# SPDX-License-Identifier: MIT OR Apache-2.0
"""PV1 explicit object import construction and shared original orchestrators."""
import json
from .contracts import ProfilePin,BooleanValue,TextValue,ObjectKeySelection,ObjectKeyComponent,ReadTypeReference,QualifiedOwner
from .imports import ObjectImportRecord,OwnedObjectImportRecord,ImportCatalogPin,ImportInvalid
from .execution import Ok
from ._temporal_profiles import profiles,abi


def context_from_native(value,manifest,digest,*,owned=False):
    from . import temporal as dto
    selected=profiles()
    import_key='ownedImportProfile' if owned else 'importProfile'
    payload_key='ownedImportPayloadProfile' if owned else 'importPayloadProfile'
    if (value['valueProfile']!=selected['valueProfile'] or value[import_key]!=selected[import_key]
        or value[payload_key]!=selected[payload_key] or value['queryAbi']!=abi()
        or value['releaseId']!=manifest['releaseId'] or value['releaseSha256']!=digest):
        raise ValueError('Actual selected temporal import capability required')
    cls=dto.OwnedImportRuntimeContext if owned else dto.ImportRuntimeContext
    return cls(layout_profile=ProfilePin(**value['layoutProfile']),import_profile=ProfilePin(**value[import_key]),
        value_profile=ProfilePin(**value['valueProfile']),payload_profile=ProfilePin(**value[payload_key]),
        catalog=ImportCatalogPin(revision=value['catalog']['revision'],model_bundle_sha256=value['catalog']['modelBundleSha256']),
        query_abi=ProfilePin(**value['queryAbi']),release_id=value['releaseId'],release_sha256=value['releaseSha256'])


def execute_import(assembly,operation,args):
    from .catalog_runtime import _release,_pin_cursor,_admission_refused
    from .groups import UnauthorizedPerson
    from . import temporal as dto
    manifest,digest,_=_release()
    if operation=='import_in_transaction':
        if type(args['input']) is dto.ImportInput:
            from ._import_runtime import run_import
            return run_import(assembly._host,args['transaction'],args['input'],args['documents'],manifest,digest,_pin_cursor,
                              bun_executable=args['bun_executable'],temporal=True)
        if type(args['input']) is dto.OwnedImportInput:
            from ._owned_import_runtime import run_owned_import
            return run_owned_import(assembly._host,args['transaction'],args['input'],args['documents'],manifest,digest,_pin_cursor,
                                    bun_executable=args['bun_executable'],temporal=True)
        from ._import_runtime import _DIAGNOSTIC
        from ._group_runtime import _artifact
        return ImportInvalid(diagnostic_profile=_DIAGNOSTIC,diagnostic=_artifact(b'{"code":"temporal_input_shape"}'))
    owned=operation in ('owned_import_context_in_transaction','owned_object_import_record_in_transaction')
    def observe(cursor,observed):
        _pin_cursor(cursor)
        if operation in ('import_context_in_transaction','owned_import_context_in_transaction'):
            cursor.execute('SELECT truss.person_temporal_import_context(%s,%s)',(manifest['releaseId'],digest),prepare=False)
            return context_from_native(json.loads(bytes(cursor.fetchone()[0])),manifest,digest,owned=owned)
        cursor.execute('SELECT truss.person_temporal_import_key_selection(%s,%s,%s,%s,%s)',
                       (args['document_id'],args['module_id'],args['record_id'],manifest['releaseId'],digest),prepare=False)
        selection=json.loads(bytes(cursor.fetchone()[0]));components=[]
        # Identity selection remains the existing accepted non-temporal key codec.
        for component in selection['components']:
            matching=tuple(v.value for v in args['values'] if v.name==component['name'])
            if len(matching)!=1 or not (type(matching[0]) is BooleanValue or type(matching[0]) is TextValue
                    and matching[0].kind in ('string','integer','decimal','binary')):
                raise ValueError('Complete original non-temporal primary components required')
            components.append(ObjectKeyComponent(property_id=component['propertyId'],definition_pin=component['definitionPin'],value=matching[0]))
        identity=ObjectKeySelection(type=ReadTypeReference(type_id=selection['type']['typeId'],definition_pin=selection['type']['definitionPin'],
            owner=QualifiedOwner(document_id=args['document_id'],module_id=args['module_id'])),key_number=selection['keyNumber'],
            key_definition_pin=selection['keyDefinitionPin'],key_encoding_profile=ProfilePin(**selection['keyEncodingProfile']),components=tuple(components))
        cursor.execute('SELECT truss.person_temporal_import_context(%s,%s)',(manifest['releaseId'],digest),prepare=False)
        builder=context_from_native(json.loads(bytes(cursor.fetchone()[0])),manifest,digest,owned=owned)
        payload=(builder.object_payload(args['values'],root=args['root'],source=args['source']) if owned
                 else builder.object_payload(args['values'],source=args['source']))
        cls=OwnedObjectImportRecord if owned else ObjectImportRecord
        return cls(identity=identity,payload=payload,payload_profile=builder.payload_profile)
    result=assembly._host._run_operation(args['transaction'],observe,function_call=True)
    return Ok(UnauthorizedPerson()) if _admission_refused(result) else result
