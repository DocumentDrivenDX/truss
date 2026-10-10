/** Restart consumer witnesses; committed native admission remains profile-qualified. */
import type {SeedRestartTooling,SeedRestartRequest,SeedRestartResult,SeedRestartObservation} from './truss-seed-restart-v0.1';
import type {SeedExtractionTooling,RestartedSeedExtractionRequest} from './truss-seed-extraction-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
declare const tooling:SeedRestartTooling;
declare const extraction:SeedExtractionTooling;
declare const transaction:TransactionHandle;
declare const request:SeedRestartRequest;
declare const pending:Extract<SeedRestartResult,{readonly outcome:'registered'}>;
declare const extractionRequest:RestartedSeedExtractionRequest;
void tooling.restartInTransaction(transaction,request);
void tooling.observeRestart(transaction,pending);
void extraction.extractRestarted(extractionRequest);
// @ts-expect-error Pending successor is not a committed observation.
extraction.extractRestarted({...extractionRequest,restart:pending});
// @ts-expect-error Superseded observation cannot return extraction identity.
const stale:SeedRestartObservation={outcome:'unavailable',reason:'superseded',attempt:pending.attempt};
// @ts-expect-error Source restart registration cannot claim enclosing commit.
const early:SeedRestartResult={...pending,durability:'committed'};
// @ts-expect-error Committed observation requires exact original admission, not only current labels.
const abbreviated:SeedRestartObservation={outcome:'current_committed',attempt:pending.attempt,preservedConsumer:pending.preservedConsumer,observation:pending.admissionEvidence};
void [stale,early,abbreviated];
