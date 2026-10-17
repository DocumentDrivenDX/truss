"""Import batches on a connection and outer transactions owned by Truss."""
from __future__ import annotations
from typing import Literal
from hashlib import sha256
from dataclasses import replace
from .execution import Error,ExecutionFailure
from .imports import (ImportInput,OwnedImportInput,ImportReported,ImportCounts,ImportExecutionResult,ImportExecutionFailed,CommittedBatch,RolledBackBatch,
    CommitUnknownBatch,TransactionUnresolvedBatch)
from .preparation import CatalogDocument


class _EngineImportSession:
    def __init__(self,connection_info,statement_timeout_ms,operation_timeout_ms):
        self.connection_info=connection_info
        self.statement_timeout_ms=statement_timeout_ms
        self.operation_timeout_ms=operation_timeout_ms
        self.connection=None;self.host=None;self.last_settlement=None;self.reconnect=False;self.submitted=False

    def _open_connection(self):
        import psycopg
        return psycopg.connect(self.connection_info,autocommit=True,connect_timeout=10,
            options='-c statement_timeout='+str(self.statement_timeout_ms))

    def begin(self, *, isolation="read_committed"):
        if type(isolation) is not str or isolation not in ("read_committed", "repeatable_read"):
            raise ValueError("Supported engine transaction isolation required")
        import psycopg
        from psycopg import pq
        from .psycopg_host import adopt_psycopg_host
        if self.host is not None:
            reusable=self.host.detach()
            if not reusable:self.close()
            self.host=None
        if self.reconnect:self.close();self.reconnect=False
        if self.connection is None or self.connection.closed or self.connection.broken:
            self.connection=self._open_connection()
        if self.connection.info.transaction_status!=pq.TransactionStatus.IDLE:
            # Only this runner owns the outer transaction, including readmission.
            _,error=self.control('ROLLBACK',None)
            if error is not None:raise ValueError('Engine transaction cleanup unresolved')
        _,error=self.control('BEGIN ISOLATION LEVEL '+isolation.replace('_',' ').upper()+' READ WRITE',None)
        if error is not None:raise ValueError('Engine transaction start unavailable')
        self.host=adopt_psycopg_host(self.connection,statement_timeout_ms=self.statement_timeout_ms,
            operation_timeout_ms=self.operation_timeout_ms)
        adopted=self.host.adopt_transaction(isolation=isolation)
        if isinstance(adopted,Error):raise ValueError('Engine transaction adoption unavailable')
        return self.host,adopted.value

    def control(self,command,settlements):
        import psycopg
        from psycopg import pq
        from .psycopg_host import _Deadline
        deadline=_Deadline(self.connection,self.operation_timeout_ms)
        observed=None;error=None;cursor=None;self.submitted=False
        try:
            deadline.check();self.submitted=True;cursor=self.connection.execute(command,prepare=False)
            actual=cursor.statusmessage
            if (actual in ('COMMIT','ROLLBACK') and settlements is not None
                    and self.connection.info.transaction_status==pq.TransactionStatus.IDLE):
                # The acknowledgement is captured before result construction,
                # cancellation joining or cursor cleanup can fail.
                observed=settlements[actual];self.last_settlement=observed
            expected='BEGIN' if command.startswith('BEGIN ') else command
            if actual!=expected or self.connection.info.transaction_status!=(pq.TransactionStatus.INTRANS if expected=='BEGIN' else pq.TransactionStatus.IDLE):
                error=ExecutionFailure('execution_obligation','Engine transaction command refused')
        except Exception as failure:
            state=getattr(failure,'sqlstate',None)
            confirmed_rollback=(command=='COMMIT' and isinstance(failure,psycopg.Error)
                and failure.pgresult is not None and failure.pgresult.status==pq.ExecStatus.FATAL_ERROR
                and not self.connection.closed and not self.connection.broken
                and self.connection.info.transaction_status==pq.TransactionStatus.IDLE)
            if confirmed_rollback and settlements is not None:
                observed=settlements['ROLLBACK'];self.last_settlement=observed
                code='retry' if state in ('40001','40P01') else 'cancelled' if state=='57014' else 'execution_obligation'
                error=ExecutionFailure(code,'Engine batch commit rejected with confirmed rollback',
                    retry_scope='whole_transaction' if code=='retry' else 'none',sql_state=state)
            else:
                error=ExecutionFailure('commit_unknown' if command=='COMMIT' and self.submitted else 'transaction_unusable',
                    'Engine commit acknowledgement unavailable' if command=='COMMIT' else 'Engine transaction command unresolved',sql_state=state)
        finally:
            try:
                if not deadline.finish():
                    self.reconnect=True;error=ExecutionFailure('transaction_unusable','Engine cancellation completion unresolved')
                else:
                    try:deadline.check()
                    except TimeoutError:error=ExecutionFailure('cancelled','Engine transaction command deadline exceeded',sql_state=None if error is None else error.sql_state)
            except Exception:
                self.reconnect=True;error=ExecutionFailure('transaction_unusable','Engine cancellation completion unresolved')
            try:
                if cursor is not None:cursor.close()
            except Exception:error=ExecutionFailure('transaction_unusable','Engine transaction cursor cleanup unresolved')
        if command=='COMMIT' and self.submitted and observed is None:
            error=ExecutionFailure('commit_unknown','Engine commit acknowledgement unavailable',sql_state=None if error is None else error.sql_state)
        return observed,error

    def settle(self,batch,*,commit):
        if self.last_settlement is not None and self.last_settlement.batch_id==batch.batch_id:
            return self.last_settlement,None
        if self.reconnect:
            unresolved=TransactionUnresolvedBatch(batch_id=batch.batch_id,input_indices=batch.input_indices,recovery_reference=batch.batch_id)
            return unresolved,ExecutionFailure('transaction_unusable','Engine cancellation custody unresolved')
        from ._group_runtime import _bytes,_wire
        index=batch.input_indices
        evidence=lambda command:sha256(b'truss-engine-import-command/0.1\n'+_bytes({
            'command':command,'batch':_wire(batch),'backendPid':str(self.connection.info.backend_pid)})).hexdigest()
        committed=CommittedBatch(batch_id=batch.batch_id,input_indices=index,commit_evidence_sha256=evidence('COMMIT'))
        rolled=RolledBackBatch(batch_id=batch.batch_id,input_indices=index,rollback_evidence_sha256=evidence('ROLLBACK'))
        if self.host is not None:
            if not self.host.detach():
                self.reconnect=True
                # No new command can race an unresolved guarded cancellation.
                unresolved=TransactionUnresolvedBatch(batch_id=batch.batch_id,input_indices=index,recovery_reference=batch.batch_id)
                return unresolved,ExecutionFailure('transaction_unusable','Engine operation completion unresolved')
            self.host=None
        observed,error=self.control('COMMIT' if commit else 'ROLLBACK',{'COMMIT':committed,'ROLLBACK':rolled})
        if observed is not None:return observed,error
        unknown=CommitUnknownBatch(batch_id=batch.batch_id,input_indices=index,recovery_reference=batch.batch_id) if commit and self.submitted else TransactionUnresolvedBatch(batch_id=batch.batch_id,input_indices=index,recovery_reference=batch.batch_id)
        return unknown,error or ExecutionFailure('transaction_unusable','Engine settlement unavailable')

    def close(self):
        if self.host is not None:
            self.host.detach();self.host=None
        if self.connection is not None:
            try:self.connection.close()
            finally:self.connection=None


