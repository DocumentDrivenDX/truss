/** CONTRACT-003/007 candidate explicit postcommit jobs; no constructor-started worker. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {Outcome,TransactionHandle} from './truss-execution-v0.1';
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {IndexDispatchRequest,IndexAttemptIdentity,IndexReadiness,IndexJobIdentity} from './truss-index-readiness-v0.1';
import type {StatisticsJobIdentity,StatisticsAttemptIdentity,StatisticsReadiness} from './truss-statistics-readiness-v0.1';
export interface StatisticsDispatchRequest {
 readonly job:StatisticsJobIdentity;readonly expectedGeneration:string;
 readonly committedAcceptanceEvidenceSha256:string;
}
declare const pendingIndexBrand:unique symbol;declare const committedIndexBrand:unique symbol;
declare const pendingStatisticsBrand:unique symbol;declare const committedStatisticsBrand:unique symbol;
export interface PendingIndexAdmission {readonly [pendingIndexBrand]:true;readonly durability:'pending';readonly attempt:IndexAttemptIdentity;readonly evidence:ExactArtifact;}
export interface CommittedIndexAdmission {readonly [committedIndexBrand]:true;readonly durability:'committed';readonly attempt:IndexAttemptIdentity;readonly observation:ExactArtifact;}
export interface PendingStatisticsAdmission {readonly [pendingStatisticsBrand]:true;readonly durability:'pending';readonly attempt:StatisticsAttemptIdentity;readonly evidence:ExactArtifact;}
export interface CommittedStatisticsAdmission {readonly [committedStatisticsBrand]:true;readonly durability:'committed';readonly attempt:StatisticsAttemptIdentity;readonly observation:ExactArtifact;}
export type JobAdmission<T>={readonly outcome:'admitted';readonly admission:T}|{readonly outcome:'unavailable';readonly reason:'authority'|'profile'|'context'|'generation'|'observation'|'disposed';readonly admission?:never};
export type JobObservation<T>={readonly outcome:'observed';readonly readiness:T}|{readonly outcome:'unavailable';readonly reason:'authority'|'profile'|'context'|'observation'|'disposed';readonly readiness?:never};
export interface PhysicalJobTooling {
 admitIndexInTransaction(transaction:TransactionHandle,request:IndexDispatchRequest):Promise<Outcome<JobAdmission<PendingIndexAdmission>>>;
 observeIndexAdmission(transaction:TransactionHandle,original:PendingIndexAdmission):Promise<Outcome<JobAdmission<CommittedIndexAdmission>>>;
 runIndexAttempt(original:CommittedIndexAdmission):Promise<Outcome<JobObservation<IndexReadiness>>>;
 observeIndex(transaction:TransactionHandle,job:IndexJobIdentity):Promise<Outcome<JobObservation<IndexReadiness>>>;
 admitStatisticsInTransaction(transaction:TransactionHandle,request:StatisticsDispatchRequest):Promise<Outcome<JobAdmission<PendingStatisticsAdmission>>>;
 observeStatisticsAdmission(transaction:TransactionHandle,original:PendingStatisticsAdmission):Promise<Outcome<JobAdmission<CommittedStatisticsAdmission>>>;
 runStatisticsAttempt(original:CommittedStatisticsAdmission):Promise<Outcome<JobObservation<StatisticsReadiness>>>;
 observeStatistics(transaction:TransactionHandle,job:StatisticsJobIdentity):Promise<Outcome<JobObservation<StatisticsReadiness>>>;
}
export type PhysicalJobConstructionResult={readonly status:'ok';readonly value:PhysicalJobTooling}|{readonly status:'error';readonly code:'disposed'|'unsupported_profile'|'incompatible_selection'|'missing_service'};
/** Inert projection of original assembly administrative/native job services. */
export declare function createPhysicalJobTooling(assembly:ReferenceAssembly,
 selection:CapabilitySelection & {readonly family:'physical_optimization'},jobProfile:ProfilePin):PhysicalJobConstructionResult;

export interface PhysicalJobServiceConfiguration {
 readonly selection:CapabilitySelection & {readonly family:'physical_optimization'};
 readonly jobProfile:ProfilePin;readonly originalComposition:ExactArtifact;
 readonly queueProfile:ProfilePin;readonly admissionObservationProfile:ProfilePin;
 readonly nativeExecutionProfile:ProfilePin;readonly resourceProfile:ProfilePin;
 readonly recoveryProfile:ProfilePin;
}
/** Original administrative/native adapter; no assembly construction side effects. */
export interface HostPhysicalJobService extends PhysicalJobTooling {
 readonly configuration:PhysicalJobServiceConfiguration;
}
declare const physicalJobRegistrationBrand:unique symbol;
export interface PhysicalJobServiceRegistration {
 readonly [physicalJobRegistrationBrand]:true;
 readonly configuration:PhysicalJobServiceConfiguration;
}
export type PhysicalJobServiceRegistrationResult={readonly status:'ok';readonly registration:PhysicalJobServiceRegistration}|
 {readonly status:'error';readonly code:'disposed'|'unsupported_profile'|'incompatible_selection'|'already_registered';readonly registration?:never};
export declare function registerPhysicalJobService(assembly:ReferenceAssembly,
 configuration:PhysicalJobServiceConfiguration,service:HostPhysicalJobService):PhysicalJobServiceRegistrationResult;
