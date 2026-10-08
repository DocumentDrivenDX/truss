/** CONTRACT-004/007 candidate standalone mutation facade; shared group semantics. */
import type {GroupOperation, GroupSemanticInput, ObjectReference} from './truss-group-input-v0.1';
import type {OperationResult} from './truss-group-result-v0.1';
import type {ProfilePin, ExactArtifact} from './truss-acceptance-input-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {Outcome, TransactionHandle} from './truss-execution-v0.1';
type StoredReference=Extract<ObjectReference,{readonly state:'stored'}>;
type StandaloneOwnership={readonly state:'rootless'} | {readonly state:'owned';readonly root:StoredReference};
export type SingleMutationOperation =
  (Omit<Extract<GroupOperation,{readonly operation:'create_object'}>,'alias'|'ownership'> & {readonly alias?:never;readonly ownership:StandaloneOwnership}) |
  (Omit<Extract<GroupOperation,{readonly operation:'create_edge'}>,'alias'|'source'|'target'> & {readonly alias?:never;readonly source:StoredReference;readonly target:StoredReference}) |
  (Omit<Extract<GroupOperation,{readonly operation:'update_object'}>,'target'|'ownershipChange'> & {readonly target:StoredReference;readonly ownershipChange?:StandaloneOwnership}) |
  (Omit<Extract<GroupOperation,{readonly operation:'update_edge'}>,'target'|'endpointChange'> & {readonly target:StoredReference;readonly endpointChange?:{readonly source:StoredReference;readonly target:StoredReference}}) |
  (Omit<Extract<GroupOperation,{readonly operation:'delete_object'|'delete_edge'}>,'target'> & {readonly target:StoredReference});
export interface MutationSemanticInput extends Omit<GroupSemanticInput,'interfaceVersion'|'operations'> {
  readonly interfaceVersion:'truss-mutation-input/0.1.0';
  readonly operation:SingleMutationOperation;
}
export type MutationApplicationResult = {
  readonly outcome:'success'; readonly result:OperationResult & {readonly alias?:never};
  readonly executedCatalogRevision:string;
  readonly layoutProfile:ProfilePin; readonly mutationProfile:ProfilePin;
  readonly durability:'pending';
} | {
  readonly outcome:'failed'; readonly code:string;
  readonly errorProfile:ProfilePin; readonly error:ExactArtifact;
  readonly result?:never;
} | {
  readonly outcome:'unavailable'; readonly reason:'profile'|'observation'|'resource';
  readonly result?:never;
};
export interface MutationCapability {
  readonly selection:CapabilitySelection & {readonly family:'mutation'};
  applyInTransaction(transaction:TransactionHandle,input:MutationSemanticInput):Promise<Outcome<MutationApplicationResult>>;
}
export type MutationCapabilityResult = {
  readonly status:'ok';readonly capability:MutationCapability;
} | {readonly status:'unavailable';readonly reason:'selection'|'disposed'};
