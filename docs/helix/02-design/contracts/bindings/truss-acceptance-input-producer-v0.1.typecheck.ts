import type {AcceptanceInput} from './truss-acceptance-input-v0.1';
declare const validInput:AcceptanceInput;
import type {OriginalAcceptanceInputSource,OriginalAcceptanceInputCustody,OriginalAcceptanceInputAccount,AdmittedOriginalAcceptanceInput,AcceptanceInputProducerResult} from './truss-acceptance-input-producer-v0.1';
const pin={identity:'fixture',version:'draft',sha256:'0'.repeat(64)};
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'0'.repeat(64)};
const raw:OriginalAcceptanceInputSource={representation:'raw-json-transport',artifact,decoderProfile:pin};
const tree:OriginalAcceptanceInputSource={representation:'canonical-tree-utf8',artifact,canonicalProfile:'truss-canonical/0.1.0'};
const frame:OriginalAcceptanceInputSource={representation:'framed-fingerprint-preimage',artifact,canonicalProfile:'truss-canonical/0.1.0',domain:'truss-acceptance-input/0.1.0'};
// @ts-expect-error A framed group domain cannot supply original catalog acceptance input.
const foreign:OriginalAcceptanceInputSource={...frame,domain:'truss-group-input/0.1.0'};
// @ts-expect-error Raw input requires an explicit original decoder profile.
const missingDecoder:OriginalAcceptanceInputSource={representation:'raw-json-transport',artifact};
// @ts-expect-error A claimed identity does not issue original custody.
const custody:OriginalAcceptanceInputCustody={identity:'caller'};
// @ts-expect-error Caller remaining counters are not an original issued resource account.
const account:OriginalAcceptanceInputAccount={remainingBytes:'4194304'};
// @ts-expect-error A parsed input/source pair cannot fabricate issuer-bound admission.
const admitted:AdmittedOriginalAcceptanceInput={source:tree,input:validInput,canonicalTree:artifact,framedPreimage:artifact,canonicalProfile:'truss-canonical/0.1.0',domain:'truss-acceptance-input/0.1.0',installedInputProfile:pin};
// @ts-expect-error Refusal cannot carry a partial admitted original input.
const partial:AcceptanceInputProducerResult={status:'refused',reason:'resource',original:admitted};
// @ts-expect-error Interpretation admission is not public committed acceptance.
const committed:AcceptanceInputProducerResult={status:'admitted',original:admitted,durability:'committed'};
void [raw,tree,frame,foreign,missingDecoder,custody,account,admitted,partial,committed];
