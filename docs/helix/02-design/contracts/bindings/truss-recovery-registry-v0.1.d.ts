/** CONTRACT-007 candidate trusted host registry; no native recovery implementation. */
import type {ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
export type RecoveryTargetContext = {
  readonly databaseIdentity: string;
  readonly schemaName: string;
} & ({
  readonly kind: 'installed';
  readonly installationId: string;
  readonly sourceEpoch: string;
} | {
  readonly kind: 'bootstrap_attempt';
  readonly bootstrapAttemptId: string;
  readonly candidateInstallationId: string;
  readonly bundleSha256: string;
  readonly inventoryProfile: ProfilePin;
} | {
  readonly kind: 'namespace_observation';
  readonly observationAttemptId: string;
  readonly observationProfile: ProfilePin;
});
export interface RecoveryObligation {
  readonly obligationId: string;
  readonly assemblyId: string;
  readonly target: RecoveryTargetContext;
  readonly assemblyProfile: ProfilePin;
  readonly observationProfile: ProfilePin;
  readonly ownership: 'assembly_owned' | 'host_owned';
  /** Exact admitted attempt/resource evidence; contains no reusable handle. */
  readonly originalEvidence: ExactArtifact;
}
export interface RecoveryObservation {
  readonly obligationId: string;
  readonly observationId: string;
  readonly expectedPreviousObservationId: string | null;
  readonly observationProfile: ProfilePin;
  /** Claims below require profile admission of these exact bytes. */
  readonly evidence: ExactArtifact;
  readonly nativeTermination: 'unknown' | 'confirmed';
  readonly resourceRelease: 'unknown' | 'confirmed' | 'host_owned';
  readonly applicationDurability: 'unknown' | 'pending_host' | 'committed' | 'rolled_back';
}
export type RegistryResult<T> = {readonly status: 'ok'; readonly value: T} | {
  readonly status: 'unavailable';
  readonly reason: 'authority' | 'profile' | 'storage' | 'conflict' | 'missing';
};
export interface HostRecoveryRegistry {
  readonly profile: ProfilePin;
  readonly retention: 'process_lifetime' | 'restart_durable';
  /** Idempotent complete-evidence registration before native submission. */
  register(obligation: RecoveryObligation): Promise<RegistryResult<{readonly reference: string}>>;
  /** Serialized immutable append; observations cannot overwrite original evidence. */
  append(reference: string, observation: RecoveryObservation): Promise<RegistryResult<void>>;
  /** Host-authorized exact context lookup; never a permission to replay. */
  inspect(reference: string, context: RecoveryTargetContext): Promise<RegistryResult<{
    readonly obligation: RecoveryObligation;
    readonly observations: readonly RecoveryObservation[];
  }>>;
}
