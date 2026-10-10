/** CONTRACT-006/007 candidate: versioned progress throughout lifecycle. */
import type {Outcome,TransactionHandle} from './truss-execution-v0.1';
import type {FeedConsumerState} from './truss-feed-registration-v0.1';
import type {ConsumerAppliedBoundaryV02} from './truss-feed-key-transition-v0.2';
import type {FeedAdministrationRequest,FeedAdministrationResult,FeedAdministrationReceipt,
 FeedPendingAdministrationResult,FeedAdministrationObservation} from './truss-feed-administration-v0.1';
import type {SeedRestartRequest,SeedRestartResult,SeedRestartObservation} from './truss-seed-restart-v0.1';
/** Distributes over correlated variants; unrelated fields and their original semantics stay intact. */
type ReplaceField<T,K extends PropertyKey,V>=T extends unknown ? K extends keyof T ? Omit<T,K> & {[P in K]:V} : T : never;
export type FeedConsumerStateV02=Extract<FeedConsumerState,{readonly state:'awaiting_seed'}> |
 (Omit<Extract<FeedConsumerState,{readonly state:'active'}>,'applied'> & {readonly applied:ConsumerAppliedBoundaryV02});
export type FeedAdministrationRequestV02=ReplaceField<
 ReplaceField<FeedAdministrationRequest,'expectedApplied',ConsumerAppliedBoundaryV02>,
 'interfaceVersion','truss-feed-administration/0.2.0'>;
export type FeedAdministrationResultV02=ReplaceField<FeedAdministrationResult,'preservedApplied',ConsumerAppliedBoundaryV02>;
export type FeedAdministrationReceiptV02=Omit<FeedAdministrationReceipt,'interfaceVersion'|'request'|'result'> & {
 readonly interfaceVersion:'truss-feed-administration-receipt/0.2.0';
} & (
 {readonly request:Extract<FeedAdministrationRequestV02,{readonly operation:'begin_reseed'}>;
 readonly result:Extract<FeedAdministrationResultV02,{readonly outcome:'reseed_registered'}>} |
 {readonly request:Extract<FeedAdministrationRequestV02,{readonly operation:'remove_consumer'}>;
 readonly result:Extract<FeedAdministrationResultV02,{readonly outcome:'removed'}>});
export type FeedPendingAdministrationResultV02={
 readonly outcome:'reseed_registered';readonly durability:'pending';
 readonly receipt:Extract<FeedAdministrationReceiptV02,{readonly result:{readonly outcome:'reseed_registered'}}>;
} | {
 readonly outcome:'removed';readonly durability:'pending';
 readonly receipt:Extract<FeedAdministrationReceiptV02,{readonly result:{readonly outcome:'removed'}}>;
} | Exclude<FeedPendingAdministrationResult,{readonly outcome:'reseed_registered'|'removed'}>;
export type FeedAdministrationObservationV02=ReplaceField<Extract<FeedAdministrationObservation,{readonly outcome:'committed'}>,'receipt',FeedAdministrationReceiptV02> |
 Exclude<FeedAdministrationObservation,{readonly outcome:'committed'}>;
export interface FeedAdministrativeToolingV02 {
 applyInTransaction(transaction:TransactionHandle,request:FeedAdministrationRequestV02):Promise<Outcome<FeedPendingAdministrationResultV02>>;
 observeReceipt(transaction:TransactionHandle,receipt:FeedAdministrationReceiptV02):Promise<Outcome<FeedAdministrationObservationV02>>;
}
export interface SeedRestartRequestV02 extends Omit<SeedRestartRequest,'interfaceVersion'|'expectedConsumer'> {
 readonly interfaceVersion:'truss-seed-restart/0.2.0';readonly expectedConsumer:FeedConsumerStateV02;
}
export type SeedRestartResultV02=ReplaceField<Extract<SeedRestartResult,{readonly outcome:'registered'}>,'preservedConsumer',FeedConsumerStateV02> |
 (Exclude<SeedRestartResult,{readonly outcome:'registered'}> & {readonly preservedConsumer?:never;readonly admissionEvidence?:never});
export type SeedRestartObservationV02=ReplaceField<Extract<SeedRestartObservation,{readonly outcome:'current_committed'}>,'preservedConsumer',FeedConsumerStateV02> |
 (Exclude<SeedRestartObservation,{readonly outcome:'current_committed'}> & {readonly preservedConsumer?:never;readonly originalAdmission?:never;readonly observation?:never});
