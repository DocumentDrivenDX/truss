import type {ReceiptLifecycleConfiguration} from '../../../02-design/contracts/bindings/truss-receipt-lifecycle-tooling-v0.1';
import type {ReceiptObservationAdmission,ReceiptObservationCoordinatorRegistration,ReceiptObservationLease} from '../../../02-design/contracts/bindings/truss-receipt-observation-coordinator-v0.1';
declare const configuration:ReceiptLifecycleConfiguration;
declare const lease:ReceiptObservationLease;
// @ts-expect-error Read-only mode requires original registered coordinator custody.
const missing:ReceiptLifecycleConfiguration={...configuration,observationBinding:{mode:'coordinated_read_only'}};
// @ts-expect-error Unavailable native admission cannot leak a lease.
const failed:ReceiptObservationAdmission={outcome:'unavailable',reason:'authority',lease};
// @ts-expect-error Matching serialized profile/composition cannot fabricate original registration.
const fabricated:ReceiptObservationCoordinatorRegistration={profile:configuration.observationProfile,originalComposition:configuration.composition};
