/** CONTRACT-006 host-owned application; source acknowledgment remains separate. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {FeedAssemblyAssessment,FeedIntervalCoverage} from './truss-feed-transaction-v0.1';
import type {WorkerInstallation,ApplicationProofSubmission} from './truss-feed-worker-v0.1';
export interface FeedApplicationRequest {
 readonly interfaceVersion:'truss-feed-application/0.1.0';
 readonly installation:Extract<WorkerInstallation,{readonly outcome:'installed'}>;
 readonly transaction:Extract<FeedAssemblyAssessment,{readonly state:'complete'}>;
 readonly applicationProfile:ProfilePin;
}
/** Source coverage remains untrusted until independent source and downstream admission. */
export interface FeedCoverageApplicationRequest {
 readonly interfaceVersion:'truss-feed-coverage-application/0.1.0';
 readonly installation:Extract<WorkerInstallation,{readonly outcome:'installed'}>;
 readonly coverage:FeedIntervalCoverage;
 readonly applicationProfile:ProfilePin;
}
export type FeedApplicationResult = {
 readonly outcome:'applied'|'equal';
 /** Submission is evidence for registered host verification, not a VerifiedApplication. */
 readonly proofSubmission:ApplicationProofSubmission;
 readonly committedApplicationEvidence:ExactArtifact;
} | {
 readonly outcome:'unavailable';
 readonly reason:'authorization'|'context'|'generation'|'prior'|'integrity'|'profile'|'resource';
 readonly proofSubmission?:never;
} | {
 readonly outcome:'commit_unknown';readonly recoveryReference:string;
 readonly originalAttemptEvidence:ExactArtifact;readonly proofSubmission?:never;
};
export interface HostFeedApplicationAdapter {
 readonly downstreamIdentity:string;
 readonly downstreamProfile:ProfilePin;
 readonly applicationProfile:ProfilePin;
 apply(request:FeedApplicationRequest):Promise<FeedApplicationResult>;
 /** Atomically persists complete coverage under the same native fence as apply. */
 advanceCoverage(request:FeedCoverageApplicationRequest):Promise<FeedApplicationResult>;
 reconcileApplication(recoveryReference:string):Promise<FeedApplicationResult>;
}
