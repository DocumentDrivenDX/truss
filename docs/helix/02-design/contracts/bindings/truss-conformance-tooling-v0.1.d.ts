/** CONTRACT-011 explicit host runner/custody; importing declarations starts no tests. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
export interface ConformanceRunRequest {
 readonly interfaceVersion:'truss-conformance-run/0.1.0';
 readonly procedureProfile:ProfilePin;
 readonly requiredManifest:ExactArtifact;
 readonly inputInventory:ExactArtifact;
 /** Host-issued registered environment custody; not a connection string or shell command. */
 readonly environmentReference:string;
 readonly resourceProfile:ProfilePin;
 readonly signal?:AbortSignal;
}
declare const preparedRunBrand:unique symbol;
export interface PreparedConformanceRun {
 readonly [preparedRunBrand]:true;
 /** Original issuer-bound recovery correlation, never run authority by itself. */
 readonly recoveryReference:string;
}
export type ConformancePreparationResult={readonly outcome:'prepared';readonly run:PreparedConformanceRun} |
 {readonly outcome:'unavailable';readonly reason:'authorization'|'profile'|'custody'|'resource'|'cancelled';readonly run?:never};
export type ConformancePreparedCleanupResult={readonly outcome:'abandoned'} |
 {readonly outcome:'not_abandoned';readonly recoveryReference:string} |
 {readonly outcome:'unavailable';readonly reason:'authorization'|'profile'|'custody'|'integrity'};
export type ConformanceRunResult={
 readonly outcome:'recorded';
 /** Exact CONTRACT-011 receipt; may truthfully include failed/skipped/not-run cases. */
 readonly receipt:ExactArtifact;
} | {readonly outcome:'unavailable';
 readonly reason:'authorization'|'profile'|'custody'|'resource';readonly receipt?:never;
} | {readonly outcome:'interrupted';
 readonly originalRunEvidence:ExactArtifact;
 readonly recoveryReference:string;
};
export type ConformanceReconciliationResult=ConformanceRunResult |
 {readonly outcome:'prepared';readonly run:PreparedConformanceRun} |
 {readonly outcome:'abandoned';readonly originalPreparation:ExactArtifact;readonly originalClosure:ExactArtifact};
export type ConformanceAssessment={
 readonly state:'qualified';readonly receipt:ExactArtifact;
 readonly requiredManifest:ExactArtifact;readonly qualificationProfile:ProfilePin;
 readonly assessmentEvidence:ExactArtifact;
} | {readonly state:'unqualified';readonly diagnostics:ExactArtifact} |
 {readonly state:'unavailable';readonly reason:'authorization'|'profile'|'custody'|'integrity'|'resource'};
export interface HostConformanceRunner {
 readonly runnerProfile:ProfilePin;
 readonly resourceProfile:ProfilePin;
 /** Admit/register original request and recovery before acquiring native/environment resources. */
 prepareRun(request:ConformanceRunRequest):Promise<ConformancePreparationResult>;
 /** Starts at most once for this original prepared run; never accepts a replacement request. */
 run(prepared:PreparedConformanceRun):Promise<ConformanceRunResult>;
 /** Closes only still-prepared original work; never cancels/frees a claimed native run. */
 abandonPreparedRun(prepared:PreparedConformanceRun):Promise<ConformancePreparedCleanupResult>;
 /** Observes original state; prepared observation never starts cases or remints a claim. */
 reconcileRun(recoveryReference:string):Promise<ConformanceReconciliationResult>;
}
export interface ConformanceEvidenceTooling {
 assess(receipt:ExactArtifact,requiredManifest:ExactArtifact,qualificationProfile:ProfilePin):Promise<ConformanceAssessment>;
}

export interface HostConformanceAssessor extends ConformanceEvidenceTooling {
 readonly assessorProfile:ProfilePin;
 readonly resourceProfile:ProfilePin;
}
export interface ConformanceEvidenceConfiguration {
 readonly interfaceVersion:'truss-conformance-evidence/0.1.0';
 readonly assessorProfile:ProfilePin;readonly resourceProfile:ProfilePin;
 readonly approvedManifests:readonly [{readonly qualificationProfile:ProfilePin;readonly manifest:ExactArtifact},
  ...{readonly qualificationProfile:ProfilePin;readonly manifest:ExactArtifact}[]];
}
export type ConformanceEvidenceConstructionResult={readonly status:'ok';readonly value:ConformanceEvidenceTooling} |
 {readonly status:'error';readonly code:'invalid_configuration'|'unsupported_profile'|'incompatible_service'};
/** Inert host-service binding; no runner, resource creation or artifact resolution. */
export declare function createConformanceEvidenceTooling(
 configuration:ConformanceEvidenceConfiguration,
 hostAssessor:HostConformanceAssessor
):ConformanceEvidenceConstructionResult;

export type ConformanceRunTooling=Pick<HostConformanceRunner,
 'prepareRun'|'run'|'abandonPreparedRun'|'reconcileRun'>;
export interface ConformanceRunConfiguration {
 readonly interfaceVersion:'truss-conformance-runner/0.1.0';
 readonly runnerProfile:ProfilePin;readonly resourceProfile:ProfilePin;
 readonly originalComposition:ExactArtifact;
 readonly approvedManifests:readonly [{readonly qualificationProfile:ProfilePin;readonly manifest:ExactArtifact},
 ...{readonly qualificationProfile:ProfilePin;readonly manifest:ExactArtifact}[]];
 readonly approvedEnvironmentReferences:readonly [string,...string[]];
}
export type ConformanceRunConstructionResult={readonly status:'ok';readonly value:ConformanceRunTooling} |
 {readonly status:'error';readonly code:'invalid_configuration'|'unsupported_profile'|'incompatible_service'};
/** Inert original-service projection; no artifact resolution, environment acquisition or run. */
export declare function createConformanceRunTooling(configuration:ConformanceRunConfiguration,
 originalHostRunner:HostConformanceRunner):ConformanceRunConstructionResult;
