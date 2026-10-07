/** CONTRACT-002 candidate; evidence authority is established by the host. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
import type {HistoricalRecord, TypedIdentity} from './truss-history-v0.1';
export interface ReconstructionRequest {
  /** Recorded historical interpretation; no implicit current-catalog reinterpretation. */
  readonly interfaceVersion: 'truss-history-reconstruction/0.1.0';
  readonly sourceEpoch: string;
  readonly historyProfile: ProfilePin;
  readonly identity: TypedIdentity;
  readonly version: string;
}
export interface ReconstructionEvidence {
  readonly baselineSha256: string;
  readonly eventInventorySha256: string;
  readonly definitionInventorySha256: string;
  readonly procedureProfile: ProfilePin;
  readonly observationEvidenceSha256: string;
}
export type ReconstructionResult = {
  readonly outcome: 'reconstructed'; readonly request: ReconstructionRequest;
  readonly record: HistoricalRecord; readonly evidence: ReconstructionEvidence;
} | {
  readonly outcome: 'deleted'; readonly request: ReconstructionRequest;
  readonly deletionVersion: string; readonly evidence: ReconstructionEvidence;
  readonly record?: never;
} | {
  readonly outcome: 'unwritten'; readonly request: ReconstructionRequest;
  readonly nonexistenceEvidenceSha256: string;
  readonly record?: never;
} | {
  readonly outcome: 'not_found'; readonly record?: never;
  readonly request?: never;
} | {
  readonly outcome: 'history_unavailable';
  readonly reason: 'baseline' | 'events' | 'definitions' | 'retention' | 'profile' | 'observation';
  readonly record?: never;
} | {
  readonly outcome: 'unsupported'; readonly requiredMeaning: string;
  readonly record?: never;
};
