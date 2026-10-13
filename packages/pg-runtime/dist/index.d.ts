/** Host-only PostgreSQL driver. Portable Truss package imports no pg dependency. */
export { inspectOriginalQueryFile, type OriginalQueryInspection, createFileQueryJournal, type OriginalQueryJournal, type LocalQueryCustody } from './journal';
import type { OriginalQueryJournal } from './journal';
import { type PoolConfig } from 'pg';
import type { NativeConnectionSource } from '@documentdrivendx/truss-postgresql';
/** Experimental read-only subject preflight. The host must qualify the exact
 * private routine and its immutable deployment; names/shape alone are not trust.
 * It returns one ordered TEXT key tuple for SESSION_USER, or no rows. */
export interface OrdinarySubjectPreflight {
    readonly schema: string;
    readonly routine: string;
    readonly keyColumns: readonly string[];
    /** Explicit native input carrier; output keys remain TEXT. Default: text. */
    readonly actorCarrier?: 'text' | 'name';
}
/** Experimental deployment-qualified zero-argument principal observation.
 * Caller identity remains outside the definer; names alone are not trust. */
export interface OrdinaryPrincipalObserver {
    readonly schema: string;
    readonly routine: string;
}
export declare function createPgConnectionSource(config: PoolConfig, options?: {
    journal?: OriginalQueryJournal;
    ordinaryPrincipal?: string;
    ordinarySubject?: OrdinarySubjectPreflight;
    ordinaryPrincipalObserver?: OrdinaryPrincipalObserver;
    originalResponseTimeoutMs?: number;
}): {
    readonly source: NativeConnectionSource;
    readonly quarantinedCount: () => number;
    readonly close: () => Promise<void>;
    /** Explicit transport shutdown only; uncertain native outcomes remain unresolved. */
    readonly shutdownQuarantinedTransports: () => Promise<void>;
};
export { decodeResponseFrame } from './wire';
export type { WireLimits } from './wire';
export { ResponseIngress } from './wire';
