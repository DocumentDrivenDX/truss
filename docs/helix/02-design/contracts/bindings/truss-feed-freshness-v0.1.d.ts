/** CONTRACT-006 complete-feed observation; native fact-clock profile remains gated. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {Backlog} from './truss-feed-observation-v0.1';
import type {ConsumerWorkerIdentity,ConsumerAppliedBoundary} from './truss-feed-worker-v0.1';
export interface CompleteFeedFreshnessRequest {
 readonly interfaceVersion:'truss-complete-feed-freshness/0.1.0';
 readonly worker:ConsumerWorkerIdentity;
 readonly observationProfile:ProfilePin;
}
export type CompleteFeedFreshnessResult = {
 readonly outcome:'observed';
 readonly worker:ConsumerWorkerIdentity;
 /** Confirmed source acknowledgment; downstream may be durably ahead. */
 readonly sourceApplied:ConsumerAppliedBoundary;
 readonly checkpointUpdatedAt:string;
 readonly observedAt:string;
 readonly safeWatermarkXid:string;
 readonly publishable:Backlog;
 readonly held:Backlog;
 readonly observationProfile:ProfilePin;
 readonly factClockProfile:ProfilePin;
 readonly observation:ExactArtifact;
 readonly limitations:readonly string[];
} | {
 readonly outcome:'unavailable';
 readonly reason:'authorization'|'context'|'generation'|'awaiting_seed'|'retention'|'profile'|'observation'|'clock'|'resource';
 readonly sourceApplied?:never;
 readonly publishable?:never;
 readonly held?:never;
};
