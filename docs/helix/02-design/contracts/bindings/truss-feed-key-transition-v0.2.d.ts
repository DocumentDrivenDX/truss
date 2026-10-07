/** CONTRACT-006 candidate extension; v0.1 manifests remain unchanged. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {KeyMigrationAttempt,KeyMigrationBasis} from './truss-key-profile-migration-v0.1';
import type {SelectedMutationConfiguration} from './truss-mutation-configuration-v0.1';
import type {FeedContext} from './truss-feed-observation-v0.1';
import type {FeedRecordKey,FeedManifestMember,FeedTransactionManifest} from './truss-feed-transaction-v0.1';
/** Constructed before receipt/manifest; never references its later containing artifacts. */
export interface FeedKeyTransitionBasis {
 readonly interfaceVersion:'truss-feed-key-transition-basis/0.2.0';
 readonly transitionProfile:ProfilePin;readonly context:FeedContext;
 readonly originalAttempt:KeyMigrationAttempt;
 readonly source:KeyMigrationBasis;readonly target:KeyMigrationBasis;
 readonly priorConfiguration:SelectedMutationConfiguration;
 readonly resultingConfiguration:SelectedMutationConfiguration;
 readonly priorSelectedBinding:ExactArtifact;readonly resultingSelectedBinding:ExactArtifact;
 readonly sourceInventory:ExactArtifact;readonly targetCorrespondence:ExactArtifact;
}
export interface FeedKeyTransitionFact {
 readonly interfaceVersion:'truss-feed-key-transition/0.2.0';
 /** Exact original FeedKeyTransitionBasis bytes, also named by the receipt. */
 readonly transition:ExactArtifact;
 /** Exact original receipt bytes; independently established producing commit remains external. */
 readonly receipt:ExactArtifact;
}
export type FeedRecordKeyV02=FeedRecordKey | {
 readonly kind:'key_profile_transition';
 readonly sourceEpoch:string;readonly installationId:string;readonly migrationAttemptId:string;
};
export interface FeedManifestMemberV02 extends Omit<FeedManifestMember,'key'> {
 readonly key:FeedRecordKeyV02;
}
export interface FeedTransactionManifestV02 extends Omit<FeedTransactionManifest,'interfaceVersion'|'members'> {
 readonly interfaceVersion:'truss-feed-transaction/0.2.0';
 readonly members:readonly [FeedManifestMemberV02,...FeedManifestMemberV02[]];
}

export interface FeedTransactionFragmentV02 extends Omit<
 import('./truss-feed-transaction-v0.1').FeedTransactionFragment,'manifest'> {
 readonly manifest:FeedTransactionManifestV02;
}
export interface FeedFragmentCursorV02 extends Omit<
 import('./truss-feed-transaction-v0.1').FeedFragmentCursor,'interfaceVersion'> {
 readonly interfaceVersion:'truss-feed-fragment-cursor/0.2.0';
}
export interface FeedFragmentRequestV02 extends Omit<
 import('./truss-feed-transaction-v0.1').FeedFragmentRequest,'manifest'|'continuation'> {
 readonly manifest:FeedTransactionManifestV02;
 readonly continuation:{readonly state:'first'} |
  {readonly state:'after';readonly cursor:FeedFragmentCursorV02};
}
export type FeedFragmentPageV02=Exclude<
 import('./truss-feed-transaction-v0.1').FeedFragmentPage,{readonly outcome:'available'}> | {
 readonly outcome:'available';
 readonly fragment:FeedTransactionFragmentV02 & {readonly records:readonly [
  {readonly ordinal:string;readonly payload:ExactArtifact},
  ...{readonly ordinal:string;readonly payload:ExactArtifact}[]
 ]};
 readonly continuation:{readonly state:'end'} |
  {readonly state:'more';readonly cursor:FeedFragmentCursorV02};
};
export type FeedAssemblyAssessmentV02=Exclude<
 import('./truss-feed-transaction-v0.1').FeedAssemblyAssessment,{readonly state:'complete'}> | {
 readonly state:'complete';readonly manifest:FeedTransactionManifestV02;
 readonly orderedPayloads:readonly [ExactArtifact,...ExactArtifact[]];
};
export type FeedDiscoveryResultV02=Exclude<
 import('./truss-feed-discovery-v0.1').FeedDiscoveryResult,{readonly outcome:'next'}> | {
 readonly outcome:'next';readonly manifest:FeedTransactionManifestV02;
 readonly safeWatermarkXid:string;readonly observation:ExactArtifact;
};

