import type {Backlog, JournalPosition, CheckpointAssessment} from './truss-feed-observation-v0.1';
const empty: Backlog = {state: 'empty', ageNanoseconds: '0'};
const unavailable: Backlog = {state: 'unavailable', reason: 'scope'};
const position: JournalPosition = {xid: '9007199254740993', seq: '2'};
// @ts-expect-error Unavailable observation cannot manufacture zero lag.
const falseZero: Backlog = {state: 'unavailable', reason: 'scope', ageNanoseconds: '0'};
// @ts-expect-error Empty backlog has no oldest record timestamp.
const falseOldest: Backlog = {state: 'empty', ageNanoseconds: '0', oldestWriteAt: 'x'};
// @ts-expect-error Exact position is not a host number.
const rounded: JournalPosition = {xid: 9007199254740993, seq: '2'};
// @ts-expect-error Unauthorized response cannot disclose current position.
const leaked: CheckpointAssessment = {outcome: 'unavailable', reason: 'authorization', current: {domain: 'journal-only', context: {sourceEpoch: 'e', feedProfile: 'p', scopeIdentity: 's'}, position}};
void [empty, unavailable, position, falseZero, falseOldest, rounded, leaked];
