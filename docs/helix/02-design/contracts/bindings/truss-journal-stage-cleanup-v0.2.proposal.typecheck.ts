import type {JournalStageSnapshotProposal,OperationSnapshotProposal,JournalStageCleanupCohortProposal,JournalStageCleanupResultProposal} from './truss-journal-stage-cleanup-v0.2.proposal';
declare const stage:JournalStageSnapshotProposal;
declare const parent:OperationSnapshotProposal;
declare const cohort:JournalStageCleanupCohortProposal;
declare const result:JournalStageCleanupResultProposal;
// @ts-expect-error Stage is not the original parent snapshot.
const parentConfusion:OperationSnapshotProposal=stage;
// @ts-expect-error Parent is not a stage snapshot.
const stageConfusion:JournalStageSnapshotProposal=parent;
// @ts-expect-error Empty stage set needs explicit evidence.
const empty:JournalStageCleanupCohortProposal={...cohort,stages:[],originalEmptyStageEvidence:undefined};
// @ts-expect-error Nonempty stage set cannot claim empty evidence.
const contradictory:JournalStageCleanupCohortProposal={...cohort,stages:[stage],originalEmptyStageEvidence:result.originalCohort};
// @ts-expect-error Pending cleanup cannot become committed by label.
const committed:JournalStageCleanupResultProposal={...result,durability:'committed'};
// @ts-expect-error Original cohort is not actual returned/absence result evidence.
const selectionAsResult:JournalStageCleanupResultProposal=cohort;
// @ts-expect-error Removed stages cannot contain parent snapshots.
const wrongRemoved:JournalStageCleanupResultProposal={...result,removedStages:[parent]};
void [parentConfusion,stageConfusion,empty,contradictory,committed,selectionAsResult,wrongRemoved];
