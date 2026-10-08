/** Host-only PostgreSQL driver. Portable Truss package imports no pg dependency. */
import { type PoolConfig } from 'pg';
import type { NativeConnectionSource } from '@documentdrivendx/truss-postgresql';
export declare function createPgConnectionSource(config: PoolConfig): {
    readonly source: NativeConnectionSource;
    readonly quarantinedCount: () => number;
    readonly close: () => Promise<void>;
};
