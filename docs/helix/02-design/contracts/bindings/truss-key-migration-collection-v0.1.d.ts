/** TD-009 candidate bucket-source original collector custody, not native qualification. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {TypedIdentity} from './truss-history-v0.1';
import type {KeyMigrationAttempt,KeyMigrationBasis} from './truss-key-profile-migration-v0.1';
export type BucketMigrationSourceLocator={
 readonly kind:'live_binding';readonly identity:TypedIdentity;readonly localKeyNumber:string;
 readonly originalBinding:ExactArtifact;readonly originalDefinition:ExactArtifact;
 readonly projection:{readonly state:'held';readonly storageRowId:string;readonly originalRow:ExactArtifact} |
  {readonly state:'omitted';readonly originalMissingComponentReport:ExactArtifact};
} | {
 readonly kind:'reservation';readonly storageRowId:string;
 readonly originalStoreDefinition:ExactArtifact;readonly originalReservation:ExactArtifact;
};
export interface BucketMigrationCollectionEvidence {
 readonly interfaceVersion:'truss-key-migration-bucket-collection/0.1.0';
 readonly originalAttempt:KeyMigrationAttempt;readonly source:KeyMigrationBasis;
 readonly collectorProfile:ProfilePin;readonly entryIdentityProfile:ProfilePin;
 readonly originalInstalledInventory:ExactArtifact;
 readonly originalExclusion:ExactArtifact;readonly originalCut:ExactArtifact;
 readonly applicability:{readonly originalCatalog:ExactArtifact;readonly originalBindingInventory:ExactArtifact;
  readonly completeObjectDomain:ExactArtifact;readonly exactApplicabilityEvidence:ExactArtifact};
 /** Complete ordered correspondence; zero entries still needs both exhaustion witnesses. */
 readonly entries:readonly {readonly entryId:string;readonly locator:BucketMigrationSourceLocator;
  readonly sourceEntry:ExactArtifact}[];
 readonly exhaustion:{readonly live:ExactArtifact;readonly reservations:ExactArtifact};
 readonly completeScopeEvidence:ExactArtifact;
}
