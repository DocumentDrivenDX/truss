/** CONTRACT-006 candidate; proof authority is host-established at runtime. */
import type {ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
import type {FeedContext} from './truss-feed-observation-v0.1';
import type {FeedTransactionBoundary, FeedCoverageBoundary, FeedProgressBoundary} from './truss-feed-transaction-v0.1';
export type ConsumerAppliedBoundary = {
  readonly state: 'seed';
  readonly context: FeedContext;
  readonly seedId: string;
  readonly activationEvidenceSha256: string;
} | {readonly state: 'transaction'; readonly boundary: FeedTransactionBoundary} |
  {readonly state: 'coverage'; readonly boundary: FeedCoverageBoundary};
export interface ConsumerWorkerIdentity {
  readonly context: FeedContext;
  readonly consumerId: string;
  /** Trusted registration identity prevents remove/recreate name reuse. */
  readonly registrationId: string;
  readonly generation: string;
}
export interface WorkerClaim {
  readonly interfaceVersion: 'truss-feed-worker/0.1.0';
  /** Exact original source acquisition procedure, preserved during confirmation. */
  readonly procedureProfile: ProfilePin;
  readonly worker: ConsumerWorkerIdentity;
  readonly sourceApplied: ConsumerAppliedBoundary;
  readonly downstreamProfile: ProfilePin;
}
export interface ApplicationProofSubmission {
  readonly interfaceVersion: 'truss-feed-application-proof/0.1.0';
  readonly worker: ConsumerWorkerIdentity;
  readonly downstreamIdentity: string;
  readonly prior: ConsumerAppliedBoundary;
  readonly applied: FeedProgressBoundary;
  readonly intervalEvidence: ExactArtifact;
  readonly committedApplicationEvidence: ExactArtifact;
}
declare const verifiedApplication: unique symbol;
/** Opaque host verification result, not a JSON-deserializable credential. */
export interface VerifiedApplication {
  readonly [verifiedApplication]: true;
  readonly proof: ApplicationProofSubmission;
  readonly verifierProfile: ProfilePin;
  readonly verificationEvidenceSha256: string;
}
export type ApplicationProofAssessment = {
  readonly outcome: 'verified'; readonly application: VerifiedApplication;
} | {
  readonly outcome: 'unavailable';
  readonly reason: 'authorization' | 'context' | 'generation' | 'integrity' | 'durability' | 'profile';
};
export interface ConsumerAcknowledgment {
  readonly worker: ConsumerWorkerIdentity;
  readonly expectedPrior: ConsumerAppliedBoundary;
  readonly application: VerifiedApplication;
}
export type WorkerInstallation = {
  readonly outcome: 'installed'; readonly worker: ConsumerWorkerIdentity;
  readonly downstreamApplied: ConsumerAppliedBoundary;
  readonly installationEvidenceSha256: string;
} | {
  readonly outcome: 'unavailable';
  readonly reason: 'authorization' | 'context' | 'generation' | 'profile' | 'durability';
  readonly worker?: never;
  readonly downstreamApplied?: never;
  readonly installationEvidenceSha256?: never;
};