export interface FeedTransactionBoundaryV02 extends Omit<
 import('./truss-feed-transaction-v0.1').FeedTransactionBoundary,'domain'> {
 readonly domain:'complete-feed-transaction/0.2.0';
}
export interface FeedCoverageBoundaryV02 extends Omit<
 import('./truss-feed-transaction-v0.1').FeedCoverageBoundary,'domain'> {
 readonly domain:'complete-feed-coverage/0.2.0';
}
export type FeedProgressBoundaryV02=FeedTransactionBoundaryV02|FeedCoverageBoundaryV02;
export type ConsumerAppliedBoundaryV02={
 readonly state:'seed';readonly context:FeedContext;readonly seedId:string;
 readonly activationEvidenceSha256:string;
 /** Required original versioned baseline/binding closure; not a readiness flag. */
 readonly seedProfile:ProfilePin;
} | {readonly state:'transaction';readonly boundary:FeedTransactionBoundaryV02} |
 {readonly state:'coverage';readonly boundary:FeedCoverageBoundaryV02};
export interface FeedIntervalCoverageV02 extends Omit<
 import('./truss-feed-transaction-v0.1').FeedIntervalCoverage,'interfaceVersion'> {
 readonly interfaceVersion:'truss-feed-coverage/0.2.0';
}
export interface FeedDiscoveryRequestV02 extends Omit<
 import('./truss-feed-discovery-v0.1').FeedDiscoveryRequest,'interfaceVersion'|'after'> {
 readonly interfaceVersion:'truss-feed-discovery/0.2.0';
 readonly after:ConsumerAppliedBoundaryV02;
}

export interface ApplicationProofSubmissionV02 extends Omit<
 import('./truss-feed-worker-v0.1').ApplicationProofSubmission,'interfaceVersion'|'prior'|'applied'> {
 readonly interfaceVersion:'truss-feed-application-proof/0.2.0';
 readonly prior:ConsumerAppliedBoundaryV02;readonly applied:FeedProgressBoundaryV02;
}
declare const verifiedApplicationV02:unique symbol;
export interface VerifiedApplicationV02 {
 readonly [verifiedApplicationV02]:true;readonly proof:ApplicationProofSubmissionV02;
 readonly verifierProfile:ProfilePin;readonly verificationEvidenceSha256:string;
}
export type ApplicationProofAssessmentV02={
 readonly outcome:'verified';readonly application:VerifiedApplicationV02;
} | Extract<import('./truss-feed-worker-v0.1').ApplicationProofAssessment,{readonly outcome:'unavailable'}>;
export interface HostFeedProofVerifierV02 {
 readonly verifierProfile:ProfilePin;readonly downstreamProfile:ProfilePin;
 readonly registrationIdentity:string;
 assess(submission:ApplicationProofSubmissionV02):Promise<ApplicationProofAssessmentV02>;
 recognizes(application:VerifiedApplicationV02):boolean;
}
export interface FeedProofVerifierRegistrationV02 {
 readonly capabilityProfile:ProfilePin;readonly verifier:HostFeedProofVerifierV02;
}
export interface ConsumerAcknowledgmentV02 extends Omit<
 import('./truss-feed-worker-v0.1').ConsumerAcknowledgment,'expectedPrior'|'application'> {
 readonly expectedPrior:ConsumerAppliedBoundaryV02;readonly application:VerifiedApplicationV02;
}
export type FeedAcknowledgmentResultV02={
 readonly outcome:'advanced'|'equal';readonly applied:ConsumerAppliedBoundaryV02;
 readonly durability:'pending';
} | {readonly outcome:'conflict';readonly current:ConsumerAppliedBoundaryV02} |
 Extract<import('./truss-feed-capability-v0.1').FeedAcknowledgmentResult,{readonly outcome:'unavailable'}>;

