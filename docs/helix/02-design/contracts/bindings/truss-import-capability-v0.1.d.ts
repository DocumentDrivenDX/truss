/** CONTRACT-004/007 candidate import facade; progress survives execution failure. */
import type {ImportInput} from './truss-import-input-v0.1';
import type {ImportReport} from './truss-import-report-v0.1';
import type {ExecutionFailure, TransactionHandle, TransactionOptions} from './truss-execution-v0.1';
import type {ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
type EngineReport=ImportReport & {readonly execution:'engine_owned'};
type ScopeReport=ImportReport & {readonly execution:'host_adopted'|'outer_engine_scope'};
export type ImportExecutionResult<R extends ImportReport> = {
  readonly outcome:'reported';readonly report:R;
} | {
  readonly outcome:'resource_limited';
  readonly reason:'candidate_bytes'|'report_bytes'|'operation_deadline';
  readonly resourceProfile:ProfilePin;
  readonly report:R & {readonly status:'interrupted'};
} | {
  readonly outcome:'execution_failed';readonly error:ExecutionFailure;
  /** Null only when no writer submission occurred; never erases prior progress. */
  readonly report:R|null;
} | {
  readonly outcome:'invalid';readonly diagnosticProfile:ProfilePin;
  readonly diagnostic:ExactArtifact;readonly report?:never;
};
export interface ImportCapability {
  readonly selection:CapabilitySelection & {readonly family:'import'};
  runBatches(input:ImportInput,options:TransactionOptions & {readonly accessMode:'read_write'}):Promise<ImportExecutionResult<EngineReport>>;
  applyInTransaction(transaction:TransactionHandle,input:ImportInput):Promise<ImportExecutionResult<ScopeReport>>;
}
export type ImportCapabilityResult = {
  readonly status:'ok';readonly capability:ImportCapability;
} | {readonly status:'unavailable';readonly reason:'selection'|'disposed'};
