/** Public abandonment witnesses; native containment/retention remains unqualified. */
import type {SeedAbandonmentTooling,SeedInvalidationRequest,SeedAbandonmentRequest,SeedAbandonmentResult} from './truss-seed-abandonment-v0.1';
import type {SeedActivationState} from './truss-seed-activation-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
declare const tooling:SeedAbandonmentTooling;
declare const transaction:TransactionHandle;
declare const invalidation:SeedInvalidationRequest;
declare const request:SeedAbandonmentRequest;
declare const active:Extract<SeedActivationState,{readonly state:'active'}>;
declare const abandoned:Extract<SeedActivationState,{readonly state:'abandoned'}>;
void tooling.invalidateInTransaction(transaction,invalidation);
void tooling.finishInTransaction(transaction,request);
// @ts-expect-error An active seed cannot enter inactive-attempt invalidation.
tooling.invalidateInTransaction(transaction,{...invalidation,expected:active});
// @ts-expect-error Source finish cannot imply outer transaction committed.
const early:SeedAbandonmentResult={outcome:'abandoned',abandoned,durability:'committed',evidence:request.downstreamContainment};
// @ts-expect-error Missing downstream containment cannot authorize cleanup/protection release.
const uncontained:SeedAbandonmentRequest={interfaceVersion:'truss-seed-abandonment/0.1.0',attempt:request.attempt,procedureProfile:request.procedureProfile,committedInvalidation:request.committedInvalidation};
// @ts-expect-error Unavailable containment cannot expose a completed abandonment descriptor.
const falseFinish:SeedAbandonmentResult={outcome:'unavailable',reason:'containment',abandoned};
void [early,uncontained,falseFinish];
