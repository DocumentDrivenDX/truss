"""Held private producer -> native stage -> original whole-batch inspection.

This is internal sequencing, not caller/source/current admission. The caller
owns verified child assets, the shared deadline and all native closing guards.
No result from this module may be released before those guards succeed.
"""
from ._current_disclosure_pipe import VERSION
from ._current_disclosure_wire import frame_digest,object_members
from ._owner_evidence_json import decode_owner_evidence_json,same_owner_evidence
from ._current_query_evaluation import wire


def evaluate_stage_inspect(child,deadline,initialize_bytes,evaluation_bytes,stage):
    """Run one held child. stage is the host's fixed private staging closure."""
    initial=decode_owner_evidence_json(initialize_bytes)
    evaluation=decode_owner_evidence_json(evaluation_bytes)
    receipt=frame_digest(initialize_bytes)
    if (initial.get('version')!=VERSION or initial.get('kind')!='initialize'
            or evaluation.get('version')!=VERSION or evaluation.get('kind')!='evaluate-disclosure'
            or evaluation.get('sourceReceipt')!=receipt
            or initial.get('requestId')==evaluation.get('requestId')):
        raise ValueError('Exact held disclosure request sequence required')
    def exchange(raw):
        deadline.check()
        response=child.exchange(raw,source_receipt=receipt)
        deadline.check()
        return response,decode_owner_evidence_json(response)
    _,initialized=exchange(initialize_bytes)
    if not same_owner_evidence(initialized,{'version':VERSION,'kind':'initialized',
            'requestId':initial['requestId'],'sourceReceipt':receipt}):
        raise ValueError('Exact held original initialization required')
    produced_raw,produced=exchange(evaluation_bytes)
    if (set(produced)!={'version','kind','requestId','sourceReceipt','result'}
            or produced['version']!=VERSION or produced['kind']!='disclosure-evaluated'
            or produced['requestId']!=evaluation['requestId'] or produced['sourceReceipt']!=receipt):
        raise ValueError('Exact held original evaluation required')
    result_raw=object_members(produced_raw)['result']
    result=produced['result']
    if (type(result) is not dict or result.get('version')!='umf.security.logical-disclosure-batch/0.1-candidate'
            or result.get('status')!='rendered' or result.get('complete') is not False
            or result.get('authority') is not False or type(result.get('batch')) is not dict):
        raise ValueError('Actual held rendered disclosure required')
    deadline.check()
    staged=stage(result_raw)
    deadline.check()
    # Preserve actual driver cells and original header tokens. Inspection is by
    # the same still-live UMF child, against its retained original batch/sources.
    request_id='native_inspection'
    if request_id in (initial['requestId'],evaluation['requestId']):
        raise ValueError('Distinct held inspection request required')
    prefix=wire({'version':VERSION,'kind':'inspect-native-disclosure','requestId':request_id,'sourceReceipt':receipt})
    inspect=prefix[:-1]+b',"batch":'+staged.reconstructed_batch+b'}'
    frame_digest(inspect)  # enforce inspection wire bound before any exchange
    _,inspected=exchange(inspect)
    expected={'version':VERSION,'kind':'native-disclosure-inspected','requestId':request_id,
        'sourceReceipt':receipt,'evaluationFrameSha256':frame_digest(evaluation_bytes),
        'inspectionFrameSha256':frame_digest(inspect),'status':'validated-disclosure',
        'complete':False,'authority':False}
    if not same_owner_evidence(inspected,expected):
        raise ValueError('Exact same-held-child whole disclosure inspection required')
    deadline.check()
    return staged
