/** Precommit evidence grammar, never a commit observation or activation permit. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {KeyMigrationAttempt} from './truss-key-profile-migration-v0.1';
export interface MigrationGuardEffects {
 readonly namespaceSha256:string;readonly keySha256:string;
 readonly original:{readonly state:'existing';readonly generation:string}|{readonly state:'created'};
 readonly deletions:string;readonly insertions:string;readonly resultingGeneration:string;readonly actualEffectEvidence:ExactArtifact;
}
export interface KeyMigrationSwitchEvidence {
 readonly interfaceVersion:'truss-key-migration-switch-evidence/0.1.0';readonly originalAttempt:KeyMigrationAttempt;
 readonly procedure:ProfilePin;readonly originalExclusion:ExactArtifact;readonly locatorCorrespondence:ExactArtifact;
 readonly guardEffects:readonly MigrationGuardEffects[];readonly priorAdmission:ExactArtifact;readonly resultingAdmission:ExactArtifact;
 readonly installedInventory:ExactArtifact;readonly originalObservation:ExactArtifact;readonly completeEffectEvidence:ExactArtifact;
}
