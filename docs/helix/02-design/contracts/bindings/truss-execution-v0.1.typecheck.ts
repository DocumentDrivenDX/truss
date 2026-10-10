/** Compile-time boundary examples only; no native/runtime qualification. */
import type { Parameter, RawCell, TransactionHandle, ExecutionFailure,
  StatementResult } from './truss-execution-v0.1';
const decimal: Parameter = {position: 1, carrier: 'decimal', text: '1.00'};
const nullParameter: Parameter = {position: 2, carrier: 'null'};
const cell: RawCell = {state: 'text', text: '9007199254740993'};
const retry: ExecutionFailure = {code: 'retry', retryScope: 'whole_transaction', message: 'restart'};
const unknownCommit: ExecutionFailure = {code: 'commit_unknown', retryScope: 'qualified_request_lookup', message: 'inspect'};
// @ts-expect-error exact numeric transport rejects host numbers
const rounded: Parameter = {position: 1, carrier: 'decimal', text: 1.00};
// @ts-expect-error null carrier has no text member
const ambiguousNull: Parameter = {position: 1, carrier: 'null', text: 'null'};
// @ts-expect-error raw numeric cells remain text
const numericCell: RawCell = {state: 'text', text: 9007199254740993};
// @ts-expect-error an ordinary object cannot manufacture a branded handle
const forged: TransactionHandle = {ownership: 'caller', isolation: 'read_committed', accessMode: 'read_only'};
// @ts-expect-error commit uncertainty cannot instruct blind transaction retry
const blindRetry: ExecutionFailure = {code: 'commit_unknown', retryScope: 'whole_transaction', message: 'bad'};
// @ts-expect-error exact affected-row count is text
const count: StatementResult = {columns: [], rows: [], affectedRows: 1, command: 'UPDATE'};
void [decimal, nullParameter, cell, retry, unknownCommit, rounded, ambiguousNull,
  numericCell, forged, blindRetry, count];

const requestFreeUnknownCommit:ExecutionFailure={code:'commit_unknown',retryScope:'none',message:'retain original attempt custody'};
void requestFreeUnknownCommit;
