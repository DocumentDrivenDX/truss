/** CONTRACT-006 candidate; source transition is separate from downstream commit. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {FeedConsumerState} from './truss-feed-registration-v0.1';
import type {SeedActivationState} from './truss-seed-activation-v0.1';
import type {SeedDownstreamActivationResult} from './truss-seed-downstream-adapter-v0.1';
import type {Outcome,TransactionHandle} from './truss-execution-v0.1';
export interface SeedConfirmationRequest {
 readonly interfaceVersion:'truss-seed-confirmation/0.1.0';
 readonly expectedConsumer:FeedConsumerState;
 readonly activation:Extract<SeedDownstreamActivationResult,{readonly outcome:'activated'}>;
 readonly confirmationProfile:ProfilePin;
}
export type SeedConfirmationResult = {
 readonly outcome:'confirmed'|'equal';
 readonly active:Extract<SeedActivationState,{readonly state:'active'}> & {
  readonly sourceConfirmation:{readonly state:'confirmed';readonly evidenceSha256:string};
 };
 /** Source confirmation effects are not durable until this scope commits. */
 readonly durability:'pending';
 readonly confirmationEvidence:ExactArtifact;
} | {readonly outcome:'conflict'} | {
 readonly outcome:'unavailable';
 readonly reason:'authorization'|'context'|'generation'|'activation'|'integrity'|'protection'|'profile'|'observation';
 readonly active?:never;
};
export interface SeedSourceConfirmation {
 confirmInTransaction(transaction:TransactionHandle,request:SeedConfirmationRequest):Promise<Outcome<SeedConfirmationResult>>;
}