def run_import_batches(input: ImportInput | OwnedImportInput,*,connection_info: str,documents: tuple[CatalogDocument,...],bun_executable: str='bun',
        statement_timeout_ms: int=2000,operation_timeout_ms: int=5000) -> ImportExecutionResult[Literal['engine_owned']]:
    """Own a fresh psycopg connection and READ COMMITTED import batches.

    Legacy input uses one-record batches; owned input uses one atomic group.
    Input and document carriers are the same as caller-owned imports. All
    objects precede edges across the full input. Repetition creates or skips
    under current identity policy; it does not recover the original report.
    No supplied connection/transaction is committed and no batch is retried.
    """
    if (type(connection_info) is not str or not connection_info or type(statement_timeout_ms) is not int
        or not 1<=statement_timeout_ms<=60000 or type(operation_timeout_ms) is not int
        or not 1<=operation_timeout_ms<=60000):
        return ImportExecutionFailed(error=ExecutionFailure('invalid_transaction','Engine import connection or deadline options invalid'),report=None)
    from .catalog_runtime import _release,_pin_cursor
    from ._import_runtime import run_import
    session=_EngineImportSession(connection_info,statement_timeout_ms,operation_timeout_ms)
    result=None
    try:
        manifest,digest,_=_release();host,transaction=session.begin()
        if type(input) is OwnedImportInput:
            from ._owned_import_runtime import run_owned_import
            result=run_owned_import(host,transaction,input,documents,manifest,digest,_pin_cursor,bun_executable=bun_executable)
            if isinstance(result,ImportReported):
                report=result.report;settlement_error=None;batches=()
                disposition='pending'
                if report.batches:
                    batch=report.batches[0]
                    settled,settlement_error=session.settle(batch,commit=batch.disposition=='pending')
                    batches=(settled,);disposition=settled.disposition
                created=report.counts.created_pending
                counts=replace(report.counts,created_pending='0',
                    created_committed=created if disposition=='committed' else '0',
                    created_rolled_back=created if disposition=='rolled_back' else '0',
                    created_commit_unknown=created if disposition=='commit_unknown' else '0',
                    created_transaction_unresolved=created if disposition=='transaction_unresolved' else '0')
                report=replace(report,execution='engine_owned',batches=batches,counts=counts,
                    status='interrupted' if settlement_error is not None else 'processed')
                result=ImportReported(report=report) if settlement_error is None else ImportExecutionFailed(error=settlement_error,report=report)
        else:
            result=run_import(host,transaction,input,documents,manifest,digest,_pin_cursor,
                bun_executable=bun_executable,_engine=session)
    except Exception:
        result=ImportExecutionFailed(error=ExecutionFailure('transaction_unusable','Engine import connection or control unavailable'),report=None)
    finally:
        try:session.close()
        except Exception:
            prior=getattr(result,'error',None)
            error=prior if prior is not None and prior.code=='commit_unknown' else ExecutionFailure('transaction_unusable','Engine connection cleanup unresolved')
            result=ImportExecutionFailed(error=error,report=getattr(result,'report',None))
    return result
