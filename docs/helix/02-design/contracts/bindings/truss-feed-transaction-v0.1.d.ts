/** D-07 candidate: requires atomic manifest production, not current layout. */
import type {ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
import type {TypedIdentity} from './truss-history-v0.1';
import type {FeedContext} from './truss-feed-observation-v0.1';
import type {SelectedMutationConfiguration} from './truss-mutation-configuration-v0.1';
export type FeedRecordKey = {
  readonly kind: 'change'; readonly seq: string;
} | {
  readonly kind: 'revision'; readonly revision: string;
} | {
  readonly kind: 'source'; readonly entityKind: 'object' | 'edge'; readonly identity: TypedIdentity;
} | {
  readonly kind: 'reservation';
  readonly entityKind: 'object' | 'edge';
  readonly typeId: string;
  readonly keyNumber: string;
  readonly encodedKey: string;
};
export interface FeedManifestMember {
  readonly ordinal: string;
  readonly key: FeedRecordKey;
  readonly payloadProfile: ProfilePin;
  readonly payloadSha256: string;
}
export interface FeedTransactionManifest {
  readonly interfaceVersion: 'truss-feed-transaction/0.1.0';
  readonly context: FeedContext;
  /** Producing committed top-level full transaction ID. */
  readonly xid: string;
  readonly manifestProfile: ProfilePin;
  /** Original configuration needed by member interpretation, never today's settings. */
  readonly configurationPrerequisites: readonly {
    readonly configuration: SelectedMutationConfiguration;
    readonly artifact: ExactArtifact;
  }[];
  readonly members: readonly [FeedManifestMember, ...FeedManifestMember[]];
  /** Complete required definition artifacts, including revision-only inputs. */
  readonly prerequisites: readonly {
    readonly revision: string; readonly artifact: ExactArtifact;
  }[];
  readonly manifestSha256: string;
}
/** Fragment receipt is never a durable transaction acknowledgment. */
export interface FeedTransactionFragment {
  readonly manifest: FeedTransactionManifest;
  readonly records: readonly {
    readonly ordinal: string; readonly payload: ExactArtifact;
  }[];
}
export interface FeedFragmentCursor {
  readonly interfaceVersion: 'truss-feed-fragment-cursor/0.1.0';
  readonly context: FeedContext;
  readonly xid: string;
  readonly manifestSha256: string;
  readonly deliveryProfile: ProfilePin;
  /** Last delivered manifest ordinal, not journal seq or an acknowledged boundary. */
  readonly afterOrdinal: string;
}
export interface FeedFragmentRequest {
  readonly manifest: FeedTransactionManifest;
  readonly deliveryProfile: ProfilePin;
  readonly limits: {readonly records: string; readonly encodedBytes: string};
  readonly continuation: {readonly state: 'first'} |
    {readonly state: 'after'; readonly cursor: FeedFragmentCursor};
}
export type FeedFragmentPage = {
  readonly outcome: 'available'; readonly fragment: FeedTransactionFragment & {
    readonly records: readonly [{readonly ordinal: string; readonly payload: ExactArtifact},
      ...{readonly ordinal: string; readonly payload: ExactArtifact}[]];
  };
  readonly continuation: {readonly state: 'end'} |
    {readonly state: 'more'; readonly cursor: FeedFragmentCursor};
} | {
  readonly outcome: 'unavailable';
  readonly reason: 'authorization' | 'retention' | 'profile' | 'integrity' | 'resource_limit';
  readonly fragment?: never;
};
export type FeedAssemblyAssessment = {
  readonly state: 'incomplete'; readonly missingOrdinals: readonly [string, ...string[]];
} | {
  readonly state: 'unavailable';
  readonly reason: 'authorization' | 'retention' | 'profile' | 'integrity' | 'resource_limit';
} | {
  readonly state: 'complete'; readonly manifest: FeedTransactionManifest;
  readonly orderedPayloads: readonly [ExactArtifact, ...ExactArtifact[]];
};
/** Distinct candidate domain; cannot be substituted for journal-only positions. */
export interface FeedTransactionBoundary {
  readonly domain: 'complete-feed-transaction/0.1.0';
  readonly context: FeedContext;
  readonly xid: string;
  readonly manifestSha256: string;
}
/** Every required transaction strictly below the frontier is accounted for. */
export interface FeedCoverageBoundary {
  readonly domain: 'complete-feed-coverage/0.1.0';
  readonly context: FeedContext;
  readonly throughExclusiveXid: string;
  readonly coverageEvidenceSha256: string;
}
export type FeedProgressBoundary = FeedTransactionBoundary | FeedCoverageBoundary;
export interface FeedIntervalCoverage {
  readonly interfaceVersion: 'truss-feed-coverage/0.1.0';
  readonly context: FeedContext;
  readonly fromInclusiveXid: string;
  readonly throughExclusiveXid: string;
  readonly observedSafeWatermarkXid: string;
  readonly sourceEnumerationEvidence: ExactArtifact;
  readonly retentionProtectionEvidence: ExactArtifact;
  /** Exactly all required producing transactions in this protected interval. */
  readonly transactions: readonly {
    readonly xid: string;
    readonly manifestSha256: string;
    readonly disposition: {readonly kind: 'represented'; readonly visibilityManifestSha256: string} |
      {readonly kind: 'applied'; readonly committedApplicationEvidenceSha256: string};
  }[];
  readonly coverageProfile: ProfilePin;
}
