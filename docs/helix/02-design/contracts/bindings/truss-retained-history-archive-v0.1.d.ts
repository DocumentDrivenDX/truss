/** CONTRACT-002/005/006 candidate complete retained per-record archive. */
import type {ExactArtifact,ProfilePin} from './truss-acceptance-input-v0.1';
import type {HistoricalRecord,HistoricalEvent,TypedIdentity} from './truss-history-v0.1';
export interface RetainedHistoryArchive {
 readonly interfaceVersion:'truss-retained-history-archive/0.1.0';
 readonly sourceEpoch:string;
 readonly archiveProfile:ProfilePin;
 readonly identity:TypedIdentity;
 readonly baseline:HistoricalRecord;
 readonly throughVersion:string;
 readonly events:readonly HistoricalEvent[];
 readonly definitions:readonly {readonly definitionPin:string;readonly interpretationProfile:ProfilePin;readonly artifact:ExactArtifact}[];
 readonly baselineEvidence:ExactArtifact;
 readonly completeEventInventory:ExactArtifact;
 readonly retainedOwnerInventory:ExactArtifact;
 readonly retentionEvidence:ExactArtifact;
}
