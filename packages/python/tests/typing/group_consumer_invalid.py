"""Negative static cases; each named line must produce a type error."""
from typing import Literal
from truss.contracts import TextValue, BooleanValue, ProfilePin
from truss.groups import RequestIdentity, GroupSuccess, AppliedCommitted, SameTransactionReplay, SameTransactionReplayEvidence, GroupSemanticResult, RequestFreeGroupApplicationResult, GroupUnavailable, Created, RequestConflict, GroupFailed

TextValue(kind='decimal', text=0.1)  # bad_float
BooleanValue(value=1)  # bad_bool_alias
RequestIdentity(authorized_scope_identity='scope', request_id='key', claimed_sha256=None)  # bad_optional_null
ProfilePin(identity='fixture', version=1, sha256='fixture')  # bad_pin_number

def negative(semantic: GroupSemanticResult, replay: SameTransactionReplay) -> None:
    GroupSuccess(response=AppliedCommitted(semantic=semantic))  # bad_applied_committed
    free: RequestFreeGroupApplicationResult = GroupSuccess(response=replay)  # bad_free_replay
    expired: GroupUnavailable[Literal['receipt_expired']] = GroupUnavailable(reason='receipt_expired')
    free = expired  # bad_free_expired

def more(semantic: GroupSemanticResult, item: Created, conflict: RequestConflict) -> None:
    from dataclasses import replace
    from truss.execution import TransactionHandle
    replace(item, events=())  # bad_empty_events
    free: RequestFreeGroupApplicationResult = GroupFailed(failure=conflict)  # bad_free_conflict
    handle = TransactionHandle(object(), 'key', 'read_committed', 'read_only')
    handle.ownership = 'caller'  # bad_mutable_handle
