/** Public freshness consumer witnesses; no native clock/snapshot qualification. */
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
import type {CompleteFeedFreshnessRequest,CompleteFeedFreshnessResult} from './truss-feed-freshness-v0.1';
import type {ConsumerAppliedBoundary} from './truss-feed-worker-v0.1';
declare const assembly:ReferenceAssembly;
declare const selection:CapabilitySelection & {readonly family:'feed'};
declare const transaction:TransactionHandle;
declare const request:CompleteFeedFreshnessRequest;
declare const applied:ConsumerAppliedBoundary;
const selected=assembly.feed(selection);
if(selected.status==='ok')void selected.capability.observeFreshness(transaction,request);
// @ts-expect-error Awaiting/hidden consumer cannot disclose an applied boundary.
const hidden:CompleteFeedFreshnessResult={outcome:'unavailable',reason:'awaiting_seed',sourceApplied:applied};
// @ts-expect-error Unavailable freshness cannot masquerade as zero publishable lag.
const zero:CompleteFeedFreshnessResult={outcome:'unavailable',reason:'retention',publishable:{state:'empty',ageNanoseconds:'0'}};
void [hidden,zero];
