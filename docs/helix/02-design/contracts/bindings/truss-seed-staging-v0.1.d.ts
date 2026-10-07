/** CONTRACT-006 explicit host staging; stage does not activate a copy. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {SeedExtractionResult} from './truss-seed-extraction-v0.1';
import type {SeedActivationState} from './truss-seed-activation-v0.1';
export interface SeedStagingRequest {
 readonly interfaceVersion:'truss-seed-staging/0.1.0';
 readonly extraction:Extract<SeedExtractionResult,{readonly outcome:'extracted'}>;
 readonly stagingProfile:ProfilePin;
 readonly sourceAdmission:ExactArtifact;
 readonly limits:{readonly encodedBytes:string;readonly records:string};
}
export type SeedStagingResult = {
 readonly outcome:'staged';
 readonly stage:Extract<SeedActivationState,{readonly state:'staged'}>;
 readonly custodyEvidence:ExactArtifact;
} | {
 readonly outcome:'unavailable';
 readonly reason:'authorization'|'context'|'generation'|'profile'|'protection'|'integrity'|'resource'|'custody';
 readonly stage?:never;
} | {
 readonly outcome:'recovery_required';
 readonly recoveryReference:string;
 readonly originalAttemptEvidence:ExactArtifact;
 readonly stage?:never;
};
export interface HostSeedStagingAdapter {
 readonly downstreamIdentity:string;
 readonly downstreamProfile:ProfilePin;
 readonly stagingProfile:ProfilePin;
 stage(request:SeedStagingRequest):Promise<SeedStagingResult>;
 reconcileStage(recoveryReference:string):Promise<SeedStagingResult>;
}
