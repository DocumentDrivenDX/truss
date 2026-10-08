export interface OriginalQueryJournal {
    begin(text: string, values: readonly (string | null)[]): {
        frame(bytes: Uint8Array): void;
        finish(outcome: 'response_complete' | 'server_error' | 'uncertain'): void;
    };
}
/** Explicit opt-in. Directory must already exist, be private and host-owned. Contains sensitive SQL/data. */
export declare function createFileQueryJournal(directory: string): OriginalQueryJournal;
