/** CONTRACT-006 proposed explicit extraction tooling; no implicit assembly worker. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {SeedAttemptIdentity} from './truss-seed-activation-v0.1';
import type {SeedRestartObservation} from './truss-seed-restart-v0.1';
import type {FeedRegistrationObservation} from './truss-feed-registration-v0.1';
import type {FeedConsumerState} from './truss-feed-registration-v0.1';
import type {FeedAdministrationReceipt,FeedAdministrationRequest,FeedAdministrationResult} from './truss-feed-administration-v0.1';
export interface SeedExtractionRequest {
 readonly interfaceVersion:'truss-seed-extraction/0.1.0';
 readonly registration:Extract<FeedRegistrationObservation,{readonly outcome:'current_committed'}>;
 readonly extractionProfile:ProfilePin;
 readonly activationProfile:ProfilePin;
 readonly limits:{readonly encodedBytes:string;readonly records:string};
}
export interface ReplacementSeedExtractionRequest extends Omit<SeedExtractionRequest,'registration'|'interfaceVersion'> {
 readonly interfaceVersion:'truss-replacement-seed-extraction/0.1.0';
 readonly expectedConsumer:Extract<FeedConsumerState,{readonly state:'active'}>;
 readonly reseedReceipt:Omit<FeedAdministrationReceipt,'request'|'result'> & {
  readonly request:Extract<FeedAdministrationRequest,{readonly operation:'begin_reseed'}>;
  readonly result:Extract<FeedAdministrationResult,{readonly outcome:'reseed_registered'}>;
 };
}
export interface RestartedSeedExtractionRequest extends Omit<SeedExtractionRequest,'registration'|'interfaceVersion'> {
 readonly interfaceVersion:'truss-restarted-seed-extraction/0.1.0';
 readonly restart:Extract<SeedRestartObservation,{readonly outcome:'current_committed'}>;
}
export type SeedExtractionResult = {
 readonly outcome:'extracted';
 readonly attempt:SeedAttemptIdentity;
 readonly baseline:ExactArtifact;
 readonly visibility:ExactArtifact;
 readonly inventory:ExactArtifact;
 readonly inclusiveReplayXmin:string;
 readonly extractionEvidence:ExactArtifact;
 /** Only snapshot resources owned by this invocation are released. */
 readonly ownedSnapshotReleased:true;
} | {
 readonly outcome:'unavailable';
 readonly reason:'authorization'|'context'|'generation'|'profile'|'protection'|'snapshot'|'integrity'|'resource';
 readonly baseline?:never;
 readonly visibility?:never;
 readonly inventory?:never;
} | {
 readonly outcome:'recovery_required';
 readonly recoveryReference:string;
 readonly originalAttemptEvidence:ExactArtifact;
 readonly baseline?:never;
 readonly visibility?:never;
 readonly inventory?:never;
};
export interface SeedExtractionTooling {
 extract(request:SeedExtractionRequest):Promise<SeedExtractionResult>;
 extractReplacement(request:ReplacementSeedExtractionRequest):Promise<SeedExtractionResult>;
 extractRestarted(request:RestartedSeedExtractionRequest):Promise<SeedExtractionResult>;
}
