/** Unadopted archive wire; complete original inventory and semantic admission required. */
import type {RetainedHistoryArchive} from './truss-retained-history-archive-v0.1';
import type {ProposedHistoricalEvent} from './truss-history-v0.2.proposal';
export type ProposedRetainedHistoryArchive = Omit<RetainedHistoryArchive,'interfaceVersion'|'events'> & {
 readonly interfaceVersion:'truss-retained-history-archive/0.2.0-proposal';
 readonly events:readonly ProposedHistoricalEvent[];
};