export interface SeedRestartToolingV02 {
 restartInTransaction(transaction:TransactionHandle,request:SeedRestartRequestV02):Promise<Outcome<SeedRestartResultV02>>;
 observeRestart(transaction:TransactionHandle,admission:Extract<SeedRestartResultV02,{readonly outcome:'registered'}>):Promise<Outcome<SeedRestartObservationV02>>;
}
export interface ReplacementSeedExtractionRequestV02 extends Omit<import('./truss-seed-extraction-v0.1').ReplacementSeedExtractionRequest,
 'interfaceVersion'|'expectedConsumer'|'reseedReceipt'> {
 readonly interfaceVersion:'truss-replacement-seed-extraction/0.2.0';
 readonly expectedConsumer:Extract<FeedConsumerStateV02,{readonly state:'active'}>;
 readonly reseedReceipt:Extract<FeedAdministrationReceiptV02,{readonly result:{readonly outcome:'reseed_registered'}}>;
}
export interface RestartedSeedExtractionRequestV02 extends Omit<import('./truss-seed-extraction-v0.1').RestartedSeedExtractionRequest,'interfaceVersion'|'restart'> {
 readonly interfaceVersion:'truss-restarted-seed-extraction/0.2.0';
 readonly restart:Extract<SeedRestartObservationV02,{readonly outcome:'current_committed'}>;
}
export interface SeedSourceConfirmationV02 {
 confirmInTransaction(transaction:TransactionHandle,request:Omit<import('./truss-seed-confirmation-v0.1').SeedConfirmationRequest,
 'interfaceVersion'|'expectedConsumer'> & {readonly interfaceVersion:'truss-seed-confirmation/0.2.0';readonly expectedConsumer:FeedConsumerStateV02}):
 Promise<Outcome<import('./truss-seed-confirmation-v0.1').SeedConfirmationResult>>;
}

export interface FeedRegistrationRequestV02 extends Omit<import('./truss-feed-registration-v0.1').FeedRegistrationRequest,'interfaceVersion'> {
 readonly interfaceVersion:'truss-feed-registration/0.2.0';
}
/** Initial awaiting-seed envelopes contain no progress; qualified native admission still selects v0.2. */
export interface FeedConsumerRegistrationV02 {
 registerInTransaction(transaction:TransactionHandle,request:FeedRegistrationRequestV02):Promise<Outcome<import('./truss-feed-registration-v0.1').FeedRegistrationResult>>;
 observeRegistration(transaction:TransactionHandle,consumer:Extract<FeedConsumerStateV02,{readonly state:'awaiting_seed'}>):Promise<Outcome<import('./truss-feed-registration-v0.1').FeedRegistrationObservation>>;
}
export interface SeedExtractionRequestV02 extends Omit<import('./truss-seed-extraction-v0.1').SeedExtractionRequest,'interfaceVersion'> {
 readonly interfaceVersion:'truss-seed-extraction/0.2.0';
}
export interface SeedExtractionToolingV02 {
 extract(request:SeedExtractionRequestV02):Promise<import('./truss-seed-extraction-v0.1').SeedExtractionResult>;
 extractReplacement(request:ReplacementSeedExtractionRequestV02):Promise<import('./truss-seed-extraction-v0.1').SeedExtractionResult>;
 extractRestarted(request:RestartedSeedExtractionRequestV02):Promise<import('./truss-seed-extraction-v0.1').SeedExtractionResult>;
}
export interface FeedLifecycleToolingV02 {
 readonly selection:import('./truss-capability-readiness-v0.1').CapabilitySelection & {readonly family:'feed'};
 readonly administration:FeedAdministrativeToolingV02;
 readonly registration:FeedConsumerRegistrationV02;
 readonly workers:import('./truss-feed-host-composition-v0.2').FeedWorkerAdministrationV02;
 readonly extraction:SeedExtractionToolingV02;
 readonly confirmation:SeedSourceConfirmationV02;
 /** Artifact/state-only envelopes reused exclusively under the captured v0.2 composition. */
 readonly abandonment:import('./truss-seed-abandonment-v0.1').SeedAbandonmentTooling;
 readonly restart:SeedRestartToolingV02;
}
export type FeedLifecycleConstructionV02={readonly status:'ok';readonly value:FeedLifecycleToolingV02} |
 {readonly status:'error';readonly code:'disposed'|'unsupported_profile'|'incompatible_selection'|'registration';readonly value?:never};
/** Inert projection; original registration must belong to this exact live assembly instance. */
export declare function createFeedLifecycleToolingV02(assembly:import('./truss-reference-assembly-v0.1').ReferenceAssembly,
 registration:import('./truss-feed-host-composition-v0.2').FeedHostCompositionRegistrationV02):FeedLifecycleConstructionV02;
