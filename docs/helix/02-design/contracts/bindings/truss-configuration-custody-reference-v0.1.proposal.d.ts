/** Private historical lookup locator. Shape and digest confer no authority. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
export interface ConfigurationCustodyReference {
 readonly interfaceVersion:'truss-configuration-custody-reference/0.1.0';
 readonly installationId:string;readonly sourceEpoch:string;readonly targetIncarnation:string;
 readonly writerXid:string;readonly operationOrdinal:string;
 readonly configurationGeneration:string;
 /** Original selected capsule interpretation/retention composition. */
 readonly custodyProfile:ProfilePin;
 /** Exact retained artifact locator; resolution must compare full original bytes. */
 readonly capsule:{readonly identity:string;readonly sha256:string;readonly byteLength:string};
}
export type ConfigurationCustodyResolution = {
 readonly outcome:'available';
 /** Original private raw capsule and complete original settlement/retention evidence. */
 readonly capsule:import('./truss-acceptance-input-v0.1').ExactArtifact;
 readonly correspondence:import('./truss-acceptance-input-v0.1').ExactArtifact;
} | {
 readonly outcome:'unavailable';
 readonly reason:'authorization'|'custody'|'profile'|'integrity'|'resource'|'retention';
 readonly capsule?:never;readonly correspondence?:never;
};
