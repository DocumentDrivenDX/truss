/** CONTRACT-003 candidate complete accepted report; no persistence/native claim. */
import type {AcceptanceInput, AcceptanceAttemptContext, ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
import type {EnforcementReport} from './truss-enforcement-report-v0.1';
import type {HistoricalEvent, EventContext} from './truss-history-v0.1';
import type {ReadTypeReference, ReadRelationshipReference} from './truss-direct-read-v0.1';
import type {IndexJobIdentity} from './truss-index-readiness-v0.1';
export interface AcceptanceReport {
  readonly interfaceVersion: 'truss-acceptance-report/0.1.0';
  readonly reportProfile: ProfilePin;
  readonly rev: string;
  readonly originalExecution: {
    readonly installationId: string; readonly sourceEpoch: string;
    readonly origin: {
      readonly asserted: AcceptanceAttemptContext['assertedOrigin'];
      readonly databaseRole:string;
    };
    readonly journalOrigin:EventContext['origin'];
    readonly originMappingProfile:ProfilePin;
    readonly captureProfile: ProfilePin;
    readonly contextEvidence: ExactArtifact;
  };
  /** Full admitted input retained; its digest alone is not repeat equality. */
  readonly acceptedInput: AcceptanceInput;
  /** Complete original registrations referenced by acceptedInput.transforms. */
  readonly transformRegistrations:readonly {
    readonly registration:ProfilePin;readonly manifest:ExactArtifact;
    readonly originalImplementationRecognition:ExactArtifact;
  }[];
  readonly umf: readonly {
    readonly version: string;
    readonly interpretationProfile: ProfilePin;
    readonly supportedSubset: ExactArtifact;
  }[];
  readonly documents: readonly {
    readonly doc_id: string; readonly doc_revision: string;
    readonly content_sha256: string; readonly ord: string;
  }[];
  readonly diagnostics:readonly AcceptanceDiagnostic[];
  /** Producer interpretation coverage, distinct from Truss inventory scope. */
  readonly documentInterpretations:readonly {
    readonly documentId:string;
    readonly contentSha256:string;
    readonly interpretationProfile:ProfilePin;
    readonly completeness:'complete' | 'partial';
    readonly evidence:ExactArtifact;
  }[];
  readonly counts: {
    readonly typesAdded: string; readonly propertiesAdded: string;
    readonly keysAdded: string; readonly relationshipsAdded: string;
    readonly endpointsAdded: string; readonly elementsRetired: string;
  };
  readonly provisional: readonly {
    readonly type: ReadTypeReference;
    readonly via: readonly ReadRelationshipReference[];
  }[];
  readonly rebinds: readonly Extract<HistoricalEvent,{readonly operation:'rebind'}>[];
  readonly assertions: EnforcementReport & {readonly scope:{readonly kind:'complete'}};
  readonly pending_indexes: readonly IndexJobIdentity[];
  readonly losses: readonly {
    readonly source: ExactArtifact;
    readonly sourcePointer: string;
    readonly lossProfile: ProfilePin;
    readonly loss: ExactArtifact;
  }[];
  /** Retained uninterpreted content; does not silently extend required meaning. */
  readonly extensions: readonly ExactArtifact[];
}
export interface AcceptanceDiagnostic {
  readonly classification:'upstream_validation' | 'truss_admission' | 'conversion' | 'transform';
  readonly source: {readonly kind:'input'} | {
    readonly kind:'document' | 'binding'; readonly artifact: ExactArtifact;
    readonly sourcePointer: string;
  };
  readonly diagnosticProfile: ProfilePin;
  /** Preserves exact native diagnostics rather than remapping their meaning. */
  readonly diagnostic: ExactArtifact;
}
export interface AcceptanceRejection {
  readonly interfaceVersion: 'truss-acceptance-rejection/0.1.0';
  readonly reportProfile: ProfilePin;
  readonly completeness: {readonly state:'complete'} | {
    readonly state:'incomplete';
    readonly reason:'resource' | 'unsupported_profile' | 'observation' | 'transform_failure';
  };
  readonly diagnostics: readonly AcceptanceDiagnostic[];
  readonly acceptedRevision?: never;
}
/** In-transaction admission result; committed durability is an outer execution fact. */
export type AcceptanceSemanticResult = {
  readonly outcome:'accepted';
  readonly disposition:'new' | 'exact_repeat';
  readonly report: AcceptanceReport;
} | {
  readonly outcome:'rejected'; readonly rejection: AcceptanceRejection;
  readonly report?: never;
};
