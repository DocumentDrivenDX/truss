"""Draft import carriers and local consistency, not native import execution."""
from dataclasses import dataclass, field, fields
from typing import Generic, Literal, TypeAlias, TypeVar
from .contracts import ABSENT, Absent, ExactArtifact, ExactValue, ObjectKeySelection, ProfilePin, SelectedMutationConfiguration, TypedIdentity, _Carrier
from .execution import ExecutionFailure

@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectImportRecord(_Carrier):
    identity: ObjectKeySelection
    payload: ExactArtifact
    payload_profile: ProfilePin
    kind: Literal['object'] = field(default='object', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class EdgeImportIdentity(_Carrier):
    relationship_definition_pin: str
    source: TypedIdentity
    target: TypedIdentity

@dataclass(frozen=True, slots=True, kw_only=True)
class EdgeImportRecord(_Carrier):
    identity: EdgeImportIdentity
    payload: ExactArtifact
    payload_profile: ProfilePin
    kind: Literal['edge'] = field(default='edge', init=False)

ImportRecordInput: TypeAlias = ObjectImportRecord | EdgeImportRecord

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportCatalogPin(_Carrier):
    revision: str
    model_bundle_sha256: str

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportInput(_Carrier):
    layout_profile: ProfilePin
    import_profile: ProfilePin
    value_profile: ProfilePin
    catalog: ImportCatalogPin
    load_id: str
    asserted_origin: ExactValue
    records: tuple[ImportRecordInput, ...]
    interface_version: Literal['truss-import-input/0.1.0'] = field(default='truss-import-input/0.1.0', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportCreated(_Carrier):
    input_index: str
    batch_id: str
    identity: TypedIdentity
    version: str
    outcome: Literal['created'] = field(default='created', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportSkipped(_Carrier):
    input_index: str
    batch_id: str
    reason: Literal['live_identity', 'reserved_identity']
    identity: TypedIdentity | Absent = ABSENT
    outcome: Literal['skipped'] = field(default='skipped', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportRejected(_Carrier):
    input_index: str
    batch_id: str
    code: str
    path: str | Absent = ABSENT
    outcome: Literal['rejected'] = field(default='rejected', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportAttemptUnknown(_Carrier):
    input_index: str
    batch_id: str
    recovery_reference: str
    identity: TypedIdentity | Absent = ABSENT
    outcome: Literal['attempt_unknown'] = field(default='attempt_unknown', init=False)

ImportRecordOutcome: TypeAlias = ImportCreated | ImportSkipped | ImportRejected | ImportAttemptUnknown

@dataclass(frozen=True, slots=True, kw_only=True)
class CommittedBatch(_Carrier):
    batch_id: str
    input_indices: tuple[str, *tuple[str, ...]]
    commit_evidence_sha256: str
    disposition: Literal['committed'] = field(default='committed', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class PendingBatch(_Carrier):
    batch_id: str
    input_indices: tuple[str, *tuple[str, ...]]
    host_transaction_id: str
    disposition: Literal['pending'] = field(default='pending', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class RolledBackBatch(_Carrier):
    batch_id: str
    input_indices: tuple[str, *tuple[str, ...]]
    rollback_evidence_sha256: str
    disposition: Literal['rolled_back'] = field(default='rolled_back', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class CommitUnknownBatch(_Carrier):
    batch_id: str
    input_indices: tuple[str, *tuple[str, ...]]
    recovery_reference: str
    disposition: Literal['commit_unknown'] = field(default='commit_unknown', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionUnresolvedBatch(_Carrier):
    batch_id: str
    input_indices: tuple[str, *tuple[str, ...]]
    recovery_reference: str
    disposition: Literal['transaction_unresolved'] = field(default='transaction_unresolved', init=False)

ImportBatchDisposition: TypeAlias = CommittedBatch | PendingBatch | RolledBackBatch | CommitUnknownBatch | TransactionUnresolvedBatch

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportCounts(_Carrier):
    created_committed: str
    created_pending: str
    created_rolled_back: str
    created_commit_unknown: str
    created_transaction_unresolved: str
    attempt_unknown: str
    skipped: str
    rejected: str
    unprocessed: str

ImportExecution: TypeAlias = Literal['engine_owned', 'host_adopted', 'outer_engine_scope']
ImportStatus: TypeAlias = Literal['processed', 'interrupted']
Execution = TypeVar('Execution', bound=ImportExecution, covariant=True)
Status = TypeVar('Status', bound=ImportStatus, covariant=True)

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportReport(_Carrier, Generic[Execution, Status]):
    attempt_id: str
    input_count: str
    executed_catalog_revision: str
    import_profile: ProfilePin
    selected_configuration: SelectedMutationConfiguration
    input_sha256: str
    execution: Execution
    status: Status
    outcomes: tuple[ImportRecordOutcome, ...]
    batches: tuple[ImportBatchDisposition, ...]
    unprocessed_indices: tuple[str, ...]
    counts: ImportCounts
    interface_version: Literal['truss-import-report/0.1.0'] = field(default='truss-import-report/0.1.0', init=False)

EngineReport: TypeAlias = ImportReport[Literal['engine_owned'], ImportStatus]
ScopeReport: TypeAlias = ImportReport[Literal['host_adopted', 'outer_engine_scope'], ImportStatus]
Report = TypeVar('Report', bound=ImportReport[ImportExecution, ImportStatus], covariant=True)

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportReported(_Carrier, Generic[Report]):
    report: Report
    outcome: Literal['reported'] = field(default='reported', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportResourceLimited(_Carrier, Generic[Execution]):
    reason: Literal['candidate_bytes', 'report_bytes', 'operation_deadline']
    resource_profile: ProfilePin
    report: ImportReport[Execution, Literal['interrupted']]
    outcome: Literal['resource_limited'] = field(default='resource_limited', init=False)

    def __post_init__(self) -> None:
        _Carrier.__post_init__(self)
        if (self.report.status != 'interrupted'
            or any(type(item) is ImportAttemptUnknown for item in self.report.outcomes)
            or any(item.disposition in ('commit_unknown', 'transaction_unresolved') for item in self.report.batches)):
            raise ValueError('Resource-limited report must retain interrupted progress')

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportExecutionFailed(_Carrier, Generic[Report]):
    error: ExecutionFailure
    report: Report | None
    outcome: Literal['execution_failed'] = field(default='execution_failed', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportInvalid(_Carrier):
    diagnostic_profile: ProfilePin
    diagnostic: ExactArtifact
    outcome: Literal['invalid'] = field(default='invalid', init=False)

ImportExecutionResult: TypeAlias = ImportReported[ImportReport[Execution, ImportStatus]] | ImportResourceLimited[Execution] | ImportExecutionFailed[ImportReport[Execution, ImportStatus]] | ImportInvalid

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportConsistencyLimits(_Carrier):
    maximum_records: int
    maximum_decimal_digits: int
    maximum_text_units: int

    def __post_init__(self) -> None:
        _Carrier.__post_init__(self)
        if not (0 <= self.maximum_records <= 4096 and 1 <= self.maximum_decimal_digits <= 20 and 1 <= self.maximum_text_units <= 1_048_576):
            raise ValueError('Finite reduced consistency limits required')

@dataclass(frozen=True, slots=True, kw_only=True)
class ImportConsistency(_Carrier):
    result: Literal['consistent', 'invalid', 'resource']


def check_import_report_consistency(report: ImportReport[ImportExecution, ImportStatus], *, expected_input_count: str, limits: ImportConsistencyLimits) -> ImportConsistency:
    """Local accounting only, never writer/commit/authority evidence.

    Scope reports with host-confirmed commit are outside this selected subset.
    Bounds apply to this check, not prior carrier allocation or native ingress.
    """
    if type(report) is not ImportReport or type(limits) is not ImportConsistencyLimits or type(expected_input_count) is not str:
        return ImportConsistency(result='invalid')
    maximum = limits.maximum_records
    if (len(report.outcomes) + len(report.unprocessed_indices) > maximum
        or len(report.batches) > maximum):
        return ImportConsistency(result='resource')
    total = 0
    for batch in report.batches:
        total += len(batch.input_indices)
        if total > maximum: return ImportConsistency(result='resource')
    # Before hashing/conversion, walk the fixed carrier tree under text budget.
    budget = limits.maximum_text_units
    stack: list[object] = [report, expected_input_count]
    while stack:
        item = stack.pop()
        if type(item) is str:
            budget -= len(item)
            if budget < 0: return ImportConsistency(result='resource')
        elif isinstance(item, _Carrier):
            stack.extend(getattr(item, member.name) for member in fields(item))  # type: ignore[arg-type]
        elif type(item) is tuple:
            stack.extend(item)
    class DecimalLimit(Exception):
        pass
    def decimal(text: str) -> int:
        if type(text) is str and len(text) > limits.maximum_decimal_digits:
            raise DecimalLimit
        if (type(text) is not str or not text
                or not text.isascii() or not text.isdecimal() or len(text) > 1 and text[0] == '0'):
            raise ValueError('Canonical bounded decimal required')
        return int(text)
    try:
        count = decimal(expected_input_count)
        if count > maximum: return ImportConsistency(result='resource')
        if decimal(report.input_count) != count: return ImportConsistency(result='invalid')
        seen: dict[int, str] = {}
        previous = -1
        for outcome in report.outcomes:
            index = decimal(outcome.input_index)
            if index <= previous or index >= count: return ImportConsistency(result='invalid')
            seen[index] = outcome.batch_id
            previous = index
        previous = -1
        for text in report.unprocessed_indices:
            index = decimal(text)
            if index <= previous or index >= count or index in seen: return ImportConsistency(result='invalid')
            previous = index
        if len(seen) + len(report.unprocessed_indices) != count: return ImportConsistency(result='invalid')
        if report.status == 'processed' and report.unprocessed_indices: return ImportConsistency(result='invalid')
        covered: set[int] = set()
        batches: dict[str, ImportBatchDisposition] = {}
        for batch in report.batches:
            if batch.batch_id in batches: return ImportConsistency(result='invalid')
            if report.execution == 'engine_owned' and batch.disposition == 'pending': return ImportConsistency(result='invalid')
            if report.execution != 'engine_owned' and batch.disposition in ('committed', 'commit_unknown'): return ImportConsistency(result='invalid')
            batches[batch.batch_id] = batch
            for text in batch.input_indices:
                index = decimal(text)
                if index in covered or seen.get(index) != batch.batch_id: return ImportConsistency(result='invalid')
                covered.add(index)
        if covered != set(seen): return ImportConsistency(result='invalid')
        derived = {member.name: 0 for member in fields(ImportCounts)}
        derived['unprocessed'] = len(report.unprocessed_indices)
        for outcome in report.outcomes:
            key = 'created_' + batches[outcome.batch_id].disposition if type(outcome) is ImportCreated else outcome.outcome
            derived[key] += 1
        if any(decimal(getattr(report.counts, key)) != value for key, value in derived.items()):
            return ImportConsistency(result='invalid')
    except DecimalLimit:
        return ImportConsistency(result='resource')
    except ValueError:
        return ImportConsistency(result='invalid')
    return ImportConsistency(result='consistent')

__all__ = ['ImportCatalogPin', 'ObjectImportRecord', 'EdgeImportIdentity', 'EdgeImportRecord', 'ImportRecordInput', 'ImportInput', 'ImportCreated', 'ImportSkipped', 'ImportRejected', 'ImportAttemptUnknown', 'ImportRecordOutcome', 'CommittedBatch', 'PendingBatch', 'RolledBackBatch', 'CommitUnknownBatch', 'TransactionUnresolvedBatch', 'ImportBatchDisposition', 'ImportCounts', 'ImportExecution', 'ImportStatus', 'ImportReport', 'EngineReport', 'ScopeReport', 'ImportReported', 'ImportResourceLimited', 'ImportExecutionFailed', 'ImportInvalid', 'ImportExecutionResult', 'ImportConsistencyLimits', 'ImportConsistency', 'check_import_report_consistency']


def check_import_execution_shape(result: ImportExecutionResult[ImportExecution], *, expected_execution: ImportExecution) -> ImportConsistency:
    """Check runtime family correlation only; no progress/native verification."""
    if type(expected_execution) is not str or expected_execution not in ('engine_owned', 'host_adopted', 'outer_engine_scope'):
        return ImportConsistency(result='invalid')
    if isinstance(result, ImportInvalid):
        return ImportConsistency(result='consistent' if type(result) is ImportInvalid else 'invalid')
    if type(result) not in (ImportReported, ImportResourceLimited, ImportExecutionFailed):
        return ImportConsistency(result='invalid')
    if result.report is None:
        return ImportConsistency(result='consistent' if type(result) is ImportExecutionFailed else 'invalid')
    return ImportConsistency(result='consistent' if result.report.execution == expected_execution else 'invalid')

__all__ += ['check_import_execution_shape']
