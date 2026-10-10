/** Same-store physical mapping; no native custody is established by this declaration. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {KeyMigrationAttempt} from './truss-key-profile-migration-v0.1';
export interface HeldMigrationLocator {readonly state:'held';readonly storageRowId:string;readonly rowEvidence:ExactArtifact}
export interface OmittedMigrationLocator {readonly state:'omitted';readonly missingComponentEvidence:ExactArtifact}
export type MigrationLocatorEntry={readonly sourceEntryId:string} & ({
 readonly kind:'live'|'reservation';readonly action:'unchanged'|'replaced';
 readonly source:HeldMigrationLocator;readonly target:HeldMigrationLocator;
}|{readonly kind:'live';readonly action:'created';readonly source:OmittedMigrationLocator;readonly target:HeldMigrationLocator}
 |{readonly kind:'live';readonly action:'removed';readonly source:HeldMigrationLocator;readonly target:OmittedMigrationLocator}
 |{readonly kind:'live';readonly action:'omitted';readonly source:OmittedMigrationLocator;readonly target:OmittedMigrationLocator});
export interface KeyMigrationLocatorCorrespondence {
 readonly interfaceVersion:'truss-key-migration-locator-correspondence/0.1.0';readonly originalAttempt:KeyMigrationAttempt;
 readonly sourceInventory:ExactArtifact;readonly targetCorrespondence:ExactArtifact;readonly locatorProfile:ProfilePin;
 readonly entries:readonly MigrationLocatorEntry[];readonly originalObservation:ExactArtifact;readonly completeCorrespondenceEvidence:ExactArtifact;
}
