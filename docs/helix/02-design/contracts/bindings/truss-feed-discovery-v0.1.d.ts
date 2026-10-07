/** CONTRACT-006 candidate; source enumeration is not downstream coverage proof. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {ConsumerWorkerIdentity,ConsumerAppliedBoundary} from './truss-feed-worker-v0.1';
import type {FeedTransactionManifest} from './truss-feed-transaction-v0.1';
export interface FeedDiscoveryRequest {
 readonly interfaceVersion:'truss-feed-discovery/0.1.0';
 readonly worker:ConsumerWorkerIdentity;
 /** Complete source resume state, including seed classifier when required. */
 readonly after:ConsumerAppliedBoundary;
 readonly discoveryProfile:ProfilePin;
 readonly limits:{readonly encodedBytes:string;readonly scannedTransactions:string};
}
export type FeedDiscoveryResult = {
 readonly outcome:'next';
 readonly manifest:FeedTransactionManifest;
 readonly safeWatermarkXid:string;
 readonly observation:ExactArtifact;
} | {
 /** No eligible required transaction in the exact observed interval. */
 readonly outcome:'empty_interval';
 readonly fromInclusiveXid:string;
 readonly throughExclusiveXid:string;
 readonly safeWatermarkXid:string;
 readonly observation:ExactArtifact;
} | {
 readonly outcome:'unavailable';
 readonly reason:'authorization'|'context'|'generation'|'profile'|'retention'|'integrity'|'resource_limit'|'observation';
 readonly manifest?:never;
 readonly observation?:never;
};
