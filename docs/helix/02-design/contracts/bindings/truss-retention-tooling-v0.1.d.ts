/** CONTRACT-006 explicit retention; submitted evidence is not a reusable drop permit. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {Outcome,TransactionHandle} from './truss-execution-v0.1';
export interface RetentionDropRequest {
 readonly interfaceVersion:'truss-retention-drop/0.1.0';
 readonly sourceEpoch:string;readonly installationId:string;
 readonly procedureProfile:ProfilePin;
 readonly candidateInventory:ExactArtifact;
 readonly expectedRetainedHorizon:ExactArtifact;
}
export type RetentionDropResult={
 readonly outcome:'dropped';readonly durability:'pending';
 readonly originalRequest:RetentionDropRequest;
 readonly droppedInventory:ExactArtifact;
 readonly originalProtectionObservation:ExactArtifact;
 readonly resultingRetainedHorizon:ExactArtifact;
} | {readonly outcome:'refused';
 readonly reason:'authorization'|'affinity'|'profile'|'integrity'|'protected'|'changed'|'resource';
 readonly droppedInventory?:never;readonly resultingRetainedHorizon?:never;
};
export interface RetentionTooling {
 dropInTransaction(transaction:TransactionHandle,request:RetentionDropRequest):Promise<Outcome<RetentionDropResult>>;
}
export type RetentionConstructionResult={readonly status:'ok';readonly value:RetentionTooling} |
 {readonly status:'error';readonly code:'disposed'|'unsupported_profile'|'incompatible_selection'};
export declare function createRetentionTooling(
 assembly:import('./truss-reference-assembly-v0.1').ReferenceAssembly,
 selection:import('./truss-capability-readiness-v0.1').CapabilitySelection & {readonly family:'feed'}
):RetentionConstructionResult;
