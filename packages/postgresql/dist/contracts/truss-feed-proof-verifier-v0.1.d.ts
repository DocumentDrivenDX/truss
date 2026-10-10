/** CONTRACT-006/007 draft trusted host service; no portable verifier implementation. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
import type {ApplicationProofSubmission,ApplicationProofAssessment,VerifiedApplication} from './truss-feed-worker-v0.1';
export interface HostFeedProofVerifier {
 readonly verifierProfile:ProfilePin;
 readonly downstreamProfile:ProfilePin;
 /** Host-issued registration identity; not data-caller authority. */
 readonly registrationIdentity:string;
 /** Resolves only registered evidence custody and observes actual downstream durability. */
 assess(submission:ApplicationProofSubmission):Promise<ApplicationProofAssessment>;
 /** Checks issuer custody and exact immutable proof; false for casts/deserialized copies. */
 recognizes(application:VerifiedApplication):boolean;
}
export interface FeedProofVerifierRegistration {
 readonly capabilityProfile:ProfilePin;
 readonly verifier:HostFeedProofVerifier;
}
