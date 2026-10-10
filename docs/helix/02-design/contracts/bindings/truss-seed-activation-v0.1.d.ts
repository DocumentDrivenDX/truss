/** CONTRACT-006 candidate; state labels alone prove no activation/durability. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
import type {ConsumerWorkerIdentity} from './truss-feed-worker-v0.1';
export interface SeedAttemptIdentity {
  readonly interfaceVersion: 'truss-seed-activation/0.1.0';
  readonly seedId: string;
  readonly worker: ConsumerWorkerIdentity;
  readonly activationProfile: ProfilePin;
}
/** Produced by completed extraction; cannot be required before it exists. */
export interface SeedStagePins {
  readonly visibilityManifestSha256: string;
  readonly baselineInventorySha256: string;
  readonly baselineSha256: string;
}
export type SeedActivationState = {
  readonly state: 'protected'; readonly attempt: SeedAttemptIdentity;
  readonly inclusiveReplayXmin: string; readonly protectionEvidenceSha256: string;
} | {
  readonly state: 'extracting'; readonly attempt: SeedAttemptIdentity;
  readonly inclusiveReplayXmin: string; readonly extractionEvidenceSha256: string;
} | {
  readonly state: 'staged'; readonly attempt: SeedAttemptIdentity;
  readonly pins: SeedStagePins;
  readonly inclusiveReplayXmin: string; readonly validationEvidenceSha256: string;
  readonly downstreamStageIdentity: string;
} | {
  readonly state: 'active'; readonly attempt: SeedAttemptIdentity;
  readonly pins: SeedStagePins;
  readonly inclusiveReplayXmin: string;
  readonly downstreamActivationEvidenceSha256: string;
  readonly sourceConfirmation: {readonly state: 'pending'} | {
    readonly state: 'confirmed'; readonly evidenceSha256: string;
  };
} | {
  readonly state: 'abandoned'; readonly attempt: SeedAttemptIdentity;
  readonly abandonmentEvidenceSha256: string;
};
