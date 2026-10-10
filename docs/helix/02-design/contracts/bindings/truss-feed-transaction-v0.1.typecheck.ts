import type {FeedRecordKey, FeedTransactionBoundary, FeedAssemblyAssessment} from './truss-feed-transaction-v0.1';
import type {JournalCheckpoint} from './truss-feed-observation-v0.1';
const context = {sourceEpoch: 'fixture', feedProfile: 'draft', scopeIdentity: 'fixture'};
const boundary: FeedTransactionBoundary = {
  domain: 'complete-feed-transaction/0.1.0', context, xid: '9007199254740993', manifestSha256: '0'.repeat(64),
};
const reservation: FeedRecordKey = {kind: 'reservation', entityKind: 'object', typeId: '1', keyNumber: '2', encodedKey: 'fixture'};
// @ts-expect-error A complete-feed boundary cannot substitute for a journal cursor.
const journal: JournalCheckpoint = boundary;
// @ts-expect-error Native transaction identity cannot use a rounded host number.
const rounded: FeedTransactionBoundary = {...boundary, xid: 9007199254740993};
// @ts-expect-error Reservation identity needs the complete native key tuple.
const abbreviated: FeedRecordKey = {kind: 'reservation', reservationIdentity: 'opaque'};
// @ts-expect-error Incomplete assembly must identify at least one missing ordinal.
const vacuousIncomplete: FeedAssemblyAssessment = {state: 'incomplete', missingOrdinals: []};
// @ts-expect-error Unavailable assembly cannot also disclose complete payloads.
const unavailableComplete: FeedAssemblyAssessment = {state: 'unavailable', reason: 'authorization', orderedPayloads: []};
void [boundary, reservation, journal, rounded, abbreviated, vacuousIncomplete, unavailableComplete];
