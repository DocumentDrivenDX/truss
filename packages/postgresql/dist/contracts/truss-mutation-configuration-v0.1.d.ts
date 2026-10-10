/** CONTRACT-009 draft provenance; selection does not prove actual native admission. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
export interface SelectedMutationConfiguration {
  readonly sourceEpoch: string;
  readonly installationId: string;
  readonly generation: string;
  readonly keyReuse: 'forbid' | 'allow';
  readonly journalMode: 'engine' | 'trigger';
  readonly configurationProfile: ProfilePin;
  readonly installedProducerInventorySha256: string;
}
