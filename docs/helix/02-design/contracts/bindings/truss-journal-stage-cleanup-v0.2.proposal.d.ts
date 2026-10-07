/** Unadopted private data shapes; never native authority or settlement tokens. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
export interface OperationSnapshotProposal {
 readonly kind:'operation';
 readonly fields:{readonly original_writer_xid:string;readonly operation_ordinal:string;readonly operation_kind:string;readonly phase:string;readonly effect_generation:string;readonly readiness_generation:string|null;readonly sealed_generation:string|null;readonly application_generation:string|null;readonly original_context_bytes_hex:string;readonly original_definition_bytes_hex:string;readonly original_input_bytes_hex:string;readonly original_prestate_bytes_hex:string;readonly admitted_candidate_bytes_hex:string;readonly effect_obligation_bytes_hex:string;readonly original_group_custody_bytes_hex:string;readonly application_result_bytes_hex:string|null};
}
export interface JournalStageSnapshotProposal {
 readonly interfaceVersion:'truss-journal-stage-snapshot/0.2.0-proposal';
 readonly kind:'journal-stage';
 readonly fields:{readonly original_writer_xid:string;readonly operation_ordinal:string;readonly stage_name:string;readonly stage_ordinal:string;readonly effect_generation:string;readonly body_bytes_hex:string};
}
interface CohortEvidence {
 readonly interfaceVersion:'truss-journal-stage-cleanup-cohort/0.2.0-proposal';readonly profile:ProfilePin;
 readonly originalOperationSnapshot:OperationSnapshotProposal;
 readonly originalInstallation:ExactArtifact;readonly originalLayout:ExactArtifact;readonly originalAdministrativeContext:ExactArtifact;readonly originalSettlement:ExactArtifact;readonly originalDependencyClosure:ExactArtifact;readonly originalResourceReservation:ExactArtifact;readonly originalStageMembership:ExactArtifact;
}
export type JournalStageCleanupCohortProposal=CohortEvidence & (
 {readonly stages:readonly [];readonly originalEmptyStageEvidence:ExactArtifact} |
 {readonly stages:readonly [JournalStageSnapshotProposal,...JournalStageSnapshotProposal[]];readonly originalEmptyStageEvidence?:never}
);
export interface JournalStageCleanupResultProposal {
 readonly interfaceVersion:'truss-journal-stage-cleanup-result/0.2.0-proposal';readonly durability:'pending-original-host-settlement';readonly profile:ProfilePin;
 readonly removedOperationSnapshot:OperationSnapshotProposal;readonly removedStages:readonly JournalStageSnapshotProposal[];
 readonly originalCohort:ExactArtifact;readonly originalAdministrativeContext:ExactArtifact;readonly originalCleanupAttempt:ExactArtifact;readonly originalRecheckObservation:ExactArtifact;readonly originalReturnedMembership:ExactArtifact;readonly completeChildAbsence:ExactArtifact;readonly completeParentAbsence:ExactArtifact;readonly preservedDependencyInventory:ExactArtifact;readonly capacityTransition:ExactArtifact;readonly completeCleanupEffectEvidence:ExactArtifact;
}
