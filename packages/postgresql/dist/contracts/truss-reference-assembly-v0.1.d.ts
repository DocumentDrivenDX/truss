/** CONTRACT-007 draft construction/lifetime boundary; no runtime implementation. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
import type {Executor, Outcome} from './truss-execution-v0.1';
import type {CapabilitySelection, CapabilityReadiness} from './truss-capability-readiness-v0.1';
import type {HostRequestNamespaceAuthority} from './truss-request-namespace-v0.1';
import type {HostRecoveryRegistry} from './truss-recovery-registry-v0.1';
import type {FeedProofVerifierRegistration} from './truss-feed-proof-verifier-v0.1';
import type {DirectReadCapabilityResult} from './truss-direct-read-capability-v0.1';
import type {CatalogCapabilityResult} from './truss-catalog-capability-v0.1';
import type {GroupCapabilityResult} from './truss-group-capability-v0.1';
import type {MutationCapabilityResult} from './truss-mutation-capability-v0.1';
import type {ImportCapabilityResult} from './truss-import-capability-v0.1';
import type {HistoryCapabilityResult} from './truss-history-capability-v0.1';
import type {FeedCapabilityResult} from './truss-feed-capability-v0.1';
import type {CompiledExecutionCapabilityResult} from './truss-compiled-execution-capability-v0.1';
export interface ReferenceAssemblyConfiguration {
  readonly interfaceVersion: 'truss-reference-assembly/0.1.0';
  /** Host-issued correlation identity; never graph identity or authority. */
  readonly assemblyId: string;
  readonly assemblyProfile: ProfilePin;
  readonly recovery: {
    readonly registryProfile: ProfilePin;
    readonly retention: 'process_lifetime' | 'restart_durable';
  };
  /** Optional explicit replay setup; absence leaves request-free groups independent. */
  readonly requestReplay?:{readonly namespaceAuthorityProfile:ProfilePin};
  readonly databaseIdentity: string;
  readonly schema: string;
  readonly capabilities: readonly [CapabilitySelection, ...CapabilitySelection[]];
}
export interface AssemblyDisposalRequest {
  /** Cancels waiting only; closing admission cannot be undone. */
  readonly signal?: AbortSignal;
}
export type AssemblyDisposalResult = {
  readonly state: 'disposed';
  readonly ownedResourcesReleased: true;
} | {
  readonly state: 'quarantined';
  readonly ownedResourcesReleased: false;
  readonly reason: 'native_work_unresolved' | 'release_unconfirmed' | 'wait_cancelled';
  /** Trusted host recovery registry references, not reusable resource handles. */
  readonly recoveryReferences: readonly [string, ...string[]];
};
export interface ReferenceAssembly {
  readonly configuration: ReferenceAssemblyConfiguration;
  /** Inert handle selection; readiness/authority still checked per operation. */
  directReads(selection: CapabilitySelection & {readonly family: 'direct_read'}): DirectReadCapabilityResult;
  catalog(selection: CapabilitySelection & {readonly family:'catalog'}): CatalogCapabilityResult;
  groups(selection: CapabilitySelection & {readonly family:'group'}): GroupCapabilityResult;
  mutations(selection:CapabilitySelection & {readonly family:'mutation'}):MutationCapabilityResult;
  imports(selection:CapabilitySelection & {readonly family:'import'}):ImportCapabilityResult;
  history(selection:CapabilitySelection & {readonly family:'history'}):HistoryCapabilityResult;
  feed(selection:CapabilitySelection & {readonly family:'feed'}):FeedCapabilityResult;
  compiledExecution(selection:CapabilitySelection & {readonly family:'weft_execution'}):CompiledExecutionCapabilityResult;
  /** Explicit I/O; readiness never substitutes for per-operation admission. */
  observeReadiness(selection: CapabilitySelection): Promise<Outcome<CapabilityReadiness>>;
  /** Idempotently closes admission; never ends host-owned transactions/resources. */
  dispose(request: AssemblyDisposalRequest): Promise<AssemblyDisposalResult>;
}
export type AssemblyConstructionResult = {
  readonly status: 'ok'; readonly value: ReferenceAssembly;
} | {
  readonly status: 'error';
  readonly code: 'invalid_configuration' | 'unsupported_profile' | 'incompatible_selection';
  readonly path?: string;
  readonly diagnosticProfile: ProfilePin;
};
/** Synchronous, inert construction; invalid configuration fails before I/O. */
export declare function createReferenceAssembly<HostTransaction>(
  configuration: ReferenceAssemblyConfiguration,
  executor: Executor<HostTransaction>,
  hostServices: {readonly recoveryRegistry: HostRecoveryRegistry;
    readonly feedProofVerifiers?:readonly FeedProofVerifierRegistration[];
    readonly requestNamespaceAuthority?:HostRequestNamespaceAuthority}
): AssemblyConstructionResult;
