"""Static consumer: no callable provider or native authority is supplied."""
from typing import Literal, assert_type
from truss.contracts import BooleanValue, TextValue, PresentValue, NullValue, Absent
from truss.execution import Error, Outcome, TransactionHandle
from truss.groups import GroupCapability, GroupSemanticInput, RequestNone, RequestPresent, GroupRequestSelection, RequestFreeGroupApplicationResult, GroupApplicationResult, CreateObject

def consumer(capability: GroupCapability, transaction: TransactionHandle,
             data: GroupSemanticInput, request: RequestPresent, undecided: GroupRequestSelection) -> None:
    free = capability.apply_in_transaction(transaction, data, RequestNone())
    assert_type(free, Outcome[RequestFreeGroupApplicationResult])
    keyed = capability.apply_in_transaction(transaction, data, request)
    assert_type(keyed, Outcome[GroupApplicationResult])
    unresolved = capability.apply_in_transaction(transaction, data, undecided)
    assert_type(unresolved, Outcome[GroupApplicationResult])
    if isinstance(free, Error):
        assert_type(free.error.retry_scope, Literal['none', 'whole_transaction', 'qualified_request_lookup'])

def exact(data: CreateObject) -> None:
    decimal = TextValue(kind='decimal', text='9007199254740993.00000000000000001')
    integer = TextValue(kind='integer', text='9007199254740993')
    explicit_null = PresentValue(value=NullValue())
    flag = BooleanValue(value=False)
    assert_type(data.alias, str | Absent)
    assert decimal.text and integer.text and explicit_null.present and not flag.value
