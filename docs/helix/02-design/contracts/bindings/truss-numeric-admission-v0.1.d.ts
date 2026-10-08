/** ADR-006 pure-core draft; no runtime implementation or native admission claim. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {NumericInput,ExactIntegerToken,ExactDecimalToken,NumericInputOrigin} from './truss-numeric-carriers-v0.1';
export interface NumericAdmissionRequest {
 readonly interfaceVersion:'truss-numeric-admission/0.1.0';
 /** Original complete UMF JSON bytes; digest/identity and full document admission are verified. */
 readonly umfDocument:ExactArtifact;
 readonly field:{readonly documentId:string;readonly moduleId:string;readonly fieldId:string};
 readonly umfProfile:ProfilePin;
 readonly interpretationProfile:ProfilePin;
 readonly conversionProfile:ProfilePin;
 readonly resourceProfile:ProfilePin;
 readonly diagnosticProfile:ProfilePin;
 readonly input:NumericInput;
}
export type NumericAdmissionResult = {
 readonly status:'admitted';
 readonly field:NumericAdmissionRequest['field'];
 readonly originalDocumentSha256:string;
 readonly origin:NumericInputOrigin;
} & ({readonly token:ExactIntegerToken;readonly value:{readonly kind:'integer';readonly text:string}} |
 {readonly token:ExactDecimalToken;readonly value:{readonly kind:'decimal';readonly text:string}}) | {
 readonly status:'refused';
 readonly code:'invalid_source'|'unsupported_profile'|'invalid_numeric_input'|'out_of_domain'|'resource';
 readonly diagnosticProfile:ProfilePin;
 /** Exact original diagnostics under the selected encoder; never reconstructed from message text. */
 readonly diagnostics?:ExactArtifact;
 readonly token?:never;readonly value?:never;
};
/** Pure bounded conversion + pinned UMF field validation; no native/transaction/receipt I/O. */
export declare function admitNumericInput(request:NumericAdmissionRequest):NumericAdmissionResult;
