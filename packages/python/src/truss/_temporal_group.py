# SPDX-License-Identifier: MIT OR Apache-2.0
"""Explicit PV1 group provider over the shared protected group engine."""
import json
from .contracts import ProfilePin
from .execution import Error,Ok
from .groups import UnauthorizedPerson,GroupUnavailable
from ._temporal_profiles import profiles,abi


def execute_group(assembly,operation,args):
    from .catalog_runtime import _release,_pin_cursor,_admission_refused
    from . import temporal as dto
    manifest,digest,_=_release()
    if operation=='group_context_in_transaction':
        def observe(cursor,observed):
            _pin_cursor(cursor)
            cursor.execute('SELECT truss.person_temporal_group_context(%s,%s)',(manifest['releaseId'],digest),prepare=False)
            value=json.loads(bytes(cursor.fetchone()[0]))
            return context_from_native(value,manifest,digest)
        result=assembly._host._run_operation(args['transaction'],observe,function_call=True)
        return Ok(UnauthorizedPerson()) if _admission_refused(result) else result
    if operation=='apply_in_transaction':
        from ._group_runtime import apply_group
        return apply_group(assembly._host,args['transaction'],args['input'],args['request'],args['documents'] or assembly._group_documents,
            manifest,digest,_pin_cursor,bun_executable=args['bun_executable'],_schema_state=assembly._record_schema_state,temporal=True)
    if operation=='recover_group_request_in_transaction':
        from ._group_runtime import recover_group_request
        return recover_group_request(assembly._host,args['transaction'],args['frame'],manifest,digest,_pin_cursor,temporal=True)
    from ._preview_runtime import validate_completion
    if operation=='complete_in_transaction':
        return validate_completion(assembly._host,args['transaction'],manifest,digest,_pin_cursor,temporal=True)
    return validate_completion(assembly._host,args['transaction'],manifest,digest,_pin_cursor,
        input=args['input'],documents=args['documents'] or assembly._group_documents,
        schema_state=assembly._record_schema_state,dry_run=True,temporal=True)


def context_from_native(value,manifest,digest):
    from . import temporal as dto
    expected=profiles()
    if (value['valueProfile']!=expected['valueProfile'] or value['mutationProfile']!=expected['mutationProfile']
        or value['queryAbi']!=abi() or value['releaseId']!=manifest['releaseId'] or value['releaseSha256']!=digest):
        raise ValueError('Actual native temporal group capability required')
    return dto.GroupRuntimeContext(layout_profile=ProfilePin(**value['layoutProfile']),
        mutation_profile=ProfilePin(**value['mutationProfile']),value_profile=ProfilePin(**value['valueProfile']),
        request_fingerprint_profile=ProfilePin(**value['requestFingerprintProfile']),
        authorized_scope_identity=value['authorizedScopeIdentity'],source_epoch=value['sourceEpoch'],
        history_profile=value['historyProfile'],query_abi=ProfilePin(**value['queryAbi']),
        release_id=value['releaseId'],release_sha256=value['releaseSha256'])
