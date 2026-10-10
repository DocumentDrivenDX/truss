/** Independent design-only public consumer; no runtime/native evidence. */
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
import type {DirectPageRequest, DirectPageResult} from './truss-direct-read-v0.1';
declare const assembly: ReferenceAssembly;
declare const selection: CapabilitySelection & {readonly family:'direct_read'};
declare const transaction: TransactionHandle;
declare const request: DirectPageRequest;
const selected = assembly.directReads(selection);
if (selected.status === 'ok') {
  const result = selected.capability.page(transaction, request);
  void result;
  // @ts-expect-error Host metadata cannot construct an executor-issued transaction.
  selected.capability.page({ownership:'caller',isolation:'repeatable_read',accessMode:'read_only'},request);
}
// @ts-expect-error Group family cannot select a direct-read facade.
assembly.directReads({...selection,family:'group'});
// @ts-expect-error Unavailable page result cannot carry a partial page.
const partial: DirectPageResult = {outcome:'unavailable',reason:'resource',page:{context:request.context,records:[],continuation:{state:'end'}}};
void partial;
