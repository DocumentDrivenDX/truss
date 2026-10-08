/** Proposed CONTRACT-006 observation binding; no complete-feed wire/support claim. */
export interface FeedContext {
  readonly sourceEpoch: string;
  readonly feedProfile: string;
  readonly scopeIdentity: string;
}
/** Text is runtime-validated nonnegative integer syntax; never host numbers. */
export interface JournalPosition {
  readonly xid: string;
  readonly seq: string;
}
/** Full revision/side-record checkpoint remains a distinct future profile. */
export interface JournalCheckpoint {
  readonly domain: 'journal-only';
  readonly context: FeedContext;
  readonly position: JournalPosition;
}
export type Backlog = {
  readonly state: 'present';
  readonly oldestWriteAt: string;
  readonly ageNanoseconds: string;
} | {
  readonly state: 'empty';
  readonly ageNanoseconds: '0';
  readonly oldestWriteAt?: never;
} | {
  readonly state: 'unavailable';
  readonly reason: 'scope' | 'retention' | 'epoch' | 'observation' | 'clock';
  readonly oldestWriteAt?: never;
  readonly ageNanoseconds?: never;
};
export interface JournalFreshness {
  readonly interfaceVersion: 'truss-feed-observation/0.1.0';
  readonly checkpoint: JournalCheckpoint;
  readonly checkpointUpdatedAt: string;
  readonly observedAt: string;
  readonly safeWatermarkXid: string;
  readonly publishable: Backlog;
  /** Committed visible rows only, never inferred uncommitted changes. */
  readonly held: Backlog;
  readonly limitations: readonly string[];
}
/** No mutation API here: authorized durable-application proof/fencing is gated. */
export type CheckpointAssessment = {
  readonly outcome: 'advanced' | 'equal';
  readonly checkpoint: JournalCheckpoint;
} | {
  readonly outcome: 'conflict';
  readonly current: JournalCheckpoint;
} | {
  readonly outcome: 'unavailable';
  readonly reason: 'authorization' | 'epoch' | 'profile' | 'retention' | 'observation';
  readonly current?: never;
};
