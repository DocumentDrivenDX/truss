/** Structural rejection controls only; not runtime/native qualification. */
import type {KeyMigrationAssessment,KeyMigrationCommit,KeyProfileMigrationRequest,
 KeyProfileMigrationResult,KeyMigrationReconciliationResult} from '../../../02-design/contracts/bindings/truss-key-profile-migration-v0.1';
import type {ExactArtifact} from '../../../02-design/contracts/bindings/truss-acceptance-input-v0.1';
declare const artifact:ExactArtifact;
declare const request:KeyProfileMigrationRequest;
declare const committed:KeyMigrationCommit;
// @ts-expect-error Incomplete assessment cannot carry a collision-free verdict.
const incomplete:KeyMigrationAssessment={state:'incomplete',reason:'resource',diagnostics:artifact,verdict:{state:'collision_free'}};
// @ts-expect-error Missing correspondence cannot certify complete assessment.
const countOnly:KeyMigrationAssessment={state:'complete',observation:artifact,sourceInventory:artifact,verdict:{state:'collision_free'}};
// @ts-expect-error Captured assessment cannot bypass migrate's native reobservation.
const permit:KeyProfileMigrationRequest={...request,assessment:committed.assessment};
// @ts-expect-error Lost commit reply cannot carry a successful commit.
const unknown:KeyProfileMigrationResult={outcome:'commit_unknown',originalAttempt:committed.originalAttempt,originalEvidence:artifact,recoveryReference:'original',commit:committed};
// @ts-expect-error Unavailable observation cannot disclose an invented original attempt.
const unavailable:KeyMigrationReconciliationResult={outcome:'observation_unavailable',reason:'custody',originalAttempt:committed.originalAttempt};

// @ts-expect-error Cleanup uncertainty must preserve its reason and original failed stage.
const lostCleanup:KeyProfileMigrationResult={outcome:'recovery_required',originalAttempt:committed.originalAttempt,originalEvidence:artifact,recoveryReference:'original'};
// @ts-expect-error Rolled-back stage uses the declared protocol stages.
const inventedStage:KeyProfileMigrationResult={outcome:'rolled_back',originalAttempt:committed.originalAttempt,failedStage:'whatever',terminationEvidence:artifact};
