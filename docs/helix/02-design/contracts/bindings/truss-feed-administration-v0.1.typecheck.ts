import type {FeedPendingAdministrationResult,FeedAdministrationObservation,FeedAdministrationReceipt} from './truss-feed-administration-v0.1';
declare const receipt:Extract<FeedAdministrationReceipt,{readonly result:{readonly outcome:'reseed_registered'}}>;
const pending:FeedPendingAdministrationResult={outcome:'reseed_registered',receipt,durability:'pending'};
// @ts-expect-error A supplied transaction cannot advertise committed durability.
const committed:FeedPendingAdministrationResult={...pending,durability:'committed'};
// @ts-expect-error Unknown commit is execution recovery, not a persisted semantic result.
const uncertain:FeedPendingAdministrationResult={outcome:'commit_unknown',recoveryReference:'fixture'};
// @ts-expect-error Committed receipt observation needs independent original observation evidence.
const observed:FeedAdministrationObservation={outcome:'committed',receipt};
// @ts-expect-error Unavailable receipt observation carries no receipt authority.
const hidden:FeedAdministrationObservation={outcome:'unavailable',reason:'authorization',receipt};
void [pending,committed,uncertain,observed,hidden];

declare const removal:Extract<FeedAdministrationReceipt,{readonly result:{readonly outcome:'removed'}}>;
// @ts-expect-error The pending operation must agree with the original receipt outcome.
const crossed:FeedPendingAdministrationResult={outcome:'reseed_registered',receipt:removal,durability:'pending'};
// @ts-expect-error A stored reseed request cannot pair with a removal result.
const mismatched:FeedAdministrationReceipt={...receipt,result:removal.result};
void [crossed,mismatched];
