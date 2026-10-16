"""Negative import typing vectors; every bad marker must be rejected."""
from dataclasses import replace
from typing import Literal
from truss.contracts import ProfilePin, ExactArtifact
from truss.imports import ImportReport, ImportResourceLimited, EngineReport, ScopeReport, ImportSkipped, PendingBatch, ImportCounts, ImportInvalid, ImportInput

def invalid(processed: ImportReport[Literal['engine_owned'], Literal['processed']], scope: ScopeReport, pin: ProfilePin, artifact: ExactArtifact, counts: ImportCounts, input: ImportInput) -> None:
    ImportResourceLimited(reason='report_bytes', resource_profile=pin, report=processed)  # bad_processed_limited
    engine: EngineReport = scope  # bad_scope_as_engine
    ImportSkipped(input_index='0',batch_id='b',reason='live_identity',identity=None)  # bad_optional_identity
    PendingBatch(batch_id='b',input_indices=(),host_transaction_id='h')  # bad_empty_batch
    replace(counts,rejected=1)  # bad_numeric_count
    ImportInvalid(diagnostic_profile=pin,diagnostic=artifact,report=scope)  # bad_invalid_report
    replace(input,records=[])  # bad_mutable_records

def additional(pin: ProfilePin, counts: ImportCounts) -> None:
    from truss.execution import ExecutionFailure
    from truss.imports import ImportExecutionFailed, ImportRejected
    ImportResourceLimited(reason='report_bytes',resource_profile=pin,report=None)  # bad_null_resource_report
    ImportExecutionFailed(error=ExecutionFailure('invalid_transaction','fixture'))  # bad_missing_progress
    ImportRejected(input_index='0',batch_id='b',code='invalid',path=None)  # bad_null_optional_path
