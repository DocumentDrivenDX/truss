import {test, expect} from 'bun:test';
import {createReferenceAssembly, INERT_ASSEMBLY_PROFILE} from '../packages/postgresql/src/index';
import type {ReferenceAssemblyConfiguration, Executor, HostRecoveryRegistry, CapabilitySelection} from '../packages/postgresql/src/index';
const profile = {identity: 'fixture-unqualified', version: '0.12', sha256: 'a'.repeat(64)};
const capability: CapabilitySelection = {family: 'direct_read', capabilityProfile: profile, layoutProfile: profile,
  adapterProfile: profile, valueProfile: profile, policyProfile: profile};
function input(): ReferenceAssemblyConfiguration {return {interfaceVersion: 'truss-reference-assembly/0.1.0',
  assemblyId: 'host-correlation-only', assemblyProfile: INERT_ASSEMBLY_PROFILE,
  recovery: {registryProfile: profile, retention: 'restart_durable'}, databaseIdentity: 'fixture-uninstalled',
  schema: 'truss', capabilities: [capability]};}
function ports() {
  let calls = 0;
  const fail = async (): Promise<never> => {calls++; throw Error('Unexpected I/O');};
  const executor: Executor<unknown> = {withTransaction: fail, adoptTransaction: fail, execute: fail,
    savepoint: fail, rollbackToSavepoint: fail, releaseSavepoint: fail};
  const registry: HostRecoveryRegistry = {profile, retention: 'restart_durable', register: fail, append: fail, inspect: fail};
  return {executor, services: {recoveryRegistry: registry}, calls: () => calls};
}
test('construction and selection preserve unverified status without touching injected native ports', async () => {
  const host = ports();const result = createReferenceAssembly(input(), host.executor, host.services);
  expect(result.status).toBe('ok');if (result.status !== 'ok') throw Error('Construction refused');
  const assembly = result.value;
  expect(assembly.directReads(capability)).toEqual({status: 'unavailable', reason: 'selection'});
  expect(await assembly.observeReadiness(capability)).toEqual({status: 'ok', value: {
    interfaceVersion: 'truss-capability-readiness/0.1.0', selection: capability, state: 'unverified'}});
  expect(host.calls()).toBe(0);
  expect(await assembly.dispose({})).toEqual({state: 'disposed', ownedResourcesReleased: true});
  expect(await assembly.dispose({})).toEqual({state: 'disposed', ownedResourcesReleased: true});
  expect(assembly.directReads(capability)).toEqual({status: 'unavailable', reason: 'disposed'});
  expect((await assembly.observeReadiness(capability)).status).toBe('error');expect(host.calls()).toBe(0);
});
test('invalid configuration and accessor metadata refuse before host calls or getter execution', () => {
  const host = ports();let getters = 0;
  const config = input();Object.defineProperty(config, 'schema', {get() {getters++; return 'truss';}});
  expect(createReferenceAssembly(config, host.executor, host.services).status).toBe('error');
  const config2 = input();Object.defineProperty(config2.capabilities, '0', {get() {getters++; return capability;}});
  expect(createReferenceAssembly(config2, host.executor, host.services).status).toBe('error');
  expect(getters).toBe(0);expect(host.calls()).toBe(0);
});
test('source mutation cannot alter held configuration; incompatible recovery and unsupported assembly profiles refuse', async () => {
  const host = ports();const config = structuredClone(input());const result = createReferenceAssembly(config, host.executor, host.services);
  if (result.status !== 'ok') throw Error('Construction refused');
  (config.capabilities[0].layoutProfile as {sha256: string}).sha256 = 'b'.repeat(64);
  expect(result.value.configuration.capabilities[0].layoutProfile.sha256).toBe('a'.repeat(64));
  expect((await result.value.observeReadiness(config.capabilities[0])).status).toBe('error');
  expect(createReferenceAssembly({...input(), assemblyProfile: profile}, host.executor, host.services)).toMatchObject({status: 'error', code: 'unsupported_profile'});
  expect(createReferenceAssembly({...input(), recovery: {registryProfile: {...profile, sha256: 'b'.repeat(64)}, retention: 'restart_durable'}}, host.executor, host.services)).toMatchObject({status: 'error', code: 'incompatible_selection'});
  expect(host.calls()).toBe(0);
});
