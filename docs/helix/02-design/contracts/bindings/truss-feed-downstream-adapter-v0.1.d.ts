/** CONTRACT-006 host-owned adapter; Truss does not implement a universal downstream. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {WorkerInstallation} from './truss-feed-worker-v0.1';
import type {WorkerClaimObservation} from './truss-feed-worker-administration-v0.1';
export type CommittedWorkerClaim = Extract<WorkerClaimObservation,{readonly outcome:'current_committed'}>;
export type DownstreamInstallationResult = WorkerInstallation | {
 readonly outcome:'commit_unknown';
 readonly recoveryReference:string;
 readonly originalAttemptEvidence:ExactArtifact;
 readonly worker?:never;
 readonly downstreamApplied?:never;
 readonly installationEvidenceSha256?:never;
};
export interface HostFeedDownstreamAdapter {
 readonly downstreamIdentity:string;
 readonly downstreamProfile:ProfilePin;
 readonly installationProfile:ProfilePin;
 /** Independently validate source confirmation; atomically fence and read durable state. */
 installGeneration(claim:CommittedWorkerClaim):Promise<DownstreamInstallationResult>;
 /** Reconcile original uncertain attempt; never blindly reinstall or downgrade. */
 reconcileInstallation(recoveryReference:string):Promise<DownstreamInstallationResult>;
}
