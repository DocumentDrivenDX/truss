/** CONTRACT-009 administrative candidate; no published/native implementation. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {Outcome,TransactionHandle} from './truss-execution-v0.1';
import type {ExpiredRequestIdentity,ReceiptPurgeAssessment} from './truss-request-receipt-v0.1';
export interface ReceiptExpiryScopeRequest {
 readonly interfaceVersion:'truss-receipt-expiry-scope/0.1.0';
 readonly authorizedScopeIdentity:string;readonly requestId:string;readonly procedureProfile:ProfilePin;
}
export interface ReceiptPayloadPurgeRequest extends ReceiptExpiryScopeRequest {
 readonly expectedReceipt:ExactArtifact;readonly expectedProtection:ExactArtifact;readonly expectedLifecycleGeneration:string;
 /** No prior eligible assessment is a permit; independently reobserve all facts. */
}
export type ReceiptPayloadPurgeResult={readonly outcome:'purged';readonly durability:'pending';
 readonly identity:ExpiredRequestIdentity;readonly expiryEvidence:ExactArtifact} |
 {readonly outcome:'protected';readonly reason:'minimum_window'|'declared_window'|'original_event_retained';readonly identity?:never} |
 {readonly outcome:'conflict';readonly identity?:never} |
 {readonly outcome:'unavailable';readonly reason:'authority'|'context'|'profile'|'clock'|'commit'|'inventory'|'observation'|'resource';readonly identity?:never};
export interface ReceiptExpiryObservationRequest extends ReceiptExpiryScopeRequest {
 readonly expectedExpiredIdentity:ExactArtifact;readonly originalExpiryEvidence:ExactArtifact;
}
export type ReceiptExpiryObservation={readonly outcome:'current_committed';readonly identity:ExpiredRequestIdentity;
 readonly originalCommitObservation:ExactArtifact;readonly currentObservation:ExactArtifact} |
 {readonly outcome:'unavailable';readonly reason:'authority'|'context'|'profile'|'uncommitted'|'superseded'|'integrity'|'observation'|'resource';readonly identity?:never};
export interface ReceiptExpiryTooling {
 /** Selected writable/qualified read-only assessment; never a purge permit. */
 assessPurge(transaction:TransactionHandle,request:ReceiptExpiryScopeRequest):Promise<Outcome<ReceiptPurgeAssessment>>;
 /** Actual writable scope; effects/proof/compact state atomic and pending. */
 purgePayloadInTransaction(transaction:TransactionHandle,request:ReceiptPayloadPurgeRequest):Promise<Outcome<ReceiptPayloadPurgeResult>>;
 /** Fresh qualified cut; never commits original work or writes a read-only scope. */
 observeExpiry(transaction:TransactionHandle,request:ReceiptExpiryObservationRequest):Promise<Outcome<ReceiptExpiryObservation>>;
}
