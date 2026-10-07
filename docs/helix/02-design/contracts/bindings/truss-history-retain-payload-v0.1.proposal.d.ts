/** CONTRACT-002 unadopted payload only. Not a HistoricalEvent or native capability. */
import type {ExactValue} from './truss-history-v0.1';
export interface RetainedAddition {
  /** Literal full name; duplicate names require runtime semantic refusal. */
  readonly retainedName: string;
  readonly before: {readonly present: false; readonly value?: never};
  readonly after: {readonly present: true; readonly value: ExactValue};
  /** References require registered original evidence; strings establish no authority. */
  readonly beforeDefinitionContext: string;
  readonly afterDefinitionContext: string;
  readonly sourceContext: string;
}
export interface HistoryRetainPayloadProposal {
  readonly interfaceVersion: 'truss-history-retain-payload/0.1.0';
  readonly operation: 'retain';
  readonly retainedChanges: readonly [RetainedAddition, ...RetainedAddition[]];
}
