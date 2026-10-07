/** CONTRACT-001 candidate administrative migration; no native implementation. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {RecoveryTargetContext} from './truss-recovery-registry-v0.1';
export interface KeyMigrationBasis {
 readonly layout:ProfilePin;readonly catalog:ExactArtifact;
 readonly encoding:ProfilePin;readonly bucket:ProfilePin;
 readonly installedPolicy:ExactArtifact;
}
export interface KeyProfileMigrationRequest {
 readonly interfaceVersion:'truss-key-profile-migration/0.1.0';
 readonly sourceEpoch:string;readonly installationId:string;
 readonly source:KeyMigrationBasis;readonly target:KeyMigrationBasis;
 readonly procedure:ProfilePin;readonly resource:ProfilePin;
 readonly conversion:{readonly state:'none'} | {
  readonly state:'selected';readonly profile:ProfilePin;
 };
 readonly targetPhysicalInventory:ExactArtifact;
 readonly transitionProfile:ProfilePin;
 readonly limits:{readonly inventoryRows:string;readonly inventoryBytes:string;
  readonly reportBytes:string;readonly workUnits:string};
}
export type KeyMigrationAttempt = Extract<RecoveryTargetContext,{readonly kind:'installed'}> & {
 readonly migrationAttemptId:string;readonly procedure:ProfilePin;
 readonly originalRequest:ExactArtifact;
};
/** Complete assessments remain captured observations, never reusable activation permits. */
export type KeyMigrationAssessment = {
 readonly state:'complete';readonly observation:ExactArtifact;
 readonly sourceInventory:ExactArtifact;readonly targetCorrespondence:ExactArtifact;
 readonly verdict:{readonly state:'collision_free'} | {
  readonly state:'blocked';readonly report:ExactArtifact;
  readonly reasons:readonly [
   'collision'|'unrepresentable_reservation'|'unrepresentable_live_key',
   ...('collision'|'unrepresentable_reservation'|'unrepresentable_live_key')[]
  ];
 };
} | {
 readonly state:'incomplete';
 readonly reason:'resource'|'authority'|'profile'|'custody'|'integrity';
 readonly diagnostics:ExactArtifact;
 readonly verdict?:never;readonly targetCorrespondence?:never;
};
export interface KeyMigrationCommit {
 readonly originalAttempt:KeyMigrationAttempt;
 readonly receipt:ExactArtifact;readonly commitObservation:ExactArtifact;
 readonly committedBinding:ExactArtifact;readonly installedInventory:ExactArtifact;
 readonly assessment:Extract<KeyMigrationAssessment,{readonly state:'complete'}> & {
  readonly verdict:{readonly state:'collision_free'};
 };
}
export type KeyMigrationStage = 'admission'|'exclusion'|'source_inventory'|'conversion'|
 'collision_assessment'|'target_staging'|'policy_verification'|'binding_switch'|'commit';
export type KeyProfileMigrationResult = {
 readonly outcome:'migrated';readonly commit:KeyMigrationCommit;
} | ({
 readonly outcome:'refused';
 readonly containment:{readonly phase:'pre_native'} | {
  readonly phase:'preflight_terminated';readonly originalAttempt:KeyMigrationAttempt;
  readonly terminationEvidence:ExactArtifact;
 };
 readonly commit?:never;
} & ({readonly reason:'authorization';readonly assessment?:never} | {
 readonly reason:'profile'|'changed'|'collision'|'representation'|'resource'|'registry'|'integrity';
 readonly assessment?:KeyMigrationAssessment;
})) | {
 readonly outcome:'rolled_back';readonly originalAttempt:KeyMigrationAttempt;
 readonly failedStage:KeyMigrationStage;readonly terminationEvidence:ExactArtifact;
 readonly commit?:never;
} | {
 readonly outcome:'commit_unknown';
 readonly originalAttempt:KeyMigrationAttempt;readonly originalEvidence:ExactArtifact;
 readonly recoveryReference:string;readonly commit?:never;
} | {
 readonly outcome:'recovery_required';
 readonly reason:'application_unknown'|'cleanup_unknown';
 readonly failedStage:KeyMigrationStage;
 readonly originalAttempt:KeyMigrationAttempt;readonly originalEvidence:ExactArtifact;
 readonly recoveryReference:string;readonly commit?:never;
};
export type KeyMigrationReconciliationResult = Exclude<KeyProfileMigrationResult,{
 readonly outcome:'refused'
}> | {
 readonly outcome:'observation_unavailable';
 readonly reason:'authorization'|'custody'|'profile'|'integrity'|'resource';
 readonly commit?:never;readonly originalAttempt?:never;
};
export interface KeyProfileMigrationTooling {
 /** Owns the administrative transaction; no host transaction or assessment permit accepted. */
 migrate(request:KeyProfileMigrationRequest):Promise<KeyProfileMigrationResult>;
 /** Reconcile original custody/attempt; never initiate replacement conversion. */
 reconcile(recoveryReference:string):Promise<KeyMigrationReconciliationResult>;
}

export interface KeyMigrationToolingSelection {
 readonly source:import('./truss-capability-readiness-v0.1').CapabilitySelection & {readonly family:'bootstrap'};
 readonly target:import('./truss-capability-readiness-v0.1').CapabilitySelection & {readonly family:'bootstrap'};
 readonly migrationProfile:ProfilePin;
}
export type KeyMigrationToolingConstructionResult = {
 readonly status:'ok';readonly value:KeyProfileMigrationTooling;
} | {readonly status:'error';
 readonly code:'disposed'|'unsupported_profile'|'incompatible_selection';
};
/** Inert source/target bootstrap transition binding; no inspection, migration or handle issuance. */
export declare function createKeyProfileMigrationTooling(
 assembly:import('./truss-reference-assembly-v0.1').ReferenceAssembly,
 selection:KeyMigrationToolingSelection
):KeyMigrationToolingConstructionResult;

/** Immutable row contents written atomically with the selected binding; not commit proof. */
export interface KeyMigrationReceipt {
 readonly interfaceVersion:'truss-key-migration-receipt/0.1.0';
 readonly receiptProfile:ProfilePin;readonly originalAttempt:KeyMigrationAttempt;
 readonly source:KeyMigrationBasis;readonly target:KeyMigrationBasis;
 readonly sourceInventory:ExactArtifact;readonly targetCorrespondence:ExactArtifact;
 readonly priorSelectedBinding:ExactArtifact;readonly resultingSelectedBinding:ExactArtifact;
 readonly installedInventory:ExactArtifact;
 /** Original transition input/output basis; no later feed manifest or commit observation. */
 readonly transition:ExactArtifact;
 readonly nativeSwitchEvidence:ExactArtifact;
}
