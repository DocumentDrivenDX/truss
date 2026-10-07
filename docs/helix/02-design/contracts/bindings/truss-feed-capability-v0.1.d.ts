/** CONTRACT-006/007 draft; no implicit worker, verifier or downstream runtime. */
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {Outcome, TransactionHandle} from './truss-execution-v0.1';
import type {FeedFragmentRequest, FeedFragmentPage} from './truss-feed-transaction-v0.1';
import type {ConsumerAcknowledgment, ConsumerAppliedBoundary} from './truss-feed-worker-v0.1';
import type {FeedDiscoveryRequest,FeedDiscoveryResult} from './truss-feed-discovery-v0.1';
import type {CompleteFeedFreshnessRequest,CompleteFeedFreshnessResult} from './truss-feed-freshness-v0.1';
export type FeedAcknowledgmentResult = {
 readonly outcome:'advanced'|'equal';
 readonly applied:ConsumerAppliedBoundary;
 /** Source checkpoint effects remain subject to the supplied transaction. */
 readonly durability:'pending';
} | {
 readonly outcome:'conflict';
 /** Returned only when current consumer-state disclosure is authorized. */
 readonly current:ConsumerAppliedBoundary;
} | {
 readonly outcome:'unavailable';
 readonly reason:'authorization'|'context'|'generation'|'integrity'|'durability'|'profile'|'retention'|'observation';
 readonly current?:never;
 readonly applied?:never;
};
export interface FeedCapability {
 readonly selection:CapabilitySelection & {readonly family:'feed'};
 discoverNext(transaction:TransactionHandle,request:FeedDiscoveryRequest):Promise<Outcome<FeedDiscoveryResult>>;
 observeFreshness(transaction:TransactionHandle,request:CompleteFeedFreshnessRequest):Promise<Outcome<CompleteFeedFreshnessResult>>;
 readFragment(transaction:TransactionHandle,request:FeedFragmentRequest):Promise<Outcome<FeedFragmentPage>>;
 acknowledgeInTransaction(transaction:TransactionHandle,request:ConsumerAcknowledgment):Promise<Outcome<FeedAcknowledgmentResult>>;
}
export type FeedCapabilityResult = {
 readonly status:'ok';readonly capability:FeedCapability;
} | {readonly status:'unavailable';readonly reason:'selection'|'disposed'};
