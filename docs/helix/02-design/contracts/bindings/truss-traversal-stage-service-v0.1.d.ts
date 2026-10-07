/** CONTRACT-004/007 candidate host store boundary; no graph expansion or SQL compiler. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
import type {TraversalRequest,TraversalStageHandle,TraversalResumeRequest,TraversalNextPageRequest,TraversalReleaseRequest,TraversalReleaseResult} from './truss-direct-traversal-v0.1';
export interface TraversalStageConfiguration {
 readonly selection:CapabilitySelection & {readonly family:'direct_read'};
 readonly storeProfile:ProfilePin;readonly privateStateProfile:ProfilePin;
 readonly resourceProfile:ProfilePin;readonly originalComposition:ExactArtifact;
 readonly retention:'process_lifetime'|'restart_durable';
}
export interface TraversalStageCounters {
 readonly examinedEdges:string;readonly pathStates:string;
 readonly retainedBytes:string;readonly activeWorkMilliseconds:string;
}
export type TraversalStageOpenRequest={readonly intent:'create';readonly transaction:TransactionHandle;
 readonly request:TraversalRequest;readonly originalQuery:ExactArtifact;readonly initialState:ExactArtifact;
 readonly reservationBytes:string} |
 {readonly intent:'resume';readonly transaction:TransactionHandle;readonly request:TraversalResumeRequest} |
 {readonly intent:'page';readonly transaction:TransactionHandle;readonly request:TraversalNextPageRequest};
declare const traversalLeaseBrand:unique symbol;
export interface TraversalStageLease {
 readonly [traversalLeaseBrand]:true;readonly handle:TraversalStageHandle;
 readonly workVersion:string;readonly phase:'working'|'sealed';
 readonly originalQuery:ExactArtifact;readonly privateState:ExactArtifact;
 readonly counters:TraversalStageCounters;readonly reservationBytes:string;
 readonly accountingVersion:string;
}
export type TraversalStageOpenResult={readonly outcome:'opened';readonly lease:TraversalStageLease} |
 {readonly outcome:'unavailable';readonly reason:'ownership'|'context'|'profile'|'version'|'resource'|'integrity';readonly lease?:never};
export interface TraversalStagePublication {
 readonly expectedWorkVersion:string;readonly expectedAccountingVersion:string;readonly nextState:ExactArtifact;
 readonly phase:'working'|'sealed';readonly counters:TraversalStageCounters;
 readonly reservationBytes:string;
}
export type TraversalStagePublishResult={readonly outcome:'stored';readonly workVersion:string;readonly evidence:ExactArtifact;readonly lease:TraversalStageLease} |
 {readonly outcome:'conflict'} |
 {readonly outcome:'unresolved';readonly recoveryReferences:readonly [string,...string[]]};
declare const traversalWorkPermitBrand:unique symbol;
export interface TraversalWorkPermit {
 readonly [traversalWorkPermitBrand]:true;readonly accountingVersion:string;
 readonly originalLease:TraversalStageLease;
}
export interface TraversalWorkReservation {
 readonly expectedAccountingVersion:string;
 readonly maximumIncrements:{readonly examinedEdges:string;readonly pathStates:string;readonly activeWorkMilliseconds:string};
 readonly maximumReservationBytes:string;
}
export type TraversalWorkAdmission={readonly outcome:'reserved';readonly permit:TraversalWorkPermit}|
 {readonly outcome:'unavailable';readonly reason:'version'|'resource'|'ownership';readonly permit?:never};
export interface TraversalWorkCompletion {
 readonly actualIncrements:TraversalWorkReservation['maximumIncrements'];
 readonly retainedBytes:string;readonly reservationBytes:string;
 readonly originalCompletionEvidence:ExactArtifact;
}
export type TraversalWorkSettlement={readonly outcome:'accounted';readonly accountingVersion:string;
 readonly counters:TraversalStageCounters;readonly evidence:ExactArtifact}|
 {readonly outcome:'unresolved';readonly recoveryReferences:readonly [string,...string[]]};
/** Private host state storage, reservation and issuer custody; engine owns expansion semantics. */
export interface HostTraversalStageService {
 readonly configuration:TraversalStageConfiguration;
 reserveWork(lease:TraversalStageLease,reservation:TraversalWorkReservation):Promise<TraversalWorkAdmission>;
 settleWork(permit:TraversalWorkPermit,completion:TraversalWorkCompletion):Promise<TraversalWorkSettlement>;
 open(request:TraversalStageOpenRequest):Promise<TraversalStageOpenResult>;
 observePublication(originalRecoveryReference:string):Promise<{readonly outcome:'observed';readonly evidence:ExactArtifact}|{readonly outcome:'unavailable';readonly reason:'ownership'|'observation'|'integrity'}>;
 publish(lease:TraversalStageLease,publication:TraversalStagePublication):Promise<TraversalStagePublishResult>;
 validateDisclosure(lease:TraversalStageLease,originalSealedState:ExactArtifact):Promise<
 {readonly outcome:'valid';readonly evidence:ExactArtifact}|{readonly outcome:'unavailable'}>;
 closeLease(lease:TraversalStageLease):Promise<{readonly outcome:'closed'}|
 {readonly outcome:'unresolved';readonly recoveryReferences:readonly [string,...string[]]}>;
 /** Invalidate before containment/deletion; does not need a live data transaction. */
 release(request:TraversalReleaseRequest):Promise<TraversalReleaseResult>;
}
declare const traversalRegistrationBrand:unique symbol;
export interface TraversalStageRegistration {
 readonly [traversalRegistrationBrand]:true;readonly configuration:TraversalStageConfiguration;
}
export type TraversalStageRegistrationResult={readonly status:'ok';readonly registration:TraversalStageRegistration}|
 {readonly status:'error';readonly code:'disposed'|'unsupported_profile'|'incompatible_selection'|'already_registered';readonly registration?:never};
/** Inert exact original-object registration; never invokes the service or establishes readiness. */
export declare function registerTraversalStageService(assembly:ReferenceAssembly,
 configuration:TraversalStageConfiguration,service:HostTraversalStageService):TraversalStageRegistrationResult;