export type WorkerInstallationV02=Exclude<
 import('./truss-feed-worker-v0.1').WorkerInstallation,{readonly outcome:'installed'}> | {
 readonly outcome:'installed';
 readonly worker:import('./truss-feed-worker-v0.1').ConsumerWorkerIdentity;
 readonly downstreamApplied:ConsumerAppliedBoundaryV02;
 readonly installationEvidenceSha256:string;
};
export interface FeedApplicationRequestV02 {
 readonly interfaceVersion:'truss-feed-application/0.2.0';
 readonly installation:Extract<WorkerInstallationV02,{readonly outcome:'installed'}>;
 readonly transaction:Extract<FeedAssemblyAssessmentV02,{readonly state:'complete'}>;
 readonly applicationProfile:ProfilePin;
}
export interface FeedCoverageApplicationRequestV02 {
 readonly interfaceVersion:'truss-feed-coverage-application/0.2.0';
 readonly installation:Extract<WorkerInstallationV02,{readonly outcome:'installed'}>;
 readonly coverage:FeedIntervalCoverageV02;readonly applicationProfile:ProfilePin;
}
export type FeedApplicationResultV02=Exclude<
 import('./truss-feed-application-adapter-v0.1').FeedApplicationResult,
 {readonly outcome:'applied'|'equal'}> | {
 readonly outcome:'applied'|'equal';readonly proofSubmission:ApplicationProofSubmissionV02;
 readonly committedApplicationEvidence:ExactArtifact;
};
export interface HostFeedApplicationAdapterV02 {
 readonly downstreamIdentity:string;readonly downstreamProfile:ProfilePin;
 readonly applicationProfile:ProfilePin;
 apply(request:FeedApplicationRequestV02):Promise<FeedApplicationResultV02>;
 advanceCoverage(request:FeedCoverageApplicationRequestV02):Promise<FeedApplicationResultV02>;
 reconcileApplication(recoveryReference:string):Promise<FeedApplicationResultV02>;
}

export interface SeedBaselineV02 extends Omit<
 import('./truss-seed-baseline-v0.1').SeedBaseline,'interfaceVersion'> {
 readonly interfaceVersion:'truss-seed-baseline/0.2.0';
 readonly keyBinding:{
  readonly basis:KeyMigrationBasis;readonly selectedBinding:ExactArtifact;
  readonly configuration:SelectedMutationConfiguration;
  readonly origin:{readonly kind:'bootstrap';readonly originalInitialization:ExactArtifact} |
   {readonly kind:'migration';readonly migrationAttemptId:string};
  /** Original admitted bootstrap or retained-cut anchor, never mutable current state. */
  readonly chainAnchor:ExactArtifact;
 };
 readonly keyTransitions:readonly {
  readonly producingXid:string;readonly fact:FeedKeyTransitionFact;
 }[];
}
export type SeedBaselineMemberIdentityV02=
 import('./truss-seed-baseline-v0.1').SeedBaselineMemberIdentity |
 {readonly kind:'key_binding';readonly sourceEpoch:string;readonly installationId:string} |
 {readonly kind:'key_profile_transition';readonly sourceEpoch:string;readonly installationId:string;readonly migrationAttemptId:string};
export interface SeedBaselineInventoryV02 extends Omit<
 import('./truss-seed-baseline-v0.1').SeedBaselineInventory,'interfaceVersion'|'entries'> {
 readonly interfaceVersion:'truss-seed-baseline-inventory/0.2.0';
 readonly entries:readonly {readonly ordinal:string;readonly identity:SeedBaselineMemberIdentityV02;
  readonly payloadSha256:string;readonly retainedOwnerEvidence:ExactArtifact}[];
}

