/** Independent tooling consumer witnesses; native claim observation remains open. */
import type {FeedWorkerAdministration,WorkerClaimRequest,PendingWorkerClaimResult,WorkerClaimObservation} from './truss-feed-worker-administration-v0.1';
import type {WorkerClaim} from './truss-feed-worker-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
declare const tooling:FeedWorkerAdministration;
declare const transaction:TransactionHandle;
declare const request:WorkerClaimRequest;
declare const claim:WorkerClaim;
void tooling.acquireInTransaction(transaction,request);
void tooling.observeClaim(transaction,claim);
// @ts-expect-error Acquisition cannot claim the outer source transaction committed.
const early:PendingWorkerClaimResult={outcome:'claimed',claim,durability:'committed',claimEvidence:{identity:'fixture',bytesBase64:'e30=',sha256:'digest'}};
// @ts-expect-error Committed claim requires independent observation evidence.
const unseen:WorkerClaimObservation={outcome:'current_committed',claim};
// @ts-expect-error Unavailable/superseded observation cannot return installation authority.
const stale:WorkerClaimObservation={outcome:'unavailable',reason:'superseded',claim};
// @ts-expect-error Claim cannot omit its original procedure pin.
const unpinned:WorkerClaim={interfaceVersion:'truss-feed-worker/0.1.0',worker:claim.worker,sourceApplied:claim.sourceApplied,downstreamProfile:claim.downstreamProfile};
void [early,unseen,stale,unpinned];
