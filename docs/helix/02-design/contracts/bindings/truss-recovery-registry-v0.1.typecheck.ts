/** Design-only consumer witnesses; no registry/native behavior claim. */
import type {RecoveryTargetContext, HostRecoveryRegistry} from './truss-recovery-registry-v0.1';
import type {Executor} from './truss-execution-v0.1';
import {createReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {ReferenceAssemblyConfiguration} from './truss-reference-assembly-v0.1';
declare const configuration: ReferenceAssemblyConfiguration;
declare const executor: Executor<unknown>;
declare const registry: HostRecoveryRegistry;
createReferenceAssembly(configuration, executor, {recoveryRegistry: registry});
// @ts-expect-error Host registry is an explicit dependency, not a global default.
createReferenceAssembly(configuration, executor);
const installed: RecoveryTargetContext = {
  kind: 'installed', databaseIdentity: 'db', schemaName: 'truss',
  installationId: 'installation', sourceEpoch: 'epoch'
};
void installed;
// @ts-expect-error Installed context cannot omit the epoch.
const incomplete: RecoveryTargetContext = {kind: 'installed', databaseIdentity: 'db', schemaName: 'truss', installationId: 'installation'};
void incomplete;
const bootstrap: RecoveryTargetContext = {
  kind: 'bootstrap_attempt', databaseIdentity: 'db', schemaName: 'truss',
  bootstrapAttemptId: 'attempt', candidateInstallationId: 'candidate',
  bundleSha256: 'digest', inventoryProfile: {identity: 'inventory', version: '0.1.0', sha256: 'digest'}
};
void bootstrap;
// @ts-expect-error A bootstrap attempt cannot impersonate an installed context.
const conflated: RecoveryTargetContext = {...bootstrap, sourceEpoch: 'invented'};
void conflated;
const namespace: RecoveryTargetContext = {
  kind: 'namespace_observation', databaseIdentity: 'db', schemaName: 'truss',
  observationAttemptId: 'readiness-attempt',
  observationProfile: {identity: 'readiness', version: '0.1.0', sha256: 'digest'}
};
void namespace;
// @ts-expect-error Namespace observation does not claim installation identity.
const inventedInstallation: RecoveryTargetContext = {...namespace, installationId: 'invented'};
void inventedInstallation;
