/** CONTRACT-003 candidate; planner statistics are not integrity guarantees. */
import type {ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
export interface StatisticsJobIdentity {
  readonly interfaceVersion: 'truss-statistics-job/0.1.0';
  readonly installationId: string;
  readonly acceptedCatalogRevision: string;
  readonly layoutProfile: ProfilePin;
  readonly bindingProfile: ProfilePin;
  readonly declarationIdentity: string;
  readonly definition: ExactArtifact;
  readonly target: {readonly schema: string; readonly relation: string; readonly statistics: string};
  readonly collectionProfile: ProfilePin;
}
export interface StatisticsAttemptIdentity {
  readonly job: StatisticsJobIdentity;
  readonly attemptId: string;
  readonly generation: string;
  readonly dispatcherProfile: ProfilePin;
}
export type StatisticsReadiness = {
  readonly state: 'declared'; readonly job: StatisticsJobIdentity;
} | {
  readonly state: 'queued' | 'building'; readonly attempt: StatisticsAttemptIdentity;
  readonly committedAcceptanceEvidenceSha256: string;
} | {
  readonly state: 'defined'; readonly attempt: StatisticsAttemptIdentity;
  readonly installedInventory: ExactArtifact;
  readonly observedAt: string;
  readonly collection: 'not_confirmed';
} | {
  readonly state: 'collected'; readonly attempt: StatisticsAttemptIdentity;
  readonly installedInventory: ExactArtifact;
  readonly collectionEvidence: ExactArtifact;
  readonly observedAt: string;
  readonly collectionOutcome: 'populated' | 'empty_qualified';
} | {
  readonly state: 'failed'; readonly attempt: StatisticsAttemptIdentity;
  readonly code: string; readonly outcomeEvidence: ExactArtifact;
  readonly physicalOutcome: 'absent' | 'defined' | 'unknown';
} | {
  readonly state: 'stale'; readonly job: StatisticsJobIdentity;
  readonly reason: 'installation' | 'catalog' | 'layout' | 'binding' | 'definition' | 'collection_profile' | 'inventory';
};
