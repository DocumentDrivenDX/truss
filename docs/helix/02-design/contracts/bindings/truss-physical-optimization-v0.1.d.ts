/** PRD P2 explicit optional tooling; no automatic catalog-acceptance DDL. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {TransactionHandle,Outcome} from './truss-execution-v0.1';
export interface PhysicalOptimizationRequest {
 readonly interfaceVersion:'truss-physical-optimization/0.1.0';
 readonly kind:'index'|'extended_statistics'|'typed_view';
 readonly declaration:ExactArtifact;readonly declarationProfile:ProfilePin;
 readonly expectedInstalledInventory:ExactArtifact;
 readonly budget:{readonly profile:ProfilePin;readonly maxIndexCount:string;readonly maxIndexBytes:string};
}
export interface PhysicalIndexBudgetObservation {
 readonly interfaceVersion:'truss-physical-index-budget/0.1.0';
 readonly profile:ProfilePin;
 readonly countedInventory:ExactArtifact;
 readonly before:{readonly indexCount:string;readonly measuredBytes:string;readonly observation:ExactArtifact};
 readonly admission:{readonly proposedCount:string;readonly totalByteUpperBound:string;
  readonly method:ProfilePin;readonly evidence:ExactArtifact};
 readonly after:{readonly indexCount:string;readonly measuredBytes:string;readonly observation:ExactArtifact};
 /** Observation is for this supplied scope, not future growth or confirmed commit. */
 readonly scope:'supplied_transaction';
}
export type PhysicalOptimizationResult = {
 readonly outcome:'pending';readonly durability:'pending';
 readonly originalRequest:PhysicalOptimizationRequest;
 readonly admittedPlan:ExactArtifact;readonly ownedObjectInventory:ExactArtifact;
 readonly resultingInventory:ExactArtifact;
 readonly budgetObservation:PhysicalIndexBudgetObservation;
} | {readonly outcome:'refused';
 readonly reason:'authorization'|'affinity'|'inventory_changed'|'profile'|'integrity'|'budget'|'nontransactional';
 readonly admittedPlan?:never;
};
export interface PhysicalOptimizationTooling {
 applyInTransaction(transaction:TransactionHandle,request:PhysicalOptimizationRequest):Promise<Outcome<PhysicalOptimizationResult>>;
}
export type PhysicalOptimizationConstructionResult={readonly status:'ok';readonly value:PhysicalOptimizationTooling} |
 {readonly status:'error';readonly code:'disposed'|'unsupported_profile'|'incompatible_selection'};
export declare function createPhysicalOptimizationTooling(
 assembly:import('./truss-reference-assembly-v0.1').ReferenceAssembly,
 selection:import('./truss-capability-readiness-v0.1').CapabilitySelection & {readonly family:'physical_optimization'}
):PhysicalOptimizationConstructionResult;
