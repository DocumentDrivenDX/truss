/** Proposed CONTRACT-007 TypeScript binding; no implementation/support claim. */
export type Isolation = 'read_committed' | 'repeatable_read' | 'serializable';
export type Ownership = 'engine' | 'caller';
export type AccessMode = 'read_only' | 'read_write';
export type Durability = 'pending' | 'committed';
export type RawCell = { readonly state: 'null' } |
  { readonly state: 'text'; readonly text: string };
export type Parameter = {
  readonly position: number;
} & ({ readonly carrier: 'null'; readonly text?: never } | {
  readonly carrier: 'text' | 'integer' | 'decimal' | 'boolean' | 'json';
  readonly text: string;
});

/** Runtime validates one-based contiguous positions and exact carrier domains. */
export interface Statement {
  readonly sql: string;
  readonly parameters: readonly Parameter[];
}
export interface StatementResult {
  readonly columns: readonly string[];
  readonly rows: readonly (readonly RawCell[])[];
  /** Exact nonnegative decimal text, never a JavaScript number. */
  readonly affectedRows: string;
  readonly command: string;
}

declare const transactionBrand: unique symbol;
declare const savepointBrand: unique symbol;
export interface TransactionHandle {
  readonly [transactionBrand]: true;
  readonly ownership: Ownership;
  readonly isolation: Isolation;
  readonly accessMode: AccessMode;
}
export interface SavepointHandle {
  readonly [savepointBrand]: true;
}
export interface Cancellation {
  readonly signal: AbortSignal;
}
export interface Adoption<HostTransaction> {
  readonly hostTransaction: HostTransaction;
  readonly isolation: Isolation;
  /** Expected mode, verified against the actual host transaction; never SET implicitly. */
  readonly accessMode: AccessMode;
  readonly cancellation?: Cancellation;
}
export interface TransactionOptions {
  readonly isolation: Isolation;
  readonly accessMode: AccessMode;
  readonly cancellation?: Cancellation;
}
export interface DurableResult<T> {
  readonly value: T;
  readonly durability: Durability;
}
export type ExecutionErrorCode = 'invalid_transaction' | 'retry' |
  'transaction_unusable' | 'commit_unknown' | 'execution_obligation' | 'cancelled';
export type ExecutionFailure = {
  readonly message: string;
  readonly sqlState?: string;
} & (
  { readonly code: 'retry'; readonly retryScope: 'whole_transaction' } |
  { readonly code: 'commit_unknown'; readonly retryScope: 'none' | 'qualified_request_lookup' } |
  { readonly code: Exclude<ExecutionErrorCode, 'retry' | 'commit_unknown'>;
    readonly retryScope: 'none' }
);
export type Outcome<T> = { readonly status: 'ok'; readonly value: T } |
  { readonly status: 'error'; readonly error: ExecutionFailure };

/** HostTransaction is adapter-owned; portable core imports no driver type. */
export interface Executor<HostTransaction> {
  withTransaction<T>(options: TransactionOptions,
    callback: (transaction: TransactionHandle) => Promise<T>):
      Promise<Outcome<{ readonly value: T; readonly durability: 'committed' }>>;
  adoptTransaction(input: Adoption<HostTransaction>): Promise<Outcome<TransactionHandle>>;
  execute(transaction: TransactionHandle, statement: Statement):
    Promise<Outcome<StatementResult>>;
  savepoint(transaction: TransactionHandle): Promise<Outcome<SavepointHandle>>;
  rollbackToSavepoint(transaction: TransactionHandle, savepoint: SavepointHandle):
    Promise<Outcome<void>>;
  releaseSavepoint(transaction: TransactionHandle, savepoint: SavepointHandle):
    Promise<Outcome<void>>;
}
