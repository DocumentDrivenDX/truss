/** CONTRACT-009/007 candidate in-transaction group facade. */
import type {GroupSemanticInput, RequestIdentity} from './truss-group-input-v0.1';
import type {GroupResponse, GroupSemanticResult} from './truss-group-result-v0.1';
import type {ProfilePin, ExactArtifact} from './truss-acceptance-input-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {Outcome, TransactionHandle} from './truss-execution-v0.1';
export type GroupRequestSelection = {readonly state:'none'} | {
  readonly state:'present'; readonly identity:RequestIdentity;
};
export type InTransactionGroupResponse = {
  readonly disposition:'applied'; readonly durability:'pending';
  readonly semantic:GroupSemanticResult;
} | Extract<GroupResponse,{readonly disposition:'replayed'}>;
export type GroupApplicationResult = {
  readonly outcome:'success'; readonly response:InTransactionGroupResponse;
} | {
  readonly outcome:'failed';
  readonly failure: {
    readonly code:'group_failed'; readonly operationIndex:string;
    readonly errorProfile:ProfilePin; readonly innerError:ExactArtifact;
  } | {
    readonly code:'invalid' | 'request_conflict';
    readonly diagnosticProfile:ProfilePin; readonly diagnostic:ExactArtifact;
  };
  readonly response?:never;
} | {
  readonly outcome:'unavailable';
  readonly reason:'profile' | 'receipt' | 'receipt_expired' | 'observation' | 'resource';
  readonly response?:never;
};
/** Request-none cannot observe replay/receipt outcomes; native failures remain in Outcome. */
type GroupFailure = Extract<GroupApplicationResult,{readonly outcome:'failed'}>['failure'];
export type RequestFreeGroupApplicationResult = {
  readonly outcome:'success';
  readonly response:Extract<InTransactionGroupResponse,{readonly disposition:'applied'}>;
} | {
  readonly outcome:'failed';
  readonly failure:Extract<GroupFailure,{readonly code:'group_failed'}> |
    (Omit<Extract<GroupFailure,{readonly code:'invalid'|'request_conflict'}>,'code'> &
      {readonly code:'invalid'});
  readonly response?:never;
} | {
  readonly outcome:'unavailable';
  readonly reason:'profile'|'observation'|'resource';
  readonly response?:never;
};
export interface GroupCapability {
  readonly selection:CapabilitySelection & {readonly family:'group'};
  applyInTransaction(transaction:TransactionHandle,input:GroupSemanticInput,
    request:Extract<GroupRequestSelection,{readonly state:'none'}>):Promise<Outcome<RequestFreeGroupApplicationResult>>;
  applyInTransaction(transaction:TransactionHandle,input:GroupSemanticInput,
    request:Extract<GroupRequestSelection,{readonly state:'present'}>):Promise<Outcome<GroupApplicationResult>>;
  /** An unresolved caller branch retains the full result union until narrowed. */
  applyInTransaction(transaction:TransactionHandle,input:GroupSemanticInput,
    request:GroupRequestSelection):Promise<Outcome<GroupApplicationResult>>;
}
export type GroupCapabilityResult = {
  readonly status:'ok'; readonly capability:GroupCapability;
} | {readonly status:'unavailable';readonly reason:'selection' | 'disposed'};
