/** ADR-005 persistence candidate; no accepted table or wire compatibility claim. */
import type {ProfilePin,ExactArtifact} from './truss-acceptance-input-v0.1';
import type {GroupSemanticInput} from './truss-group-input-v0.1';
import type {GroupSemanticResult} from './truss-group-result-v0.1';
import type {JournalEventReference} from './truss-group-result-v0.1';
import type {QualifiedOwner} from './truss-history-v0.1';
import type {SelectedMutationConfiguration} from './truss-mutation-configuration-v0.1';
export interface ReplayAuthorizationContext {
  readonly policyProfile: ProfilePin;
  /** Union of all before/after declaring and endpoint ownership contexts. */
  readonly requiredOwners: readonly [QualifiedOwner, ...QualifiedOwner[]];
  readonly retainedDefinitionPins: readonly [string, ...string[]];
}
export interface RequestReceipt {
  readonly interfaceVersion: 'truss-request-receipt/0.1.0';
  readonly authorizedScopeIdentity: string;
  readonly requestId: string;
  readonly canonicalProfile: ProfilePin;
  readonly semanticDomain: 'truss-group-input/0.1.0';
  readonly inputSha256: string;
  readonly input: GroupSemanticInput;
  readonly result: GroupSemanticResult;
  readonly authorization: ReplayAuthorizationContext;
  readonly originalExecutionRole: string;
  readonly originalExecutionConfiguration: SelectedMutationConfiguration;
  readonly creationClockProfile:ProfilePin;
  readonly createdAt: string;
  readonly retainUntil: string;
}

/** Separate administrative lifecycle, never a rewritten semantic result. */
export interface ReceiptProtection {
  readonly interfaceVersion: 'truss-receipt-protection/0.1.0';
  readonly authorizedScopeIdentity: string;
  readonly requestId: string;
  readonly clockProfile:ProfilePin;readonly retentionProfile:ProfilePin;
  readonly originalCommittedObservation:ExactArtifact;readonly originalClockEvidence:ExactArtifact;
  readonly firstConfirmedCommittedAt: string;
  readonly protectedUntil: string;
  readonly observationEvidenceSha256: string;
}
export interface ExpiredRequestIdentity {
  readonly interfaceVersion: 'truss-expired-request/0.1.0';
  readonly authorizedScopeIdentity: string;
  readonly requestId: string;
  readonly canonicalProfile: ProfilePin;
  readonly semanticDomain: 'truss-group-input/0.1.0';
  readonly inputSha256: string;
  readonly clockProfile:ProfilePin;readonly retentionProfile:ProfilePin;readonly expiryProcedureProfile:ProfilePin;
  /** Original registered minimal expiry evidence custody; never input/result payload. */
  readonly expiryEvidenceIdentity:string;
  readonly expiredAt: string;
  readonly expiryEvidenceSha256: string;
  readonly input?: never;
  readonly result?: never;
}
export type RetainedRequestState = {
  readonly state: 'complete'; readonly receipt: RequestReceipt;
} | {readonly state: 'expired'; readonly identity: ExpiredRequestIdentity};

/** Administrative assessment, not a transferable authorization to purge. */
export type ReceiptPurgeAssessment = {
  readonly outcome: 'protected';
  readonly reason: 'minimum_window' | 'declared_window' | 'original_event_retained';
} | {
  readonly outcome: 'unavailable';
  readonly reason: 'commit_observation_missing' | 'inventory_incomplete' |
    'clock_invalid' | 'profile_unsupported' | 'scope_unavailable';
} | {
  readonly outcome: 'eligible';
  readonly authorizedScopeIdentity: string;
  readonly requestId: string;
  readonly retentionProfile: ProfilePin;
  readonly assessedAt: string;
  readonly protectionEvidenceSha256: string;
  readonly eventInventory: {
    readonly kind: 'event_bearing';
    /** Exact distinct union of every operation result's event references. */
    readonly originalEvents: readonly [JournalEventReference, ...JournalEventReference[]];
    readonly absenceEvidenceSha256: string;
  } | {
    readonly kind: 'all_no_op';
    readonly originalEvents: readonly [];
    readonly replayWindowProfile: ProfilePin;
  };
};
