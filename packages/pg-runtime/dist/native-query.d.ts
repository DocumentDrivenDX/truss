/** Experimental pg 8.16.3 private listener composition; not full producer/transport qualification. */
import type { PoolClient } from 'pg';
import { decodeResponseFrame } from './wire';
export declare function originalQuery(client: PoolClient, text: string, values?: readonly (string | null)[]): Promise<readonly ReturnType<typeof decodeResponseFrame>[]>;
