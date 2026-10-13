import type { NativeConnection } from '@documentdrivendx/truss-postgresql';
import type { OrdinarySubjectObservation } from './index';
export interface OriginalSubjectKeyOwner {
    readJsonValue: (text: string, format: 'json') => unknown;
    encodeCoreKeyTuple: (source: unknown, identity: unknown, values: unknown) => unknown;
    readCoreKeyTupleBytes: (receipt: unknown, source: unknown) => Uint8Array;
}
export interface SubjectKeyBindingOptions {
    readonly host: {
        observeOrdinarySubject: (connection: NativeConnection) => OrdinarySubjectObservation;
    };
    /** Exact original owner functions; shape and output do not authenticate code. */
    readonly owner: OriginalSubjectKeyOwner;
    /** Original source-bound ontology Subject/Record/Key inspection; no issuer proof. */
    readonly inspectSubjectKey: (selection: {
        readonly sourceSha256: string;
        readonly identity: SubjectKeyBindingOptions['identity'];
    }) => undefined;
    readonly sourceText: string;
    readonly identity: {
        readonly module: string;
        readonly element: string;
        readonly key: string;
    };
    readonly keyColumns: readonly string[];
    readonly encodings: readonly ('string' | 'core-literal-json')[];
}
export interface ObservedSubjectKey {
    readonly principal: string;
    readonly sourceSha256: string;
    /** Exact observed input bytes remain available beside owner interpretation. */
    readonly observation: OrdinarySubjectObservation;
    readonly identity: SubjectKeyBindingOptions['identity'];
    readonly bytesHex: string;
    readonly originalReceiptText: string;
}
/** The trusted host selects model, ordered native mapping and original owner.
 * Returned tuple evidence is an observation, not authenticated subject issuance,
 * current authority, referenced-record existence or protected release. */
export declare function createOrdinarySubjectKeyBinding(options: SubjectKeyBindingOptions): {
    readonly encode: (connection: NativeConnection) => ObservedSubjectKey;
};
