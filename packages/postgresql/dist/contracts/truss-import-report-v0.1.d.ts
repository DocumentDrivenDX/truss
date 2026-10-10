/** CONTRACT-004/007 candidate; index coverage and counts need semantic validation. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
import type {TypedIdentity} from './truss-history-v0.1';
import type {SelectedMutationConfiguration} from './truss-mutation-configuration-v0.1';
interface IndexedOutcome { readonly inputIndex: string; readonly batchId: string }
export type ImportRecordOutcome = IndexedOutcome & ({
  readonly outcome: 'created'; readonly identity: TypedIdentity; readonly version: string;
} | {
  readonly outcome: 'skipped'; readonly reason: 'live_identity' | 'reserved_identity';
  readonly identity?: TypedIdentity;
} | {
  readonly outcome: 'rejected'; readonly code: string; readonly path?: string;
} | {
  /** Submitted to the writer, but no confirmed application/rejection result was observed. */
  readonly outcome: 'attempt_unknown'; readonly recoveryReference: string;
  readonly identity?: TypedIdentity;
});
interface Batch { readonly batchId: string; readonly inputIndices: readonly [string, ...string[]] }
export type ImportBatchDisposition = Batch & ({
  readonly disposition: 'committed'; readonly commitEvidenceSha256: string;
} | {
  readonly disposition: 'pending'; readonly hostTransactionId: string;
} | {
  readonly disposition: 'rolled_back'; readonly rollbackEvidenceSha256: string;
} | {
  readonly disposition: 'commit_unknown'; readonly recoveryReference: string;
} | {
  /** Cleanup/transaction termination remains unresolved; commit may not have been sent. */
  readonly disposition: 'transaction_unresolved'; readonly recoveryReference: string;
});
export interface ImportReport {
  readonly interfaceVersion: 'truss-import-report/0.1.0';
  readonly attemptId: string;
  readonly inputCount: string;
  readonly executedCatalogRevision: string;
  readonly importProfile: ProfilePin;
  /** Selected once for the attempt; actual per-batch admission needs trusted evidence. */
  readonly selectedConfiguration: SelectedMutationConfiguration;
  readonly inputSha256: string;
  readonly execution: 'engine_owned' | 'host_adopted' | 'outer_engine_scope';
  readonly status: 'processed' | 'interrupted';
  /** Original input order. Observed creation does not establish committed durability. */
  readonly outcomes: readonly ImportRecordOutcome[];
  readonly batches: readonly ImportBatchDisposition[];
  readonly unprocessedIndices: readonly string[];
  readonly counts: {
    readonly createdCommitted: string; readonly createdPending: string;
    readonly createdRolledBack: string; readonly createdCommitUnknown: string;
    readonly createdTransactionUnresolved: string; readonly attemptUnknown: string;
    readonly skipped: string; readonly rejected: string; readonly unprocessed: string;
  };
}
