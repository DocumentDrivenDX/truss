"""Public import consumer; preserves progress rather than wrapping Outcome."""
from typing import Literal, assert_type
from truss.contracts import ExactArtifact, ProfilePin
from truss.execution import ExecutionFailure
from truss.imports import ImportExecutionResult, ImportReport, ImportStatus, ImportExecutionFailed, ImportResourceLimited, ImportInvalid, EngineReport, ScopeReport

def engine(result: ImportExecutionResult[Literal['engine_owned']]) -> None:
    if result.outcome == 'reported':
        assert_type(result.report, ImportReport[Literal['engine_owned'], ImportStatus])
    elif result.outcome == 'resource_limited':
        assert_type(result.report, ImportReport[Literal['engine_owned'], Literal['interrupted']])
    elif result.outcome == 'execution_failed':
        assert_type(result.report, ImportReport[Literal['engine_owned'], ImportStatus] | None)
        assert_type(result.error, ExecutionFailure)
    else:
        assert_type(result, ImportInvalid)

def scope(result: ImportExecutionResult[Literal['host_adopted', 'outer_engine_scope']]) -> None:
    if result.outcome == 'reported': assert_type(result.report, ScopeReport)

def construct(report: EngineReport, interrupted: ImportReport[Literal['engine_owned'], Literal['interrupted']], error: ExecutionFailure, pin: ProfilePin, artifact: ExactArtifact) -> None:
    failure = ImportExecutionFailed(error=error, report=report)
    absent: ImportExecutionFailed[EngineReport] = ImportExecutionFailed(error=error, report=None)
    limited = ImportResourceLimited(reason='report_bytes', resource_profile=pin, report=interrupted)
    invalid = ImportInvalid(diagnostic_profile=pin, diagnostic=artifact)
    assert failure.report is not None and absent.report is None and limited.report.status == 'interrupted' and invalid.outcome == 'invalid'

from typing import assert_never
from truss.contracts import TypedIdentity, Absent
from truss.imports import ImportRecordOutcome, ImportBatchDisposition

def record(result: ImportRecordOutcome) -> None:
    if result.outcome == 'created':
        assert_type(result.identity, TypedIdentity)
        assert_type(result.version, str)
    elif result.outcome == 'skipped':
        assert_type(result.identity, TypedIdentity | Absent)
    elif result.outcome == 'rejected':
        assert_type(result.path, str | Absent)
    elif result.outcome == 'attempt_unknown':
        assert_type(result.recovery_reference, str)
    else:
        assert_never(result)

def batch(result: ImportBatchDisposition) -> None:
    if result.disposition == 'committed': assert_type(result.commit_evidence_sha256, str)
    elif result.disposition == 'pending': assert_type(result.host_transaction_id, str)
    elif result.disposition == 'rolled_back': assert_type(result.rollback_evidence_sha256, str)
    elif result.disposition == 'commit_unknown': assert_type(result.recovery_reference, str)
    elif result.disposition == 'transaction_unresolved': assert_type(result.recovery_reference, str)
    else: assert_never(result)
