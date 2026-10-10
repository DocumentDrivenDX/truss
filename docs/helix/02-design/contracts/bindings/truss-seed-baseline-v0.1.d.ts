/** CONTRACT-006 proposed complete baseline inventory; no native extraction claim. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {TypedIdentity,HistoricalRecord} from './truss-history-v0.1';
import type {FeedRevisionFact,FeedSourceFact,FeedReservationFact} from './truss-feed-side-record-v0.1';
import type {SeedAttemptIdentity} from './truss-seed-activation-v0.1';
import type {SelectedMutationConfiguration} from './truss-mutation-configuration-v0.1';
export interface SeedBaseline {
 readonly interfaceVersion:'truss-seed-baseline/0.1.0';
 readonly attempt:SeedAttemptIdentity;
 readonly baselineProfile:ProfilePin;
 readonly layoutProfile:ProfilePin;
 readonly valueProfile:ProfilePin;
 readonly interpretationProfile:ProfilePin;
 readonly catalogRevision:string;
 /** Original cut evidence has no baseline/visibility/inventory digest dependency. */
 readonly snapshotEvidence:ExactArtifact;
 /** Complete live graph at the qualified cut, preserving storage identities/versions. */
 readonly records:readonly HistoricalRecord[];
 readonly revisions:readonly FeedRevisionFact[];
 readonly sources:readonly FeedSourceFact[];
 readonly reservations:readonly FeedReservationFact[];
 readonly configurations:readonly {readonly configuration:SelectedMutationConfiguration;readonly artifact:ExactArtifact}[];
 /** Exact retained history/definition/owner evidence required by the advertised horizon. */
 readonly retainedArchives:readonly {readonly archiveProfile:ProfilePin;readonly artifact:ExactArtifact}[];
}
export type SeedBaselineMemberIdentity = {
 readonly kind:'record';readonly entityKind:'object'|'edge';readonly identity:TypedIdentity;
} | {
 readonly kind:'revision';readonly revision:string;
} | {
 readonly kind:'source';readonly entityKind:'object'|'edge';readonly identity:TypedIdentity;
} | {
 readonly kind:'reservation';readonly reservation:FeedReservationFact;
} | {
 readonly kind:'configuration';readonly configuration:SelectedMutationConfiguration;
} | {
 readonly kind:'retained_archive';readonly archiveProfile:ProfilePin;readonly artifactIdentity:string;
};
export interface SeedBaselineInventory {
 readonly interfaceVersion:'truss-seed-baseline-inventory/0.1.0';
 readonly attempt:SeedAttemptIdentity;
 readonly inventoryProfile:ProfilePin;
 readonly baselineSha256:string;
 readonly visibilityManifestSha256:string;
 /** Complete original identities and preservation/owner closure, not counts alone. */
 readonly entries:readonly {
  readonly ordinal:string;
  readonly identity:SeedBaselineMemberIdentity;
  readonly payloadSha256:string;
  readonly retainedOwnerEvidence:ExactArtifact;
 }[];
 readonly extractionObservation:ExactArtifact;
}
