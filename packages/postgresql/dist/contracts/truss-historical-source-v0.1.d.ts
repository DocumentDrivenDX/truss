/** CONTRACT-004/005 draft; exact original creation and current authority need evidence. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
import type {TypedIdentity} from './truss-history-v0.1';
import type {FeedSourceFact} from './truss-feed-side-record-v0.1';
export interface HistoricalSourceRequest {
  readonly interfaceVersion: 'truss-historical-source/0.1.0';
  readonly sourceEpoch: string;
  readonly identity: TypedIdentity;
  readonly sourceProfile: ProfilePin;
}
export interface HistoricalSourceEvidence {
  readonly creationInventorySha256: string;
  readonly retainedOwnerInventorySha256: string;
  readonly currentAuthorityObservationSha256: string;
  readonly observationProcedure: ProfilePin;
}
export type HistoricalSourceResult = {
  readonly outcome: 'found'; readonly request: HistoricalSourceRequest;
  readonly fact: FeedSourceFact; readonly evidence: HistoricalSourceEvidence;
} | {
  readonly outcome: 'absent'; readonly request: HistoricalSourceRequest;
  readonly evidence: HistoricalSourceEvidence; readonly fact?: never;
} | {
  readonly outcome: 'not_found'; readonly request?: never; readonly fact?: never;
} | {
  readonly outcome: 'unavailable'; readonly fact?: never;
  readonly reason: 'creation_inventory' | 'ownership' | 'retention' | 'profile' | 'observation';
};
