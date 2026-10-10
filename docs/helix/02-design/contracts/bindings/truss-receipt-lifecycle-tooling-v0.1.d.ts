/** CONTRACT-007/009 inert administrative group tooling candidate. */
import type {ProfilePin,ExactArtifact} from './truss-acceptance-input-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {ReceiptProtectionTooling} from './truss-receipt-protection-tooling-v0.1';
import type {ReceiptObservationCoordinatorRegistration} from './truss-receipt-observation-coordinator-v0.1';
import type {ReceiptExpiryTooling} from './truss-receipt-expiry-tooling-v0.1';
export interface ReceiptLifecycleConfiguration {
 readonly interfaceVersion:'truss-receipt-lifecycle-tooling/0.1.0';
 readonly selection:CapabilitySelection & {readonly family:'group'};
 readonly lifecycleProfile:ProfilePin;readonly clockProfile:ProfilePin;readonly retentionProfile:ProfilePin;
 /** Complete original native procedure/privilege/archive/namespace/resource composition. */
 readonly composition:ExactArtifact;
 /** Selected original observation binding; no implied read-only support. */
 readonly observationProfile:ProfilePin;
 readonly observationBinding:{readonly mode:'writable'} | {readonly mode:'coordinated_read_only';readonly registration:ReceiptObservationCoordinatorRegistration};
}
export interface ReceiptLifecycleTooling {
 readonly configuration:ReceiptLifecycleConfiguration;
 readonly protection:ReceiptProtectionTooling;
 readonly expiry:ReceiptExpiryTooling;
}
export type ReceiptLifecycleConstructionResult={readonly status:'ok';readonly value:ReceiptLifecycleTooling} |
 {readonly status:'error';readonly code:'disposed'|'unsupported_profile'|'incompatible_selection'|'missing_service';readonly value?:never};
/** Existing assembly-issued registration/custody only; no callback or native IO.
 * Original observation service registration must already belong to assembly's
 * qualified host/executor profile; names or serialized evidence cannot supply it.
 */
export declare function createReceiptLifecycleTooling(assembly:ReferenceAssembly,configuration:ReceiptLifecycleConfiguration):ReceiptLifecycleConstructionResult;
