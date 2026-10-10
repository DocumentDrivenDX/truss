import type {FeedCommittedApplicationEvidence} from './truss-feed-application-evidence-v0.1';
declare const evidence:FeedCommittedApplicationEvidence;
const preserved:FeedCommittedApplicationEvidence={...evidence};
// @ts-expect-error A boolean cannot replace original native commit evidence.
const flag:FeedCommittedApplicationEvidence={...evidence,commitObservation:true};
// @ts-expect-error Coverage must retain the exact complete coverage artifact.
const missing:FeedCommittedApplicationEvidence={...evidence,operation:{kind:'coverage'}};
// @ts-expect-error Current mutable progress is not an archived original prior.
const current:FeedCommittedApplicationEvidence={...evidence,prior:{state:'current'}};
void [preserved,flag,missing,current];
