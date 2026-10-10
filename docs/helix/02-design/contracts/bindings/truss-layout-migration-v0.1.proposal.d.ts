/** CONTRACT-008 draft administrative handoff; no executable installer or admission. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {RecoveryTargetContext} from './truss-recovery-registry-v0.1';

export interface LayoutMigrationPin {
 readonly version:string;readonly bundleSha256:string;readonly inventorySha256:string;
}
/** An original registered route plus its source observations; never a reusable permit. */
export interface LayoutMigrationRequest {
 readonly interfaceVersion:'truss-layout-migration-request/0.1.0';
 readonly manifest:ExactArtifact;readonly routeId:string;
 readonly source:LayoutMigrationPin;readonly target:LayoutMigrationPin;
 readonly originalSourceObservation:ExactArtifact;
 readonly procedure:ProfilePin;readonly resource:ProfilePin;
 readonly transitionProfile:ProfilePin;
}
/** Reuses the installed recovery target; originalEvidence retains this domain/request. */
export type LayoutMigrationAttempt = Extract<RecoveryTargetContext,{readonly kind:'installed'}> & {
 readonly layoutMigrationAttemptId:string;
 readonly originalRequest:ExactArtifact;
 readonly procedure:ProfilePin;
};
/** Exact ordered step evidence prepared in the effects transaction; not commit proof. */
export interface LayoutMigrationStepEvidence {
 readonly stepId:string;
 readonly source:LayoutMigrationPin;readonly target:LayoutMigrationPin;
 readonly recipe:ExactArtifact;readonly procedure:ProfilePin;
 readonly preconditions:ExactArtifact;
 readonly actualEffects:ExactArtifact;
 readonly validation:ExactArtifact;
 readonly preservation:ExactArtifact;
}
/** Native retained body. Visibility/commit correspondence is admitted separately. */
export interface LayoutMigrationReceiptBody {
 readonly interfaceVersion:'truss-layout-migration-receipt/0.1.0';
 readonly originalAttempt:LayoutMigrationAttempt;
 readonly manifest:ExactArtifact;readonly routeId:string;
 readonly source:LayoutMigrationPin;readonly target:LayoutMigrationPin;
 readonly procedure:ProfilePin;readonly resource:ProfilePin;
 readonly transitionProfile:ProfilePin;
 readonly originalSourceObservation:ExactArtifact;
 readonly orderedSteps:readonly [LayoutMigrationStepEvidence,...LayoutMigrationStepEvidence[]];
 readonly targetObservation:ExactArtifact;
 readonly preservationEvidence:ExactArtifact;
 /** Proposed target publication prepared atomically; never an observed COMMIT. */
 readonly targetInstallation:ExactArtifact;
 readonly targetInventory:ExactArtifact;
}
export type LayoutMigrationStage = 'admission'|'exclusion'|'source_verification'|
 'steps'|'target_verification'|'publication'|'commit'|'committed_verification';
