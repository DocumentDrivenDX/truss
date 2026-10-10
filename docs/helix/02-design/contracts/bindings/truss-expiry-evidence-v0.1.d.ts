/** Minimal metadata basis; actual native effect/commit verified separately. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
export interface ExpiryMetadataReference {readonly identity:string;readonly sha256:string;}
export interface ExpiryEvidence {
 readonly interfaceVersion:'truss-expiry-evidence/0.1.0';
 readonly authorizedScopeIdentity:string;readonly requestId:string;
 readonly canonicalProfile:ProfilePin;readonly semanticDomain:'truss-group-input/0.1.0';readonly inputSha256:string;
 readonly clockProfile:ProfilePin;readonly retentionProfile:ProfilePin;readonly expiryProcedureProfile:ProfilePin;
 readonly expiredAt:string;readonly priorLifecycleGeneration:string;readonly resultingLifecycleGeneration:string;
 readonly originalProtection:ExpiryMetadataReference;readonly clockObservation:ExpiryMetadataReference;
 readonly currentAuthorityObservation:ExpiryMetadataReference;readonly expiryWriterContext:ExpiryMetadataReference;
 readonly eventAdmission:{readonly kind:'event_bearing';readonly completeOriginalEventUnion:ExpiryMetadataReference;readonly absenceObservation:ExpiryMetadataReference} |
 {readonly kind:'all_no_op';readonly originalNoOpClassification:ExpiryMetadataReference;readonly replayWindowProfile:ProfilePin};
 readonly input?:never;readonly result?:never;readonly committed?:never;
}
