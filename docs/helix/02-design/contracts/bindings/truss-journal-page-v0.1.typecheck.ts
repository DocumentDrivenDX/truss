/** Public journal paging witnesses; no native completeness/authority evidence. */
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
import type {JournalPageRequest,JournalPageResult,JournalPageCursor} from './truss-journal-page-v0.1';
import type {FeedTransactionBoundary} from './truss-feed-transaction-v0.1';
declare const assembly:ReferenceAssembly;
declare const selection:CapabilitySelection & {readonly family:'history'};
declare const transaction:TransactionHandle;
declare const request:JournalPageRequest;
declare const complete:FeedTransactionBoundary;
const selected=assembly.history(selection);
if(selected.status==='ok')void selected.capability.pageJournal(transaction,request);
// @ts-expect-error Complete feed boundary is not a journal row position.
const mixed:JournalPageCursor={interfaceVersion:'truss-journal-cursor/0.1.0',context:request.context,after:complete};
// @ts-expect-error Unavailable journal page cannot advance a cursor.
const gap:JournalPageResult={outcome:'unavailable',reason:'retention',continuation:{state:'end'}};
// @ts-expect-error Native xid/seq are exact text, never rounded host numbers.
const numeric:JournalPageCursor={interfaceVersion:'truss-journal-cursor/0.1.0',context:request.context,after:{xid:9007199254740993,seq:1}};
// @ts-expect-error Held snapshot requires its exact issued identity.
const unknownSnapshot:JournalPageRequest={...request,context:{...request.context,snapshot:{state:'held'}}};
void [mixed,gap,numeric,unknownSnapshot];
