/** CONTRACT-002/005/007 journal-only incremental paging; not complete feed. */
import type {ProfilePin,ExactArtifact} from './truss-acceptance-input-v0.1';
import type {JournalPosition} from './truss-feed-observation-v0.1';
import type {HistoricalEvent} from './truss-history-v0.1';
export interface JournalPageContext {
 readonly sourceEpoch:string;
 readonly scopeIdentity:string;
 readonly journalProfile:ProfilePin;
 readonly observationProfile:ProfilePin;
 readonly snapshot:{readonly state:'statement'}|{readonly state:'held';readonly snapshotIdentity:string};
}
export interface JournalPageCursor {
 readonly interfaceVersion:'truss-journal-cursor/0.1.0';
 readonly context:JournalPageContext;
 readonly after:JournalPosition;
}
export interface JournalPageRequest {
 readonly interfaceVersion:'truss-journal-page/0.1.0';
 readonly context:JournalPageContext;
 readonly continuation:{readonly state:'first'}|{readonly state:'after';readonly cursor:JournalPageCursor};
 readonly limits:{readonly rows:string;readonly encodedBytes:string};
}
export type JournalPageResult = {
 readonly outcome:'page';readonly context:JournalPageContext;
 readonly events:readonly HistoricalEvent[];
 readonly safeWatermarkXid:string;
 readonly continuation:{readonly state:'end'}|{readonly state:'more';readonly cursor:JournalPageCursor};
 readonly observation:ExactArtifact;
} | {
 readonly outcome:'unavailable';readonly reason:'authorization'|'context'|'profile'|'retention'|'integrity'|'resource'|'observation';
 readonly events?:never;readonly continuation?:never;
};
