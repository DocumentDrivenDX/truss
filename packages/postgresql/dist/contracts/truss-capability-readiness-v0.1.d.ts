/** CONTRACT-007/011 candidate; readiness is an observation, never an authority token. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
export type CapabilityFamily = 'catalog' | 'mutation' | 'group' | 'import' |
  'direct_read' | 'history' | 'feed' | 'weft_execution' | 'bootstrap' |
  'physical_optimization' | 'conformance';
export interface CapabilitySelection {
  readonly family: CapabilityFamily;
  readonly capabilityProfile: ProfilePin;
  readonly layoutProfile: ProfilePin;
  readonly adapterProfile: ProfilePin;
  readonly valueProfile: ProfilePin;
  readonly policyProfile: ProfilePin;
}
export type CapabilityReadiness = {
  readonly interfaceVersion: 'truss-capability-readiness/0.1.0';
  readonly selection: CapabilitySelection;
} & ({
  readonly state: 'unverified';
} | {
  readonly state: 'available';
  readonly target: {readonly state: 'installed'; readonly installationId: string} |
    {readonly state: 'fresh_namespace'; readonly namespaceObservationSha256: string};
  readonly databaseIdentity: string;
  readonly schema: string;
  readonly observedAt: string;
  readonly observationProcedure: ProfilePin;
  readonly contextEvidenceSha256: string;
  readonly targetInventorySha256: string;
  readonly qualificationReceiptSha256: string;
} | {
  readonly state: 'unavailable';
  readonly reason: 'not_installed' | 'profile' | 'drift' | 'observation' | 'disposed';
  readonly observedAt: string;
});
