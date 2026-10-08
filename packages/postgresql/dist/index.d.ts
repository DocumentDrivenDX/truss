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
