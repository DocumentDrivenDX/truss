/** CONTRACT-002/004/007 draft retained reconstruction/source facade. */
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {Outcome, TransactionHandle} from './truss-execution-v0.1';
import type {ReconstructionRequest, ReconstructionResult} from './truss-history-reconstruction-v0.1';
import type {HistoricalSourceRequest, HistoricalSourceResult} from './truss-historical-source-v0.1';
import type {JournalPageRequest,JournalPageResult} from './truss-journal-page-v0.1';
export interface HistoryCapability {
  readonly selection:CapabilitySelection & {readonly family:'history'};
  pageJournal(transaction:TransactionHandle,request:JournalPageRequest):Promise<Outcome<JournalPageResult>>;
  reconstruct(transaction:TransactionHandle,request:ReconstructionRequest):Promise<Outcome<ReconstructionResult>>;
  historicalSource(transaction:TransactionHandle,request:HistoricalSourceRequest):Promise<Outcome<HistoricalSourceResult>>;
}
export type HistoryCapabilityResult = {
  readonly status:'ok';readonly capability:HistoryCapability;
} | {readonly status:'unavailable';readonly reason:'selection'|'disposed'};
