import type {ApplicationProofSubmission, VerifiedApplication, ConsumerWorkerIdentity, WorkerInstallation} from './truss-feed-worker-v0.1';
declare const submission: ApplicationProofSubmission;
// @ts-expect-error Deserialized proof content is not host verification authority.
const verified: VerifiedApplication = submission;
const worker: ConsumerWorkerIdentity = {context: {sourceEpoch: 'fixture', feedProfile: 'draft', scopeIdentity: 'fixture'}, consumerId: 'worker', registrationId: 'registration', generation: '9007199254740993'};
// @ts-expect-error Generation cannot be a rounded host number.
const rounded: ConsumerWorkerIdentity = {...worker, generation: 9007199254740993};
// @ts-expect-error A reused consumer name cannot omit its registration identity.
const nameOnly: ConsumerWorkerIdentity = {context: worker.context, consumerId: 'worker', generation: '1'};
// @ts-expect-error Unavailable installation cannot reveal successful downstream state.
const mixed: WorkerInstallation = {outcome: 'unavailable', reason: 'authorization', downstreamApplied: {state: 'seed'}};
void [verified, worker, rounded, nameOnly, mixed];
