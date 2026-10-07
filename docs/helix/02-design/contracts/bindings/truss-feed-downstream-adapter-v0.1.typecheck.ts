/** Public adapter consumer witnesses only; no native fencing evidence. */
import type {HostFeedDownstreamAdapter,CommittedWorkerClaim,DownstreamInstallationResult} from './truss-feed-downstream-adapter-v0.1';
import type {PendingWorkerClaimResult} from './truss-feed-worker-administration-v0.1';
import type {ConsumerAppliedBoundary} from './truss-feed-worker-v0.1';
declare const adapter:HostFeedDownstreamAdapter;
declare const claim:CommittedWorkerClaim;
declare const pending:Extract<PendingWorkerClaimResult,{readonly outcome:'claimed'}>;
declare const applied:ConsumerAppliedBoundary;
void adapter.installGeneration(claim);
void adapter.reconcileInstallation('trusted-original-reference');
// @ts-expect-error Pending source claims cannot authorize downstream installation.
adapter.installGeneration(pending);
// @ts-expect-error Uncertain installation cannot assert a durable applied boundary.
const uncertain:DownstreamInstallationResult={outcome:'commit_unknown',recoveryReference:'fixture',originalAttemptEvidence:{identity:'fixture',bytesBase64:'e30=',sha256:'digest'},downstreamApplied:applied};
// @ts-expect-error Unavailable installation cannot reveal an installed worker.
const refused:DownstreamInstallationResult={outcome:'unavailable',reason:'generation',worker:claim.claim.worker};
// @ts-expect-error Unknown outcome must retain original-attempt evidence.
const lost:DownstreamInstallationResult={outcome:'commit_unknown',recoveryReference:'fixture'};
void [uncertain,refused,lost];
