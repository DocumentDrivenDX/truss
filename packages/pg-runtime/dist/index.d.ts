/** Host-only PostgreSQL driver. Portable Truss package imports no pg dependency. */
export { createFileQueryJournal, type OriginalQueryJournal } from './journal';
import type { OriginalQueryJournal } from './journal';
import { type PoolConfig } from 'pg';
import type { NativeConnectionSource } from '@documentdrivendx/truss-postgresql';
export declare function createPgConnectionSource(config: PoolConfig, options?: {
    journal?: OriginalQueryJournal;
}): {
    readonly source: NativeConnectionSource;
    readonly quarantinedCount: () => number;
    readonly close: () => Promise<void>;
};
export { decodeResponseFrame } from './wire';
export type { WireLimits } from './wire';
export { ResponseIngress } from './wire';
