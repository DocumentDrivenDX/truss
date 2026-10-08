/** ADR-007/CONTRACT-006 draft immutable side facts; no installed compatibility. */
import type {AcceptanceInput, ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
import type {ExactValue, TypedIdentity} from './truss-history-v0.1';
export interface FeedSourceFact {
  readonly interfaceVersion: 'truss-feed-source/0.1.0';
  readonly identity: TypedIdentity;
  readonly loadId: string;
  readonly createdCatalogRevision: string;
  readonly source: {
    readonly author?: string | null;
    /** Authored opaque source text; never a trusted commit timestamp. */
    readonly at?: string | null;
    readonly system?: string | null;
    readonly extensions: readonly {readonly name: string; readonly value: ExactValue}[];
  };
  /** Required for edge-source disclosure after endpoints disappear. */
  readonly endpoints: {readonly kind: 'object'} | {
    readonly kind: 'edge'; readonly source: TypedIdentity; readonly target: TypedIdentity;
  };
}
export interface FeedReservationFact {
  readonly interfaceVersion: 'truss-feed-reservation/0.1.0';
  readonly priorIdentity: TypedIdentity;
  readonly priorVersion: string;
  readonly createdCatalogRevision: string;
  readonly reservation: {
    readonly kind: 'object_key';
    readonly keyNumber: string;
    readonly keyDefinitionPin: string;
    readonly keyEncodingProfile: ProfilePin;
    readonly encodedKey: string;
  } | {
    readonly kind: 'edge_endpoints';
    readonly relationshipDefinitionPin: string;
    readonly source: TypedIdentity;
    readonly target: TypedIdentity;
    readonly keyNumber: '0';
    readonly keyEncodingProfile: ProfilePin;
    readonly encodedKey: string;
  };
}
export interface FeedRevisionFact {
  readonly interfaceVersion: 'truss-feed-revision/0.1.0';
  readonly revision: string;
  readonly acceptedAt: string;
  readonly input: AcceptanceInput;
  /** Complete pinned report, not a reconstruction from today's definitions. */
  readonly report: ExactArtifact;
  readonly origin: {readonly asserted: ExactValue; readonly databaseRole: string};
}
