"""Private Python3.11 operation-control design; not an implemented adapter.

These structural types confer no authority. The original admitted physical
producer must recognize every token by its private object-identity registry.
No token constructor, counter reset, SQL signature or public factory is defined.
This synchronous Python profile blocks through original native observation;
an asynchronous adapter needs a separately selected interface/profile.
"""
from typing import Literal, Protocol, TypeVar, TypedDict


class OperationControlReservation(Protocol):
    @property
    def _original_reservation(self) -> object: ...


class IssuedOperationOrdinal(Protocol):
    @property
    def _original_issued(self) -> object: ...
    @property
    def ordinal(self) -> str: ...


class BoundOperationControl(Protocol):
    @property
    def _original_bound(self) -> object: ...
    @property
    def ordinal(self) -> str: ...


class ConfirmedOperationControl(Protocol):
    @property
    def _original_confirmed(self) -> object: ...
    @property
    def ordinal(self) -> str: ...


class OperationControlRecovery(Protocol):
    @property
    def _original_recovery(self) -> object: ...


class Reserved(TypedDict):
    status: Literal['reserved']
    reservation: OperationControlReservation


class ReservationRefusal(TypedDict):
    status: Literal['refused']
    reason: Literal['custody', 'closed', 'resource', 'cancelled', 'profile']


class Bound(TypedDict):
    status: Literal['bound']
    control: BoundOperationControl


class BindingRefusal(TypedDict):
    status: Literal['refused']
    reason: Literal['custody', 'closed', 'consumed', 'cancelled', 'profile']


class Confirmed(TypedDict):
    status: Literal['confirmed']
    control: ConfirmedOperationControl


class RefusedBeforeSubmission(TypedDict):
    status: Literal['refused_before_submission']
    reason: Literal['custody', 'closed', 'consumed', 'cancelled', 'profile']


class ConfirmedFailure(TypedDict):
    status: Literal['confirmed_failure']
    recovery: OperationControlRecovery


class Unavailable(TypedDict):
    status: Literal['unavailable']
    recovery: OperationControlRecovery


ControlReservationResult = Reserved | ReservationRefusal
OperationBindingResult = Bound | BindingRefusal
SavepointControlResult = Confirmed | RefusedBeforeSubmission | ConfirmedFailure | Unavailable


class OperationControlProducer(Protocol):
    def reserve_operation_control(self) -> ControlReservationResult:
        """Reserve forward/containment bounds before ordinal issuance; no SQL on refusal."""
        ...

    def bind_issued_operation(self, reservation: OperationControlReservation,
                             issued: IssuedOperationOrdinal) -> OperationBindingResult:
        """Consume original reservation/token once; every issued ordinal remains burnt."""
        ...

    def submit_operation_savepoint(self, control: BoundOperationControl) -> SavepointControlResult:
        """Consume before submission. Never retry; retain recovery on escaped failure.

        Only original correlated native observation can confirm. Command tags,
        ReadyForQuery T and a normal function return do not independently prove it.
        """
        ...


Input = TypeVar('Input', contravariant=True)
Result = TypeVar('Result', covariant=True)


class ConfirmedOperationAdmission(Protocol[Input, Result]):
    def admit_confirmed_operation(self, control: ConfirmedOperationControl,
                                 original_input: Input) -> Result:
        """Recheck original issuer/epoch/account/cycle/cancellation under arbitration.

        Consume permission before native invocation. Verify complete actor,
        installation/configuration and native issuer authority before effects.
        Refuse copied/foreign/expired/repeated tokens without invocation. Failure
        or rollback never restores permission. An ordinal string is not proof.
        """
        ...