export type SeedKeyBindingAnchor={
 readonly interfaceVersion:'truss-seed-key-binding-anchor/0.2.0';
 readonly anchorProfile:ProfilePin;readonly context:FeedContext;readonly installationId:string;
 readonly basis:KeyMigrationBasis;readonly selectedBinding:ExactArtifact;
 readonly configuration:SelectedMutationConfiguration;
} & ({
 readonly kind:'bootstrap';readonly originalInitialization:ExactArtifact;
 readonly originalInstalledInventory:ExactArtifact;
} | {
 readonly kind:'retained_cut';readonly originalSnapshotEvidence:ExactArtifact;
 readonly originalBindingState:ExactArtifact;readonly retainedHistoryHorizon:ExactArtifact;
 readonly archiveClosure:readonly [ExactArtifact,...ExactArtifact[]];
 readonly completeScopeEvidence:ExactArtifact;
});

export interface FeedCommittedApplicationEvidenceV02 extends Omit<
 import('./truss-feed-application-evidence-v0.1').FeedCommittedApplicationEvidence,
 'interfaceVersion'|'prior'|'applied'> {
 readonly interfaceVersion:'truss-feed-committed-application/0.2.0';
 readonly prior:ConsumerAppliedBoundaryV02;readonly applied:FeedProgressBoundaryV02;
}

export interface CompleteFeedFreshnessRequestV02 extends Omit<
 import('./truss-feed-freshness-v0.1').CompleteFeedFreshnessRequest,'interfaceVersion'> {
 readonly interfaceVersion:'truss-complete-feed-freshness/0.2.0';
}
export type CompleteFeedFreshnessResultV02=Exclude<
 import('./truss-feed-freshness-v0.1').CompleteFeedFreshnessResult,{readonly outcome:'observed'}> |
 (Omit<Extract<import('./truss-feed-freshness-v0.1').CompleteFeedFreshnessResult,
 {readonly outcome:'observed'}>,'sourceApplied'> & {readonly sourceApplied:ConsumerAppliedBoundaryV02});
export interface FeedCapabilityV02 {
 readonly selection:import('./truss-capability-readiness-v0.1').CapabilitySelection & {readonly family:'feed'};
 discoverNext(transaction:import('./truss-execution-v0.1').TransactionHandle,request:FeedDiscoveryRequestV02):
 Promise<import('./truss-execution-v0.1').Outcome<FeedDiscoveryResultV02>>;
 readFragment(transaction:import('./truss-execution-v0.1').TransactionHandle,request:FeedFragmentRequestV02):
 Promise<import('./truss-execution-v0.1').Outcome<FeedFragmentPageV02>>;
 observeFreshness(transaction:import('./truss-execution-v0.1').TransactionHandle,request:CompleteFeedFreshnessRequestV02):
 Promise<import('./truss-execution-v0.1').Outcome<CompleteFeedFreshnessResultV02>>;
 acknowledgeInTransaction(transaction:import('./truss-execution-v0.1').TransactionHandle,request:ConsumerAcknowledgmentV02):
 Promise<import('./truss-execution-v0.1').Outcome<FeedAcknowledgmentResultV02>>;
}
export type FeedCapabilityConstructionV02={readonly status:'ok';readonly value:FeedCapabilityV02} |
 {readonly status:'error';readonly code:'disposed'|'unsupported_profile'|'incompatible_selection'|'verifier_registration'};
/** Host setup only, inert; supplied registration is independently admitted at runtime. */
export declare function createFeedCapabilityV02(
 assembly:import('./truss-reference-assembly-v0.1').ReferenceAssembly,
 selection:import('./truss-capability-readiness-v0.1').CapabilitySelection & {readonly family:'feed'},
 verifierRegistration:FeedProofVerifierRegistrationV02
):FeedCapabilityConstructionV02;

/** Qualified procedure tuple for reuse of existing artifact-based seed protocol envelopes. */
export interface SeedProfileCompositionV02 {
 readonly interfaceVersion:'truss-seed-profile-composition/0.2.0';
 readonly compositionProfile:ProfilePin;
 readonly baselineProfile:ProfilePin;readonly inventoryProfile:ProfilePin;
 readonly anchorProfile:ProfilePin;readonly extractionProfile:ProfilePin;
 readonly visibilityProfile:ProfilePin;readonly stageProfile:ProfilePin;
 readonly activationProfile:ProfilePin;readonly confirmationProfile:ProfilePin;
 readonly downstreamProfile:ProfilePin;
 readonly originalQualificationEvidence:ExactArtifact;
}
