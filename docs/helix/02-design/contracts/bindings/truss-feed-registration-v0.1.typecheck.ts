/** Public tooling witnesses; native protection/commit observation remains open. */
import type {FeedConsumerRegistration,FeedRegistrationRequest,FeedConsumerState,FeedRegistrationResult,FeedRegistrationObservation} from './truss-feed-registration-v0.1';
import type {ConsumerAppliedBoundary} from './truss-feed-worker-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
declare const tooling:FeedConsumerRegistration;
declare const request:FeedRegistrationRequest;
declare const transaction:TransactionHandle;
declare const awaiting:Extract<FeedConsumerState,{readonly state:'awaiting_seed'}>;
declare const active:Extract<FeedConsumerState,{readonly state:'active'}>;
declare const applied:ConsumerAppliedBoundary;
void tooling.registerInTransaction(transaction,request);
void tooling.observeRegistration(transaction,awaiting);
// @ts-expect-error An awaiting registration cannot assert applied progress.
const falseProgress:FeedConsumerState={...awaiting,applied};
// @ts-expect-error Supplied transaction registration remains pending.
const early:FeedRegistrationResult={outcome:'registered',consumer:awaiting,durability:'committed'};
// @ts-expect-error Active registrations are not authority to start initial extraction.
tooling.observeRegistration(transaction,active);
// @ts-expect-error Hidden/superseded registrations cannot reveal seed authority.
const hidden:FeedRegistrationObservation={outcome:'unavailable',reason:'superseded',consumer:awaiting};
void [falseProgress,early,hidden];
