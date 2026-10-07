/** Compile-only controls: runtime profile/custody admission remains mandatory. */
import type {FeedConsumerState} from '../../../02-design/contracts/bindings/truss-feed-registration-v0.1';
import type {FeedConsumerStateV02,FeedAdministrationReceiptV02,FeedLifecycleToolingV02,SeedExtractionRequestV02} from '../../../02-design/contracts/bindings/truss-feed-lifecycle-v0.2';
import type {ConsumerAppliedBoundaryV02} from '../../../02-design/contracts/bindings/truss-feed-key-transition-v0.2';
import type {FeedLifecycleTooling} from '../../../02-design/contracts/bindings/truss-feed-tooling-v0.1';
import type {FeedAdministrationReceipt} from '../../../02-design/contracts/bindings/truss-feed-administration-v0.1';
import type {SeedExtractionRequest} from '../../../02-design/contracts/bindings/truss-seed-extraction-v0.1';
declare const active:Extract<FeedConsumerState,{readonly state:'active'}>;
declare const waiting:Extract<FeedConsumerStateV02,{readonly state:'awaiting_seed'}>;
declare const applied:ConsumerAppliedBoundaryV02;
declare const receipt:FeedAdministrationReceipt;
declare const lifecycle:FeedLifecycleTooling;
declare const extraction:SeedExtractionRequest;
// @ts-expect-error Old active progress cannot silently become migration-capable progress.
const oldActive:FeedConsumerStateV02=active;
// @ts-expect-error Awaiting seed cannot fabricate an applied boundary.
const fakeApplied:FeedConsumerStateV02={...waiting,applied};
// @ts-expect-error Old receipt preserves the wrong progress and protocol version.
const oldReceipt:FeedAdministrationReceiptV02=receipt;
// @ts-expect-error Old source worker/admin facades are not a v0.2 lifecycle.
const oldLifecycle:FeedLifecycleToolingV02=lifecycle;
// @ts-expect-error Initial extraction must explicitly select the new protocol.
const oldExtraction:SeedExtractionRequestV02=extraction;

import type {FeedPendingAdministrationResultV02,SeedRestartObservationV02,SeedRestartResultV02} from '../../../02-design/contracts/bindings/truss-feed-lifecycle-v0.2';
declare const reseed:Extract<FeedAdministrationReceiptV02,{readonly result:{readonly outcome:'reseed_registered'}}>;
declare const removed:Extract<FeedAdministrationReceiptV02,{readonly result:{readonly outcome:'removed'}}>;
declare const current:FeedConsumerStateV02;
// Positive witnesses prove receipt variants did not accidentally narrow to never.
const validReseed:FeedPendingAdministrationResultV02={outcome:'reseed_registered',receipt:reseed,durability:'pending'};
const validRemoval:FeedPendingAdministrationResultV02={outcome:'removed',receipt:removed,durability:'pending'};
// @ts-expect-error Successful outcome and original receipt operation must agree.
const swappedReceipt:FeedPendingAdministrationResultV02={outcome:'removed',receipt:reseed,durability:'pending'};
// @ts-expect-error Request/result correlation cannot swap removal and reseed.
const crossedReceipt:FeedAdministrationReceiptV02={...reseed,result:removed.result};
// @ts-expect-error Failed native observation cannot leak original consumer state.
const failedObservation:SeedRestartObservationV02={outcome:'unavailable',reason:'authorization',preservedConsumer:current};
// @ts-expect-error Conflict cannot report preserved success state.
const conflictingRestart:SeedRestartResultV02={outcome:'conflict',preservedConsumer:current};
