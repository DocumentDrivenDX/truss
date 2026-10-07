/** CONTRACT-007 private assembly/adapter integration candidate; no native support claim. */
import type {ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
declare const operationAttemptBrand: unique symbol;
export interface OperationAttempt {readonly [operationAttemptBrand]:true;}
declare const operationLeaseBrand: unique symbol;
/** Original service custody; never public reentrancy authority. */
export interface OperationLease {readonly [operationLeaseBrand]:true;}
export interface OperationArbitrationConfiguration {
 readonly interfaceVersion:'truss-operation-arbitration/0.1.0';
 readonly registryProfile:ProfilePin;
 readonly hostCoordinationProfile:ProfilePin;
 readonly recoveryProfile:ProfilePin;
 readonly resourceProfile:ProfilePin;
 readonly originalComposition:ExactArtifact;
}
export type OperationAdmissionResult =
 {readonly status:'admitted';readonly lease:OperationLease} |
 {readonly status:'refused';readonly reason:'busy'|'invalid_transaction'|'unsupported_profile'|'disposed'|'integrity'|'resource';readonly lease?:never} |
 {readonly status:'unresolved';readonly recoveryReferences:readonly [string,...string[]];readonly lease?:never};
export type OperationPreparationResult =
 {readonly status:'prepared';readonly attempt:OperationAttempt} |
 {readonly status:'refused';readonly reason:'invalid_transaction'|'unsupported_profile'|'disposed'|'integrity'|'resource';readonly attempt?:never};
export type OperationAbandonResult =
 {readonly status:'abandoned'} |
 {readonly status:'not_abandoned';readonly reason:'already_decided'|'foreign_attempt'|'integrity'};
export type OperationReleaseResult =
 {readonly status:'released'} |
 {readonly status:'unresolved';readonly recoveryReferences:readonly [string,...string[]]};
export interface HostOperationArbitration {
 readonly configuration:OperationArbitrationConfiguration;
 /** Synchronous original attempt registration; no native call or operation ownership yet. */
 prepare(assembly:ReferenceAssembly,transaction:TransactionHandle):OperationPreparationResult;
 /** Atomically acquires once for this original attempt; no SQL or host scope end. */
 acquire(attempt:OperationAttempt):Promise<OperationAdmissionResult>;
 /** Reconciles this original attempt without acquiring/replaying or minting another lease. */
 observe(attempt:OperationAttempt):Promise<OperationAdmissionResult>;
 /** Atomically closes only a still-prepared attempt; never frees an acquired lease. */
 abandonPrepared(attempt:OperationAttempt):OperationAbandonResult;
 /** Only original private protocol completion evidence may end this admission. */
 release(lease:OperationLease,originalCompletion:ExactArtifact):Promise<OperationReleaseResult>;
 /** Closes this assembly's admission, preserving other assemblies and unresolved leases. */
 closeAdmission(assembly:ReferenceAssembly):void;
}
declare const operationRegistrationBrand:unique symbol;
export interface OperationArbitrationRegistration {readonly [operationRegistrationBrand]:true;}
export type OperationArbitrationRegistrationResult =
 {readonly status:'registered';readonly registration:OperationArbitrationRegistration} |
 {readonly status:'error';readonly reason:'disposed'|'unsupported_profile'|'incompatible_service'|'already_registered'|'resource'};
/** Inert registration; same original registry across compatible assemblies/executor generations. */
export declare function registerOperationArbitration(assembly:ReferenceAssembly,
 configuration:OperationArbitrationConfiguration,originalService:HostOperationArbitration):OperationArbitrationRegistrationResult;
