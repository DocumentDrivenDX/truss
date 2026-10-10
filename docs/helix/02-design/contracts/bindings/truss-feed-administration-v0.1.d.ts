/** CONTRACT-006 candidate; administrative authority is established by the host. */
import type {ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
import type {ConsumerWorkerIdentity, ConsumerAppliedBoundary} from './truss-feed-worker-v0.1';
export type FeedAdministrationRequest = {
  readonly interfaceVersion: 'truss-feed-administration/0.1.0';
  readonly requestId: string;
  readonly procedureProfile: ProfilePin;
  readonly expectedWorker: ConsumerWorkerIdentity;
  readonly assertedReason: string;
} & ({
  readonly operation: 'begin_reseed';
  readonly expectedApplied: ConsumerAppliedBoundary;
  readonly seedAttemptId: string;
} | {
  readonly operation: 'remove_consumer';
  readonly expectedApplied: ConsumerAppliedBoundary;
  readonly removal: {readonly mode: 'fenced'; readonly downstreamFenceEvidence: ExactArtifact} |
    {readonly mode: 'withdraw_replay_protection'; readonly withdrawalEvidence: ExactArtifact};
});
export type FeedAdministrationResult = {
  readonly outcome: 'reseed_registered';
  readonly worker: ConsumerWorkerIdentity;
  readonly seedAttemptId: string;
  readonly preservedApplied: ConsumerAppliedBoundary;
  readonly auditEvidence: ExactArtifact;
} | {
  readonly outcome: 'removed';
  readonly retiredRegistrationId: string;
  readonly finalGeneration: string;
  readonly downstreamStatus: 'fenced' | 'unverified_abandoned';
  readonly auditEvidence: ExactArtifact;
} | {
  readonly outcome: 'conflict';
} | {
  readonly outcome: 'unavailable';
  readonly reason: 'authorization' | 'context' | 'fencing' | 'profile' | 'observation';
} | {
  readonly outcome: 'commit_unknown'; readonly recoveryReference: string;
};
/** Persist only successful semantic outcomes; response uncertainty is never an audit outcome. */
export type FeedAdministrationReceipt = {
  readonly interfaceVersion: 'truss-feed-administration-receipt/0.1.0';
  readonly sourceEpoch: string;
  readonly administrativeNamespace: string;
  readonly canonicalInputSha256: string;
  readonly actualDatabaseRole: string;
  readonly authorizationEvidence: ExactArtifact;
} & ({
 readonly request:Extract<FeedAdministrationRequest,{readonly operation:'begin_reseed'}>;
 readonly result:Extract<FeedAdministrationResult,{readonly outcome:'reseed_registered'}>;
} | {
 readonly request:Extract<FeedAdministrationRequest,{readonly operation:'remove_consumer'}>;
 readonly result:Extract<FeedAdministrationResult,{readonly outcome:'removed'}>;
});

/** Supplied-scope changes remain pending even when repeating a visible receipt. */
export type FeedPendingAdministrationResult = {
 readonly outcome:'reseed_registered';
 readonly receipt:Extract<FeedAdministrationReceipt,{readonly result:{readonly outcome:'reseed_registered'}}>;
 readonly durability:'pending';
} | {
 readonly outcome:'removed';
 readonly receipt:Extract<FeedAdministrationReceipt,{readonly result:{readonly outcome:'removed'}}>;
 readonly durability:'pending';
} | {readonly outcome:'conflict'} | {
 readonly outcome:'unavailable';
 readonly reason:'authorization'|'context'|'fencing'|'profile'|'observation';
};
export type FeedAdministrationObservation = {
 readonly outcome:'committed';readonly receipt:FeedAdministrationReceipt;
 readonly observation:ExactArtifact;
} | {
 readonly outcome:'unavailable';
 readonly reason:'authorization'|'context'|'uncommitted'|'integrity'|'retention'|'profile'|'observation';
 readonly receipt?:never;
};
export interface FeedAdministrativeTooling {
 applyInTransaction(transaction:import('./truss-execution-v0.1').TransactionHandle,
  request:FeedAdministrationRequest):Promise<import('./truss-execution-v0.1').Outcome<FeedPendingAdministrationResult>>;
 observeReceipt(transaction:import('./truss-execution-v0.1').TransactionHandle,
  receipt:FeedAdministrationReceipt):Promise<import('./truss-execution-v0.1').Outcome<FeedAdministrationObservation>>;
}
