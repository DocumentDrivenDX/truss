/** CONTRACT-006 proposed explicit fresh-attempt admission after abandonment. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {FeedConsumerState} from './truss-feed-registration-v0.1';
import type {SeedActivationState,SeedAttemptIdentity} from './truss-seed-activation-v0.1';
import type {Outcome,TransactionHandle} from './truss-execution-v0.1';
export interface SeedRestartRequest {
 readonly interfaceVersion:'truss-seed-restart/0.1.0';
 readonly expectedConsumer:FeedConsumerState;
 readonly abandoned:Extract<SeedActivationState,{readonly state:'abandoned'}>;
 readonly committedAbandonment:ExactArtifact;
 readonly procedureProfile:ProfilePin;
 readonly activationProfile:ProfilePin;
}
export type SeedRestartResult = {
 readonly outcome:'registered';readonly attempt:SeedAttemptIdentity;
 readonly preservedConsumer:FeedConsumerState;
 readonly durability:'pending';readonly admissionEvidence:ExactArtifact;
} | {readonly outcome:'conflict'} | {
 readonly outcome:'unavailable';readonly reason:'authorization'|'context'|'generation'|'abandonment'|'active_attempt'|'profile'|'protection'|'observation';
 readonly attempt?:never;
};
export type SeedRestartObservation = {
 readonly outcome:'current_committed';readonly attempt:SeedAttemptIdentity;
 readonly preservedConsumer:FeedConsumerState;
 readonly originalAdmission:ExactArtifact;
 readonly observation:ExactArtifact;
} | {
 readonly outcome:'unavailable';readonly reason:'authorization'|'context'|'generation'|'superseded'|'uncommitted'|'protection'|'profile'|'observation';
 readonly attempt?:never;
};
export interface SeedRestartTooling {
 restartInTransaction(transaction:TransactionHandle,request:SeedRestartRequest):Promise<Outcome<SeedRestartResult>>;
 observeRestart(transaction:TransactionHandle,admission:Extract<SeedRestartResult,{readonly outcome:'registered'}>):Promise<Outcome<SeedRestartObservation>>;
}
