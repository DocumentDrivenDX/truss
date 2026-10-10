/** CONTRACT-001 migration inventory meaning; independent collector/custody required. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {TypedIdentity} from './truss-history-v0.1';
import type {TrussKeyBinding} from './truss-key-bindings-v0.1';
import type {KeyMigrationAttempt,KeyMigrationBasis} from './truss-key-profile-migration-v0.1';
export interface MigrationFullKey {
 readonly namespace:ExactArtifact;readonly key:ExactArtifact;
 readonly encoding:ProfilePin;
 readonly namespaceSha256:string;readonly keySha256:string;
}
interface MigrationSourceEntryBase {
 /** Inventory-local identity, stable only inside this original captured inventory. */
 readonly entryId:string;readonly binding:TrussKeyBinding;
 readonly localKeyNumber:string;readonly originalDefinition:ExactArtifact;
 readonly components:{readonly state:'preserved';readonly original:ExactArtifact} |
  {readonly state:'unavailable';readonly reason:'not_retained'};
}
export type MigrationSourceEntry=MigrationSourceEntryBase & ({
 readonly kind:'live';readonly identity:TypedIdentity;readonly recordVersion:string;
 readonly membership:{readonly state:'held';readonly fullKey:MigrationFullKey} |
  {readonly state:'omitted';readonly originalMissingComponentReport:ExactArtifact};
} | {
 readonly kind:'reservation';readonly originalReservation:ExactArtifact;
 readonly originalRecordIdentity:TypedIdentity;
 readonly fullKey:MigrationFullKey;
});
export interface KeyMigrationSourceInventory {
 readonly interfaceVersion:'truss-key-migration-source-inventory/0.1.0';
 readonly originalAttempt:KeyMigrationAttempt;readonly source:KeyMigrationBasis;
 readonly inventoryProfile:ProfilePin;
 /** Explicit address grammar; ordinal profile requires original collector/locator custody. */
 readonly entryIdentityProfile:ProfilePin;readonly entries:readonly MigrationSourceEntry[];
 readonly collection:{readonly procedure:ProfilePin;readonly observation:ExactArtifact;
  readonly rawEvidence:readonly [ExactArtifact,...ExactArtifact[]];
  readonly completeScopeEvidence:ExactArtifact};
}
export type MigrationTargetEntry={readonly sourceEntryId:string} & ({
 readonly state:'held';readonly fullKey:MigrationFullKey;
 readonly derivation:{readonly kind:'owner_encoder'|'exact_conversion'|'unchanged_bytes';
  readonly profile:ProfilePin;readonly evidence:ExactArtifact};
} | {readonly state:'omitted';readonly missingComponentReport:ExactArtifact} |
 {readonly state:'unrepresentable';readonly reason:'missing_components'|'unsupported_conversion'|'resource'|'invalid_target';
  readonly diagnostics:ExactArtifact});
export interface KeyMigrationTargetCorrespondence {
 readonly interfaceVersion:'truss-key-migration-target-correspondence/0.1.0';
 readonly originalAttempt:KeyMigrationAttempt;
 readonly sourceInventory:ExactArtifact;readonly target:KeyMigrationBasis;
 readonly correspondenceProfile:ProfilePin;
 readonly entries:readonly MigrationTargetEntry[];
 readonly completeCoverageEvidence:ExactArtifact;
}
export interface KeyMigrationConflictClass {
 readonly fullKey:MigrationFullKey;
 readonly sourceEntryIds:readonly [string,string,...string[]];
 readonly policy:ProfilePin;readonly evidence:ExactArtifact;
}
export interface KeyMigrationBlockedReport {
 readonly interfaceVersion:'truss-key-migration-blocked-report/0.1.0';
 readonly sourceInventory:ExactArtifact;readonly targetCorrespondence:ExactArtifact;
 readonly reportProfile:ProfilePin;
 readonly conflicts:readonly KeyMigrationConflictClass[];
 readonly unrepresentableEntryIds:readonly string[];
 readonly completeReportEvidence:ExactArtifact;
}

/** Exact bytes serialized in MigrationSourceEntry.components.original. */
export interface MigrationPreservedComponents {
 readonly interfaceVersion:'truss-key-migration-components/0.1.0';
 readonly captureProfile:ProfilePin;
 readonly identity:TypedIdentity;readonly recordVersion:string;
 readonly binding:TrussKeyBinding;readonly originalDefinition:ExactArtifact;
 readonly originalRecordEnvelope:ExactArtifact;
 readonly components:readonly [{
  readonly property:import('./truss-key-bindings-v0.1').KeyPropertyReference;
  readonly presence:import('./truss-history-v0.1').Presence;
 },...{
  readonly property:import('./truss-key-bindings-v0.1').KeyPropertyReference;
  readonly presence:import('./truss-history-v0.1').Presence;
 }[]];
}
