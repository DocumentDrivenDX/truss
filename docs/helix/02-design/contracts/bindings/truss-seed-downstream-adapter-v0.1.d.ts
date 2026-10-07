/** CONTRACT-006 candidate; host-owned atomic downstream activation. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {SeedActivationState} from './truss-seed-activation-v0.1';
export interface SeedActivationRequest {
 readonly interfaceVersion:'truss-seed-downstream-activation/0.1.0';
 readonly staged:Extract<SeedActivationState,{readonly state:'staged'}>;
 /** Trusted current source registration/attempt/protection observation. */
 readonly sourceAdmission:ExactArtifact;
 readonly activationProfile:ProfilePin;
}
export type SeedDownstreamActivationResult = {
 readonly outcome:'activated';
 readonly active:Extract<SeedActivationState,{readonly state:'active'}> & {
  readonly sourceConfirmation:{readonly state:'pending'};
 };
 readonly committedActivationEvidence:ExactArtifact;
} | {
 readonly outcome:'unavailable';
 readonly reason:'authorization'|'context'|'generation'|'stage'|'integrity'|'profile'|'protection'|'resource';
 readonly active?:never;
} | {
 readonly outcome:'commit_unknown';
 readonly recoveryReference:string;
 readonly originalAttemptEvidence:ExactArtifact;
 readonly active?:never;
};
export interface HostSeedDownstreamAdapter {
 readonly downstreamIdentity:string;
 readonly downstreamProfile:ProfilePin;
 readonly activationProfile:ProfilePin;
 activate(request:SeedActivationRequest):Promise<SeedDownstreamActivationResult>;
 reconcileActivation(recoveryReference:string):Promise<SeedDownstreamActivationResult>;
}
