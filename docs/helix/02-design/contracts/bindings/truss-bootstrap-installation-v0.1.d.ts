/** CONTRACT-008 host-authorized installation; no fresh install from runtime catalog calls. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {BootstrapGenerationResult} from './truss-bootstrap-generation-v0.1';
import type {RecoveryTargetContext} from './truss-recovery-registry-v0.1';
export interface BootstrapMarker {
 readonly interfaceVersion:'truss-bootstrap-marker/0.1.0';
 readonly installationId:string;readonly layoutVersion:string;readonly bundleSha256:string;
 readonly inventoryProfile:string;readonly inventorySha256:string;
 readonly namespace:{readonly databaseIdentity:string;readonly schemaName:string};
 readonly installedAt:string;
}
export type BootstrapAttemptContext = Extract<RecoveryTargetContext,{readonly kind:'bootstrap_attempt'}> & {
 readonly installationProfile:ProfilePin;
 readonly namespaceLockProfile:ProfilePin;
};
export type QualifiedBootstrapCandidate = Extract<BootstrapGenerationResult,{readonly outcome:'candidate'}> & {
 readonly qualification:Extract<Extract<BootstrapGenerationResult,{readonly outcome:'candidate'}>['qualification'],{readonly state:'qualified'}>;
};
export interface BootstrapInstallationRequest {
 readonly interfaceVersion:'truss-bootstrap-installation/0.1.0';
 readonly candidate:QualifiedBootstrapCandidate;
 readonly databaseIdentity:string;
 readonly installationProfile:ProfilePin;
 readonly namespaceLockProfile:ProfilePin;
}
export type BootstrapInstallationResult = {
 readonly outcome:'installed';readonly marker:BootstrapMarker;
 readonly originalAttempt:BootstrapAttemptContext;
 readonly committedInventory:ExactArtifact;readonly commitObservation:ExactArtifact;
} | {
 readonly outcome:'refused';
 readonly reason:'authorization'|'namespace_nonempty'|'profile'|'integrity'|'resource'|'registry';
 readonly containment:{readonly phase:'pre_native'} | {
  readonly phase:'preflight_terminated';readonly originalAttempt:BootstrapAttemptContext;
  readonly terminationEvidence:ExactArtifact;
 };
 readonly marker?:never;
} | {
 readonly outcome:'rolled_back';
 readonly originalAttempt:BootstrapAttemptContext;
 readonly failedStage:string;readonly terminationEvidence:ExactArtifact;
 readonly marker?:never;
} | {
 readonly outcome:'recovery_required';
 readonly reason:'application_unknown'|'cleanup_unknown';
 readonly recoveryReference:string;
 readonly originalAttempt:BootstrapAttemptContext;
 readonly originalAttemptEvidence:ExactArtifact;readonly marker?:never;
} | {
 readonly outcome:'commit_unknown';readonly recoveryReference:string;
 readonly originalAttempt:BootstrapAttemptContext;
 readonly originalAttemptEvidence:ExactArtifact;readonly marker?:never;
};
export type BootstrapReconciliationResult = Exclude<BootstrapInstallationResult,{readonly outcome:'refused'}> | {
 readonly outcome:'observation_unavailable';
 readonly reason:'authorization'|'custody'|'profile'|'integrity'|'resource';
 readonly marker?:never;readonly originalAttempt?:never;
};
export interface BootstrapInstallationTooling {
 readonly installationProfile:ProfilePin;
 /** Explicit owns-and-commits administrative transaction; never adopts a runtime transaction. */
 installFresh(request:BootstrapInstallationRequest):Promise<BootstrapInstallationResult>;
 /** Read-only original-attempt recovery; absence without termination remains unknown. */
 reconcileInstallation(recoveryReference:string):Promise<BootstrapReconciliationResult>;
}

export type BootstrapToolingConstructionResult = {
 readonly status:'ok';readonly value:BootstrapInstallationTooling;
} | {readonly status:'error';
 readonly code:'disposed'|'unsupported_profile'|'incompatible_selection';
};
/** Inert tooling projection; no namespace inspection or original-attempt issuance. */
export declare function createBootstrapInstallationTooling(
 assembly:import('./truss-reference-assembly-v0.1').ReferenceAssembly,
 selection:import('./truss-capability-readiness-v0.1').CapabilitySelection & {readonly family:'bootstrap'}
):BootstrapToolingConstructionResult;
