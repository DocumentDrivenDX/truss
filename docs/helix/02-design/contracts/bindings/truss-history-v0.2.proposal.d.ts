/** CONTRACT-002 review wire only; no runtime registration or native qualification. */
import type {EventContext, HistoricalEvent} from './truss-history-v0.1';
import type {RetainedAddition} from './truss-history-retain-payload-v0.1.proposal';
export type ProposedEventContext = Omit<EventContext, 'interfaceVersion'> & {
  readonly interfaceVersion: 'truss-history-event/0.2.0-proposal';
};
/** Distribute across the original union so operation-specific members remain intact. */
type Reversion<E extends HistoricalEvent> = E extends unknown ?
  Omit<E, 'interfaceVersion'> & ProposedEventContext : never;
export type ProposedHistoricalEvent = Reversion<HistoricalEvent> | (ProposedEventContext & {
  readonly operation: 'retain';
  readonly retainedChanges: readonly [RetainedAddition, ...RetainedAddition[]];
});