export interface LayoutMigrationCommit {
 readonly originalAttempt:LayoutMigrationAttempt;
 readonly source:LayoutMigrationPin;readonly target:LayoutMigrationPin;
 /** Exact serialized LayoutMigrationReceiptBody, independently admitted with commit evidence. */
 readonly receipt:ExactArtifact;
 readonly commitObservation:ExactArtifact;
 readonly committedInstallation:ExactArtifact;
 readonly committedInventory:ExactArtifact;
 readonly preservationEvidence:ExactArtifact;
}
export type LayoutMigrationResult = {
 readonly outcome:'migrated';readonly commit:LayoutMigrationCommit;
} | {
 readonly outcome:'already_applied';readonly commit:LayoutMigrationCommit;
 readonly currentVerification:ExactArtifact;
} | {
 readonly outcome:'refused';
 readonly reason:'authorization'|'registry'|'profile'|'resource'|'integrity'|'changed'|
  'unsupported_route'|'nontransactional_profile';
 readonly containment:{readonly phase:'pre_native'} | {
  readonly phase:'preflight_terminated';readonly originalAttempt:LayoutMigrationAttempt;
  readonly terminationEvidence:ExactArtifact;
 };
 readonly commit?:never;
} | {
 readonly outcome:'rolled_back';readonly originalAttempt:LayoutMigrationAttempt;
 readonly failedStage:LayoutMigrationStage;readonly terminationEvidence:ExactArtifact;
 readonly commit?:never;
} | {
 readonly outcome:'commit_unknown';readonly originalAttempt:LayoutMigrationAttempt;
 readonly originalEvidence:ExactArtifact;readonly recoveryReference:string;
 readonly commit?:never;
} | {
 readonly outcome:'recovery_required';readonly originalAttempt:LayoutMigrationAttempt;
 readonly reason:'application_unknown'|'cleanup_unknown';
 readonly failedStage:LayoutMigrationStage;
 readonly originalEvidence:ExactArtifact;readonly recoveryReference:string;
 readonly commit?:never;
} | {
 /** Confirmed commit survives unavailable/drifted post-commit readiness observation. */
 readonly outcome:'committed_unverified';readonly originalAttempt:LayoutMigrationAttempt;
 readonly commitObservation:ExactArtifact;readonly originalEvidence:ExactArtifact;
 readonly reason:'authorization'|'custody'|'profile'|'resource'|'integrity'|'drift';
 readonly recoveryReference:string;readonly commit?:never;
};
export type LayoutMigrationReconciliation = Exclude<LayoutMigrationResult,{
 readonly outcome:'refused'
}> | {
 readonly outcome:'observation_unavailable';
 readonly reason:'authorization'|'custody'|'profile'|'resource'|'integrity';
 readonly commit?:never;readonly originalAttempt?:never;
};
/** Read-only requests still resolve registered procedures and current authority. */
export interface LayoutMigrationInspection {
 readonly procedure:ProfilePin;readonly resource:ProfilePin;
}
export type LayoutMigrationUnavailableReason = 'authorization'|'custody'|'profile'|
 'resource'|'integrity'|'unsupported_installation';
/** Current observation only; never proof of a prior attempt's outcome. */
export type LayoutMigrationStatus = {
 readonly outcome:'observed';readonly layout:LayoutMigrationPin;
 readonly installation:ExactArtifact;readonly nativeObservation:ExactArtifact;
 readonly scope:'current_installation_observation_only';
} | {
 readonly outcome:'observation_unavailable';readonly reason:LayoutMigrationUnavailableReason;
 readonly layout?:never;readonly installation?:never;readonly nativeObservation?:never;
};
export interface LayoutMigrationVerificationRequest extends LayoutMigrationInspection {
 readonly expected:LayoutMigrationPin;
}
export type LayoutMigrationVerification = {
 readonly outcome:'matches';readonly expected:LayoutMigrationPin;
 readonly installation:ExactArtifact;readonly nativeObservation:ExactArtifact;
 readonly correspondence:ExactArtifact;readonly scope:'current_installation_verification_only';
} | {
 readonly outcome:'drift';readonly expected:LayoutMigrationPin;
 readonly nativeObservation:ExactArtifact;readonly differences:ExactArtifact;
 readonly scope:'current_installation_verification_only';
} | {
 readonly outcome:'observation_unavailable';readonly reason:LayoutMigrationUnavailableReason;
 readonly nativeObservation?:never;readonly correspondence?:never;
};
export interface LayoutMigrationTooling {
 /** Observe current original installation under one admitted read-only cut. */
 status(request:LayoutMigrationInspection):Promise<LayoutMigrationStatus>;
 /** Compare complete selected native inventory without repair or publication. */
 verify(request:LayoutMigrationVerificationRequest):Promise<LayoutMigrationVerification>;
 /** Explicit dedicated administrative transaction for the complete declared route. */
 apply(request:LayoutMigrationRequest):Promise<LayoutMigrationResult>;
 /** Read-only original attempt lookup; cannot resubmit a step or transition. */
 reconcile(recoveryReference:string):Promise<LayoutMigrationReconciliation>;
}
