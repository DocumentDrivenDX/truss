/** CONTRACT-003 candidate; acceptance report is never rewritten by a job. */
import type {ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
export interface IndexJobIdentity {
  readonly interfaceVersion: 'truss-index-job/0.1.0';
  readonly installationId: string;
  readonly acceptedCatalogRevision: string;
  readonly layoutProfile: ProfilePin;
  readonly bindingProfile: ProfilePin;
  readonly declarationIdentity: string;
  readonly definition: ExactArtifact;
  readonly target: {readonly schema: string; readonly relation: string; readonly index: string};
}
export interface IndexAttemptIdentity {
  readonly job: IndexJobIdentity;
  readonly attemptId: string;
  readonly generation: string;
  readonly dispatcherProfile: ProfilePin;
}
export type IndexReadiness = {
  readonly state: 'declared'; readonly job: IndexJobIdentity;
} | {
  readonly state: 'queued' | 'building'; readonly attempt: IndexAttemptIdentity;
  readonly committedAcceptanceEvidenceSha256: string;
} | {
  readonly state: 'ready'; readonly attempt: IndexAttemptIdentity;
  readonly observedAt: string;
  readonly installedInventory: ExactArtifact;
  readonly verificationProfile: ProfilePin;
} | {
  readonly state: 'failed'; readonly attempt: IndexAttemptIdentity;
  readonly code: string; readonly outcomeEvidence: ExactArtifact;
  readonly physicalOutcome: 'absent' | 'invalid_owned' | 'unknown';
} | {
  readonly state: 'stale'; readonly job: IndexJobIdentity;
  readonly reason: 'installation' | 'catalog' | 'layout' | 'binding' | 'definition' | 'inventory';
};
export interface IndexDispatchRequest {
  readonly job: IndexJobIdentity;
  readonly expectedGeneration: string;
  readonly committedAcceptanceEvidenceSha256: string;
}
