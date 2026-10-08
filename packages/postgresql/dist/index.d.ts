/** Inert construction only. No native capability, profile or permission is inferred. */
import type { ReferenceAssemblyConfiguration, AssemblyConstructionResult } from './contracts/truss-reference-assembly-v0.1';
import type { Executor } from './contracts/truss-execution-v0.1';
import type { ProfilePin } from './contracts/truss-acceptance-input-v0.1';
import type { HostRecoveryRegistry } from './contracts/truss-recovery-registry-v0.1';
import type { HostRequestNamespaceAuthority } from './contracts/truss-request-namespace-v0.1';
import type { FeedProofVerifierRegistration } from './contracts/truss-feed-proof-verifier-v0.1';
export type { ReferenceAssemblyConfiguration, ReferenceAssembly, AssemblyConstructionResult, AssemblyDisposalRequest, AssemblyDisposalResult } from './contracts/truss-reference-assembly-v0.1';
export type { Executor, TransactionHandle, SavepointHandle, Statement, StatementResult, Outcome } from './contracts/truss-execution-v0.1';
export type { CapabilitySelection, CapabilityReadiness } from './contracts/truss-capability-readiness-v0.1';
export type { ProfilePin } from './contracts/truss-acceptance-input-v0.1';
export type { HostRecoveryRegistry } from './contracts/truss-recovery-registry-v0.1';
export declare const INERT_ASSEMBLY_PROFILE: ProfilePin;
export declare function createReferenceAssembly<HostTransaction>(input: ReferenceAssemblyConfiguration, executor: Executor<HostTransaction>, services: {
    readonly recoveryRegistry: HostRecoveryRegistry;
    readonly feedProofVerifiers?: readonly FeedProofVerifierRegistration[];
    readonly requestNamespaceAuthority?: HostRequestNamespaceAuthority;
}): AssemblyConstructionResult;
/** CONTRACT-008 proposed native-output grammar only; caller admits field semantics. */
export type NativeVectorFamily = 'oidvector' | 'int2vector';
export interface NativeVectorLimits {
    readonly maxBytes: number;
    readonly maxTokens: number;
    readonly ledger?: NativeDecodeBudget;
}
export interface NativeVector {
    readonly family: NativeVectorFamily;
    readonly originalText: string;
    readonly tokens: readonly string[];
}
export declare class NativeVectorError extends Error {
    readonly code: 'output-grammar' | 'native-domain' | 'resource-limit' | 'count-correspondence';
    constructor(code: 'output-grammar' | 'native-domain' | 'resource-limit' | 'count-correspondence');
}
/** ASCII grammar makes admitted byte count equal to code-unit count. No normalization. */
export declare function decodeNativeVector(family: NativeVectorFamily, text: string, limits: NativeVectorLimits, declaredCount?: string): NativeVector;
export type NativeArrayElement = string | null | readonly NativeArrayElement[];
export type NativeArray = {
    readonly kind: 'native-null';
    readonly originalText: null;
} | {
    readonly kind: 'array';
    readonly originalText: string;
    readonly bounds: readonly (readonly [string, string])[];
    readonly elements: readonly NativeArrayElement[];
};
export interface NativeArrayLimits {
    readonly maxBytes: number;
    readonly maxNodes: number;
    readonly maxDepth: number;
    readonly ledger?: NativeDecodeBudget;
}
/** Selected comma-delimited text element output. Type/ACL authority is independently admitted. */
export declare function decodeNativeTextArray(text: string | null, dimensions: string | null, limits: NativeArrayLimits): NativeArray;
export interface NativeTriggerArguments {
    readonly count: string;
    readonly byteLength: string;
    readonly originalHex: string;
    readonly encoding: 'UTF8';
    readonly arguments: readonly string[];
}
/** CONTRACT-008 exact tgargs framing. No trigger definition or callable authority inferred. */
export declare function decodeNativeTriggerArguments(count: string, hex: string | null, byteLength: string | null, limits: {
    readonly maxBytes: number;
    readonly maxArguments: number;
}, encoding: 'UTF8'): NativeTriggerArguments;
export interface NativeRoutineCarrier {
    readonly originalCatalogRowJson: string;
    readonly inputCount: string;
    readonly inputTypesText: string;
    readonly inputTypesDimensions: string;
    readonly names: {
        readonly text: string | null;
        readonly dimensions: string | null;
        readonly rawJson: string;
    };
    readonly modes: {
        readonly text: string | null;
        readonly dimensions: string | null;
        readonly rawJson: string;
    };
    readonly settings: {
        readonly text: string | null;
        readonly dimensions: string | null;
        readonly rawJson: string;
    };
}
/** Composition of selected carrier codecs; full raw row is opaque custody, not accepted semantics. */
export declare function decodeNativeRoutineCarriers(input: NativeRoutineCarrier, limits: NativeArrayLimits & {
    readonly maxTokens: number;
}): {
    readonly originalCatalogRowJson: string;
    readonly inputTypes: NativeVector;
    readonly names: NativeArray;
    readonly modes: NativeArray;
    readonly settings: NativeArray;
};
/** Aggregate decode-accounting subset; transport/deadline/containment remain separate. */
export declare class NativeDecodeBudget {
    #private;
    readonly maxBytes: number;
    readonly maxNodes: number;
    constructor(maxBytes: number, maxNodes: number);
    reserve(bytes: number, nodes: number): void;
    get remaining(): {
        readonly bytes: number;
        readonly nodes: number;
        readonly exhausted: boolean;
    };
}
