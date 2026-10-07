/** CONTRACT-007 candidate: inert host custody; no runtime implementation. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {Outcome,TransactionHandle} from './truss-execution-v0.1';
import type {WorkerClaim} from './truss-feed-worker-v0.1';
import type {WorkerClaimRequest,PendingWorkerClaimResult,WorkerClaimObservation} from './truss-feed-worker-administration-v0.1';
import type {ConsumerAppliedBoundaryV02,WorkerInstallationV02,FeedProofVerifierRegistrationV02,
 HostFeedApplicationAdapterV02,SeedProfileCompositionV02} from './truss-feed-key-transition-v0.2';

export interface WorkerClaimV02 extends Omit<WorkerClaim,'interfaceVersion'|'sourceApplied'> {
 readonly interfaceVersion:'truss-feed-worker/0.2.0';
 readonly sourceApplied:ConsumerAppliedBoundaryV02;
}
export interface WorkerClaimRequestV02 extends Omit<WorkerClaimRequest,'interfaceVersion'> {
 readonly interfaceVersion:'truss-feed-worker-claim/0.2.0';
}
export type PendingWorkerClaimResultV02=Exclude<PendingWorkerClaimResult,{readonly outcome:'claimed'}> |
 (Omit<Extract<PendingWorkerClaimResult,{readonly outcome:'claimed'}>,'claim'> & {readonly claim:WorkerClaimV02});
export type WorkerClaimObservationV02=Exclude<WorkerClaimObservation,{readonly outcome:'current_committed'}> |
 (Omit<Extract<WorkerClaimObservation,{readonly outcome:'current_committed'}>,'claim'> & {readonly claim:WorkerClaimV02});
export interface FeedWorkerAdministrationV02 {
 acquireInTransaction(transaction:TransactionHandle,request:WorkerClaimRequestV02):Promise<Outcome<PendingWorkerClaimResultV02>>;
 observeClaim(transaction:TransactionHandle,claim:WorkerClaimV02):Promise<Outcome<WorkerClaimObservationV02>>;
}
export type DownstreamInstallationResultV02=WorkerInstallationV02 |
 Extract<import('./truss-feed-downstream-adapter-v0.1').DownstreamInstallationResult,{readonly outcome:'commit_unknown'}>;
export interface HostFeedDownstreamAdapterV02 {
 readonly downstreamIdentity:string;readonly downstreamProfile:ProfilePin;readonly installationProfile:ProfilePin;
 installGeneration(claim:Extract<WorkerClaimObservationV02,{readonly outcome:'current_committed'}>):Promise<DownstreamInstallationResultV02>;
 reconcileInstallation(recoveryReference:string):Promise<DownstreamInstallationResultV02>;
}
export interface FeedHostCompositionRequestV02 {
 readonly interfaceVersion:'truss-feed-host-composition/0.2.0';
 readonly registrationId:string;
 readonly target:{readonly databaseIdentity:string;readonly schema:string;readonly installationId:string;readonly sourceEpoch:string};
 readonly selection:CapabilitySelection & {readonly family:'feed'};
 readonly compositionProfile:ProfilePin;readonly originalQualificationEvidence:ExactArtifact;
 readonly verifier:FeedProofVerifierRegistrationV02;
 readonly downstreamInstallation:HostFeedDownstreamAdapterV02;
 readonly downstreamApplication:HostFeedApplicationAdapterV02;
 readonly seed:{readonly composition:SeedProfileCompositionV02;
  /** Reused artifact-based envelopes require exact v0.2 composition qualification. */
  readonly staging:import('./truss-seed-staging-v0.1').HostSeedStagingAdapter;
  readonly activation:import('./truss-seed-downstream-adapter-v0.1').HostSeedDownstreamAdapter;
 };
 /** Source operations are Truss-owned; these pins select their registered implementations. */
 readonly sourceProcedures:{readonly worker:ProfilePin;readonly registration:ProfilePin;
  readonly administration:ProfilePin;readonly extraction:ProfilePin;readonly confirmation:ProfilePin;
  readonly abandonment:ProfilePin;readonly restart:ProfilePin};
}
declare const hostCompositionV02:unique symbol;
/** Original assembly-bound custody; neither JSON nor a readiness/authorization credential. */
export interface FeedHostCompositionRegistrationV02 {
 readonly [hostCompositionV02]:true;
 readonly originalRequest:FeedHostCompositionRequestV02;
}
export type FeedHostCompositionRegistrationResultV02={readonly status:'ok';readonly registration:FeedHostCompositionRegistrationV02} |
 {readonly status:'error';readonly code:'disposed'|'invalid_configuration'|'incompatible_selection'|'registration_conflict'|'unsupported_profile';readonly registration?:never};
/** Synchronous all-or-nothing metadata admission; calls no supplied callback or native operation. */
export declare function registerFeedHostCompositionV02(assembly:ReferenceAssembly,
 request:FeedHostCompositionRequestV02):FeedHostCompositionRegistrationResultV02;
