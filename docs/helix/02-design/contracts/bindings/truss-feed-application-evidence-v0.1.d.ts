/** CONTRACT-006 draft archived transition grammar; labels alone prove no durability. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {ConsumerWorkerIdentity,ConsumerAppliedBoundary} from './truss-feed-worker-v0.1';
import type {FeedProgressBoundary} from './truss-feed-transaction-v0.1';
export interface FeedCommittedApplicationEvidence {
 readonly interfaceVersion:'truss-feed-committed-application/0.1.0';
 readonly applicationIdentity:string;
 readonly worker:ConsumerWorkerIdentity;
 readonly downstreamIdentity:string;
 readonly downstreamProfile:ProfilePin;
 readonly applicationProfile:ProfilePin;
 readonly evidenceProfile:ProfilePin;
 readonly prior:ConsumerAppliedBoundary;
 readonly applied:FeedProgressBoundary;
 readonly operation:{readonly kind:'transaction';readonly manifest:ExactArtifact} |
  {readonly kind:'coverage';readonly coverage:ExactArtifact};
 /** Original admitted complete protected interval; raw content digest, not identity hash. */
 readonly intervalEvidence:ExactArtifact;
 /** Full original native admission/fence and durable transition inventory. */
 readonly admissionEvidence:ExactArtifact;
 readonly durableTransitionInventory:ExactArtifact;
 /** Original commit observation in registered custody, not a caller success flag. */
 readonly commitObservation:{readonly profile:ProfilePin;readonly evidence:ExactArtifact};
}
