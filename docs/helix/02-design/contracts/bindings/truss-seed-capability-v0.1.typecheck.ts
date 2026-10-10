/** Public seed adapter/tooling witnesses, not native activation proof. */
import type {HostSeedDownstreamAdapter,SeedActivationRequest,SeedDownstreamActivationResult} from './truss-seed-downstream-adapter-v0.1';
import type {SeedSourceConfirmation,SeedConfirmationRequest,SeedConfirmationResult} from './truss-seed-confirmation-v0.1';
import type {SeedActivationState} from './truss-seed-activation-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
declare const adapter:HostSeedDownstreamAdapter;
declare const tooling:SeedSourceConfirmation;
declare const request:SeedActivationRequest;
declare const confirmation:SeedConfirmationRequest;
declare const transaction:TransactionHandle;
declare const protectedSeed:Extract<SeedActivationState,{readonly state:'protected'}>;
declare const active:Extract<SeedActivationState,{readonly state:'active'}>;
void adapter.activate(request);
void adapter.reconcileActivation('trusted-original-reference');
void tooling.confirmInTransaction(transaction,confirmation);
// @ts-expect-error Protected seed has no completed staged baseline to activate.
adapter.activate({...request,staged:protectedSeed});
// @ts-expect-error Unknown downstream commit cannot carry an active seed.
const uncertain:SeedDownstreamActivationResult={outcome:'commit_unknown',recoveryReference:'fixture',originalAttemptEvidence:{identity:'fixture',bytesBase64:'e30=',sha256:'digest'},active};
// @ts-expect-error Source confirmation cannot claim enclosing commit before it occurs.
const early:SeedConfirmationResult={outcome:'confirmed',active:{...active,sourceConfirmation:{state:'confirmed',evidenceSha256:'digest'}},durability:'committed',confirmationEvidence:{identity:'fixture',bytesBase64:'e30=',sha256:'digest'}};
// @ts-expect-error Source admission requires confirmed downstream activation, not unavailable outcome.
const unactivated:SeedConfirmationRequest={...confirmation,activation:{outcome:'unavailable',reason:'stage'}};
void [uncertain,early,unactivated];
