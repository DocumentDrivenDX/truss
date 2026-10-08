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
