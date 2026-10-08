export interface LocalQueryCustody {
    readonly lease: string;
    readonly ordinal: string;
}
export interface OriginalQueryJournal {
    begin(text: string, values: readonly (string | null)[], custody: LocalQueryCustody): {
        frame(bytes: Uint8Array): void;
        finish(outcome: 'response_complete' | 'server_error' | 'uncertain'): void;
    };
}
/** Explicit opt-in. Directory must already exist, be private and host-owned. Contains sensitive SQL/data. */
export declare function createFileQueryJournal(directory: string): OriginalQueryJournal;
export interface OriginalQueryInspection {
    readonly state: 'complete' | 'uncertain' | 'incomplete' | 'invalid';
    readonly originalHex: string;
    readonly request?: {
        readonly text: string;
        readonly values: readonly (string | null)[];
        readonly custody: LocalQueryCustody;
    };
    readonly frames?: readonly string[];
    readonly outcome?: 'response_complete' | 'server_error' | 'uncertain';
}
/** Bounded offline inspection only. Never returns native settlement/replay authority. */
export declare function inspectOriginalQueryFile(path: string, limits: {
    maxBytes: number;
}): OriginalQueryInspection;
