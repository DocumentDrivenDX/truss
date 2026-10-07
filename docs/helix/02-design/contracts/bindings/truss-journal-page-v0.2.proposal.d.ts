/** Proposed result tuple only; original profile/cursor admission is still required. */
import type {JournalPageResult} from './truss-journal-page-v0.1';
import type {ProposedHistoricalEvent} from './truss-history-v0.2.proposal';
export type ProposedJournalPageResult =
  (Omit<Extract<JournalPageResult,{readonly outcome:'page'}>,'events'> & {
    readonly events:readonly ProposedHistoricalEvent[];
  }) | Extract<JournalPageResult,{readonly outcome:'unavailable'}>;
