/** CONTRACT-009 administrative candidate; supplied transaction effects remain pending. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {Outcome,TransactionHandle} from './truss-execution-v0.1';
import type {ReceiptProtection} from './truss-request-receipt-v0.1';
export interface ReceiptProtectionUpdateRequest {
 readonly interfaceVersion:'truss-receipt-protection-update/0.1.0';
 readonly authorizedScopeIdentity:string;readonly requestId:string;
 readonly originalReceipt:ExactArtifact;
 readonly expected:{readonly state:'absent'} | {readonly state:'present';readonly protection:ExactArtifact};
 readonly procedureProfile:ProfilePin;readonly clockProfile:ProfilePin;readonly retentionProfile:ProfilePin;
 /** Authorized longer deadline request; never native current time or original commit proof. */
 readonly extension:{readonly state:'none'} | {readonly state:'requested';readonly protectedUntil:string};
}
export type ReceiptProtectionUpdateResult={readonly outcome:'updated'|'equal';readonly durability:'pending';
 readonly protection:ReceiptProtection;readonly updateEvidence:ExactArtifact} |
 {readonly outcome:'conflict';readonly protection?:never} |
 {readonly outcome:'unavailable';readonly reason:'authority'|'context'|'profile'|'clock'|'commit'|'receipt'|'observation'|'resource';readonly protection?:never};
export interface ReceiptProtectionObservationRequest {
 readonly interfaceVersion:'truss-receipt-protection-observation/0.1.0';
 readonly authorizedScopeIdentity:string;readonly requestId:string;
 readonly expectedProtection:ExactArtifact;readonly originalUpdateEvidence:ExactArtifact;
 readonly observationProfile:ProfilePin;
}
export type ReceiptProtectionObservation={readonly outcome:'current_committed';
 readonly protection:ReceiptProtection;readonly originalCommitObservation:ExactArtifact;
 readonly currentObservation:ExactArtifact} |
 {readonly outcome:'unavailable';readonly reason:'authority'|'context'|'profile'|'uncommitted'|'superseded'|'integrity'|'observation'|'resource';readonly protection?:never};
export interface ReceiptProtectionTooling {
 extendInTransaction(transaction:TransactionHandle,request:ReceiptProtectionUpdateRequest):Promise<Outcome<ReceiptProtectionUpdateResult>>;
 /** Fresh qualified observation; separate read-only coordinated profile required.
  * Never writes/changes a read-only scope or commits/upgrades original pending work. */
 observeProtection(transaction:TransactionHandle,request:ReceiptProtectionObservationRequest):Promise<Outcome<ReceiptProtectionObservation>>;
}
