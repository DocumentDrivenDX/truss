/** CONTRACT-006 proposed initial registration; no fabricated applied boundary. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {FeedContext} from './truss-feed-observation-v0.1';
import type {ConsumerWorkerIdentity,ConsumerAppliedBoundary} from './truss-feed-worker-v0.1';
import type {Outcome,TransactionHandle} from './truss-execution-v0.1';
export interface FeedRegistrationRequest {
 readonly interfaceVersion:'truss-feed-registration/0.1.0';
 readonly context:FeedContext;
 readonly consumerId:string;
 readonly procedureProfile:ProfilePin;
 readonly downstreamProfile:ProfilePin;
}
export type FeedConsumerState = {
 readonly state:'awaiting_seed';readonly worker:ConsumerWorkerIdentity;
 /** Trusted native retention floor; cannot be caller-nominated. */
 readonly inclusiveProtectionXid:string;
 readonly protectionEvidence:ExactArtifact;
 readonly procedureProfile:ProfilePin;
 readonly downstreamProfile:ProfilePin;
 readonly applied?:never;
} | {
 readonly state:'active';readonly worker:ConsumerWorkerIdentity;
 readonly applied:ConsumerAppliedBoundary;
 readonly procedureProfile:ProfilePin;
 readonly downstreamProfile:ProfilePin;
};
export type FeedRegistrationResult = {
 readonly outcome:'registered';
 readonly consumer:Extract<FeedConsumerState,{readonly state:'awaiting_seed'}>;
 readonly durability:'pending';
} | {readonly outcome:'conflict'} | {
 readonly outcome:'unavailable';readonly reason:'authorization'|'context'|'profile'|'retention'|'observation'|'resource';
};
export type FeedRegistrationObservation = {
 readonly outcome:'current_committed';
 readonly consumer:Extract<FeedConsumerState,{readonly state:'awaiting_seed'}>;
 readonly observation:ExactArtifact;
} | {
 readonly outcome:'unavailable';
 readonly reason:'authorization'|'context'|'superseded'|'activated'|'uncommitted'|'retention'|'profile'|'observation';
 readonly consumer?:never;
};
export interface FeedConsumerRegistration {
 registerInTransaction(transaction:TransactionHandle,request:FeedRegistrationRequest):Promise<Outcome<FeedRegistrationResult>>;
 observeRegistration(transaction:TransactionHandle,consumer:Extract<FeedConsumerState,{readonly state:'awaiting_seed'}>):Promise<Outcome<FeedRegistrationObservation>>;
}
