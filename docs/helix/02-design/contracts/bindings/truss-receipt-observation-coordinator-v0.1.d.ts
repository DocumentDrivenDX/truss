/** Original host/native lease candidate; metadata never grants authority. */
import type {CapturedDataCaller} from './truss-authority-coordinator-v0.1';
import type {RequestNamespaceGrant} from './truss-request-namespace-v0.1';
import type {QualifiedOwner} from './truss-history-v0.1';
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {ReceiptProtectionObservationRequest} from './truss-receipt-protection-tooling-v0.1';
import type {ReceiptExpiryObservationRequest,ReceiptExpiryScopeRequest} from './truss-receipt-expiry-tooling-v0.1';
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
export type ReceiptObservationIntent={readonly kind:'protection';readonly request:ReceiptProtectionObservationRequest} |
 {readonly kind:'expiry';readonly request:ReceiptExpiryObservationRequest} |
 {readonly kind:'purge_assessment';readonly request:ReceiptExpiryScopeRequest};
export interface ReceiptObservationAdmissionRequest {
 readonly caller:CapturedDataCaller;readonly namespace:RequestNamespaceGrant;
 readonly owners:readonly [QualifiedOwner,...QualifiedOwner[]];readonly originalOwnerContext:ExactArtifact;
 readonly intent:ReceiptObservationIntent;
}
declare const receiptLeaseBrand:unique symbol;
export interface ReceiptObservationLease {
 readonly [receiptLeaseBrand]:true;readonly leaseIdentity:string;readonly profile:ProfilePin;
 readonly caller:CapturedDataCaller;readonly namespace:RequestNamespaceGrant;
 readonly originalAdmission:ReceiptObservationAdmissionRequest;
 readonly policyAdmission:ExactArtifact;readonly namespaceAdmission:ExactArtifact;
 readonly routeAdmission:ExactArtifact;readonly currentCut:ExactArtifact;
}
export type ReceiptObservationAdmission={readonly outcome:'admitted';readonly lease:ReceiptObservationLease} |
 {readonly outcome:'unavailable';readonly reason:'authority'|'context'|'profile'|'integrity'|'exclusion'|'observation'|'resource';readonly lease?:never};
export interface HostReceiptObservationCoordinator {
 readonly profile:ProfilePin;
 admit(request:ReceiptObservationAdmissionRequest):Promise<ReceiptObservationAdmission>;
 /** Original issuer recognition plus fresh native/context/proof validation. */
 validateDisclosure(lease:ReceiptObservationLease,originalObservedState:ExactArtifact):Promise<
 {readonly outcome:'valid';readonly evidence:ExactArtifact} |
 {readonly outcome:'unavailable';readonly evidence?:never}>;
 /** Service exclusion only; never end data caller work or close host service. */
 release(lease:ReceiptObservationLease):Promise<{readonly outcome:'released'} |
 {readonly outcome:'unresolved';readonly recoveryReferences:readonly [string,...string[]]}>;
}
declare const receiptCoordinatorRegistrationBrand:unique symbol;
export interface ReceiptObservationCoordinatorRegistration {
 readonly [receiptCoordinatorRegistrationBrand]:true;
 readonly profile:ProfilePin;readonly originalComposition:ExactArtifact;
}
export type ReceiptCoordinatorRegistrationResult={readonly status:'ok';readonly registration:ReceiptObservationCoordinatorRegistration} |
 {readonly status:'error';readonly code:'disposed'|'unsupported_profile'|'incompatible_selection';readonly registration?:never};
/** Inert original-object registration; no native validation/support claim. */
export declare function registerReceiptObservationCoordinator(assembly:ReferenceAssembly,
 profile:ProfilePin,originalComposition:ExactArtifact,service:HostReceiptObservationCoordinator):ReceiptCoordinatorRegistrationResult;
