/** Compile-only custody/version controls; no executable registration evidence. */
import type {WorkerClaim,VerifiedApplication} from '../../../02-design/contracts/bindings/truss-feed-worker-v0.1';
import type {HostFeedDownstreamAdapter} from '../../../02-design/contracts/bindings/truss-feed-downstream-adapter-v0.1';
import type {HostFeedApplicationAdapter} from '../../../02-design/contracts/bindings/truss-feed-application-adapter-v0.1';
import type {WorkerClaimV02,FeedHostCompositionRequestV02,FeedHostCompositionRegistrationV02,
 HostFeedDownstreamAdapterV02,FeedHostCompositionRegistrationResultV02} from '../../../02-design/contracts/bindings/truss-feed-host-composition-v0.2';
import type {FeedProofVerifierRegistration} from '../../../02-design/contracts/bindings/truss-feed-proof-verifier-v0.1';
declare const oldClaim:WorkerClaim;
declare const request:FeedHostCompositionRequestV02;
declare const oldInstallation:HostFeedDownstreamAdapter;
declare const oldApplication:HostFeedApplicationAdapter;
declare const oldVerifier:FeedProofVerifierRegistration;
declare const oldCustody:VerifiedApplication;
declare const registration:FeedHostCompositionRegistrationV02;
// @ts-expect-error Original v0.1 claim cannot become v0.2 source progress.
const claim:WorkerClaimV02=oldClaim;
// @ts-expect-error Old installation accepts/returns the wrong progress domain.
const installation:HostFeedDownstreamAdapterV02=oldInstallation;
// @ts-expect-error Complete composition requires the v0.2 application protocol.
const mixedApplication:FeedHostCompositionRequestV02={...request,downstreamApplication:oldApplication};
// @ts-expect-error Old verifier registration cannot grant new proof custody.
const mixedVerifier:FeedHostCompositionRequestV02={...request,verifier:oldVerifier};
// @ts-expect-error Missing seed services cannot create partial successful composition.
const incomplete:FeedHostCompositionRequestV02={...request,seed:{composition:request.seed.composition}};
// @ts-expect-error Copying visible request fields cannot fabricate opaque host custody.
const fabricated:FeedHostCompositionRegistrationV02={originalRequest:request};
// @ts-expect-error Application verification custody is not composition registration.
const unrelated:FeedHostCompositionRegistrationV02=oldCustody;
// @ts-expect-error Rejected registration cannot leak a usable success credential.
const rejected:FeedHostCompositionRegistrationResultV02={status:'error',code:'registration_conflict',registration};
