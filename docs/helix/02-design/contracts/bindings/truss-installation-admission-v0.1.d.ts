/** Captured admission projection, never live authority by itself. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
export interface InstallationAdmissionSnapshot {
 readonly interfaceVersion:'truss-installation-admission/0.1.0';readonly installationId:string;readonly sourceEpoch:string;
 readonly configurationGeneration:string;readonly keyReuse:'forbid'|'allow';readonly journalMode:'engine'|'trigger';
 readonly configuration:ExactArtifact;readonly selectedBinding:ExactArtifact;readonly installedInventory:ExactArtifact;
 readonly observationProfile:ProfilePin;readonly originalObservation:ExactArtifact;
}
