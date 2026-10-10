/** Consumer declaration witnesses, not native feed/proof qualification. */
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
import type {FeedFragmentRequest} from './truss-feed-transaction-v0.1';
import type {ConsumerAcknowledgment, ConsumerAppliedBoundary, ApplicationProofSubmission} from './truss-feed-worker-v0.1';
import type {FeedDiscoveryRequest,FeedDiscoveryResult} from './truss-feed-discovery-v0.1';
import type {FeedAcknowledgmentResult} from './truss-feed-capability-v0.1';
declare const assembly:ReferenceAssembly;
declare const selection:CapabilitySelection & {readonly family:'feed'};
declare const transaction:TransactionHandle;
declare const request:FeedFragmentRequest;
declare const discovery:FeedDiscoveryRequest;
declare const acknowledgment:ConsumerAcknowledgment;
declare const applied:ConsumerAppliedBoundary;
declare const proof:ApplicationProofSubmission;
const selected=assembly.feed(selection);
if(selected.status==='ok') {
 void selected.capability.discoverNext(transaction,discovery);
 void selected.capability.readFragment(transaction,request);
 void selected.capability.acknowledgeInTransaction(transaction,acknowledgment);
 // @ts-expect-error Fragment delivery is not an application acknowledgment.
 selected.capability.acknowledgeInTransaction(transaction,request);
}
// @ts-expect-error Supplied transaction CAS cannot report confirmed outer commit.
const early:FeedAcknowledgmentResult={outcome:'advanced',applied,durability:'committed'};
// @ts-expect-error Unavailable consumer state must not disclose a current checkpoint.
const hidden:FeedAcknowledgmentResult={outcome:'unavailable',reason:'authorization',current:applied};
// @ts-expect-error Submitted proof is not a host-issued verified capability.
const unverified:ConsumerAcknowledgment={worker:acknowledgment.worker,expectedPrior:applied,application:proof};
void [early,hidden,unverified];

// @ts-expect-error Unavailable discovery cannot disclose a partial manifest.
const gap:FeedDiscoveryResult={outcome:'unavailable',reason:'authorization',manifest:request.manifest};
// @ts-expect-error Empty source enumeration does not carry downstream applied progress.
const falseApplication:FeedDiscoveryResult={outcome:'empty_interval',fromInclusiveXid:'1',throughExclusiveXid:'2',safeWatermarkXid:'2',observation:{identity:'fixture',bytesBase64:'e30=',sha256:'digest'},applied};
void [gap,falseApplication];
