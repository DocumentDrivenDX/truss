/** CONTRACT-006 candidate; invalidation alone does not prove safe cleanup. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {SeedActivationState,SeedAttemptIdentity} from './truss-seed-activation-v0.1';
import type {Outcome,TransactionHandle} from './truss-execution-v0.1';
export interface SeedInvalidationRequest {
 readonly interfaceVersion:'truss-seed-invalidation/0.1.0';
 readonly expected:Exclude<SeedActivationState,{readonly state:'active'|'abandoned'}>;
 readonly procedureProfile:ProfilePin;
 readonly assertedReason:string;
}
export type SeedInvalidationResult = {
 readonly outcome:'invalidated';readonly attempt:SeedAttemptIdentity;
 readonly durability:'pending';readonly invalidationEvidence:ExactArtifact;
} | {readonly outcome:'conflict'} | {
 readonly outcome:'unavailable';readonly reason:'authorization'|'context'|'generation'|'active'|'profile'|'observation';
};
export interface SeedAbandonmentRequest {
 readonly interfaceVersion:'truss-seed-abandonment/0.1.0';
 readonly attempt:SeedAttemptIdentity;
 readonly procedureProfile:ProfilePin;
 readonly committedInvalidation:ExactArtifact;
 /** Qualified native original-attempt containment and inactive-stage cleanup proof. */
 readonly downstreamContainment:ExactArtifact;
}
export type SeedAbandonmentResult = {
 readonly outcome:'abandoned'|'equal';
 readonly abandoned:Extract<SeedActivationState,{readonly state:'abandoned'}>;
 readonly durability:'pending';readonly evidence:ExactArtifact;
} | {readonly outcome:'conflict'} | {
 readonly outcome:'unavailable';readonly reason:'authorization'|'context'|'generation'|'active'|'containment'|'profile'|'observation';
 readonly abandoned?:never;
};
export interface SeedAbandonmentTooling {
 invalidateInTransaction(transaction:TransactionHandle,request:SeedInvalidationRequest):Promise<Outcome<SeedInvalidationResult>>;
 finishInTransaction(transaction:TransactionHandle,request:SeedAbandonmentRequest):Promise<Outcome<SeedAbandonmentResult>>;
}
