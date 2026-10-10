/** CONTRACT-006 explicit tooling boundary; generation claims do not start workers. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {Outcome,TransactionHandle} from './truss-execution-v0.1';
import type {ConsumerWorkerIdentity,WorkerClaim} from './truss-feed-worker-v0.1';
export interface WorkerClaimRequest {
 readonly interfaceVersion:'truss-feed-worker-claim/0.1.0';
 readonly expectedWorker:ConsumerWorkerIdentity;
 readonly downstreamProfile:ProfilePin;
 readonly procedureProfile:ProfilePin;
}
export type PendingWorkerClaimResult = {
 readonly outcome:'claimed';readonly claim:WorkerClaim;
 readonly durability:'pending';readonly claimEvidence:ExactArtifact;
} | {readonly outcome:'conflict'} | {
 readonly outcome:'unavailable';readonly reason:'authorization'|'context'|'generation'|'profile'|'observation'|'resource';
};
export type WorkerClaimObservation = {
 readonly outcome:'current_committed';readonly claim:WorkerClaim;readonly observation:ExactArtifact;
} | {readonly outcome:'unavailable';readonly reason:'authorization'|'context'|'superseded'|'uncommitted'|'profile'|'observation';readonly claim?:never};
export interface FeedWorkerAdministration {
 acquireInTransaction(transaction:TransactionHandle,request:WorkerClaimRequest):Promise<Outcome<PendingWorkerClaimResult>>;
 /** Fresh qualified source observation; does not commit an original pending claim. */
 observeClaim(transaction:TransactionHandle,claim:WorkerClaim):Promise<Outcome<WorkerClaimObservation>>;
}
