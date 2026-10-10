/** Public consumer witnesses; no native reconstruction/authority qualification. */
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
import type {ReconstructionRequest, ReconstructionResult} from './truss-history-reconstruction-v0.1';
import type {HistoricalSourceRequest, HistoricalSourceResult} from './truss-historical-source-v0.1';
declare const assembly:ReferenceAssembly;
declare const selection:CapabilitySelection & {readonly family:'history'};
declare const wrongSelection:CapabilitySelection & {readonly family:'direct_read'};
declare const transaction:TransactionHandle;
declare const reconstruction:ReconstructionRequest;
declare const source:HistoricalSourceRequest;
const selected=assembly.history(selection);
if(selected.status==='ok') {
 void selected.capability.reconstruct(transaction,reconstruction);
 void selected.capability.historicalSource(transaction,source);
 // @ts-expect-error Source lookup cannot substitute for a versioned reconstruction request.
 selected.capability.reconstruct(transaction,source);
}
// @ts-expect-error Capability family is pinned at selection.
assembly.history(wrongSelection);
// @ts-expect-error Hidden history outcomes must not expose the request.
const hidden:ReconstructionResult={outcome:'not_found',request:reconstruction};
// @ts-expect-error Missing source evidence cannot be reported as proved absence.
const absence:HistoricalSourceResult={outcome:'absent',request:source};
void [hidden,absence];
