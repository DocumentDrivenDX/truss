import type {ExpiryEvidence} from '../../../02-design/contracts/bindings/truss-expiry-evidence-v0.1';
import type {ReceiptPayloadPurgeRequest,ReceiptPayloadPurgeResult,ReceiptExpiryObservation} from '../../../02-design/contracts/bindings/truss-receipt-expiry-tooling-v0.1';
declare const proof:ExpiryEvidence;
declare const request:ReceiptPayloadPurgeRequest;
declare const result:Extract<ReceiptPayloadPurgeResult,{outcome:'purged'}>;
// @ts-expect-error Minimal expiry metadata cannot preserve a full result.
const payload:ExpiryEvidence={...proof,result:{}};
// @ts-expect-error Expiry basis cannot declare original commit.
const committedProof:ExpiryEvidence={...proof,committed:true};
const {expectedProtection,...missingProtection}=request;
// @ts-expect-error Protected purge needs exact expected protection, not a prior eligible flag.
const incomplete:ReceiptPayloadPurgeRequest=missingProtection;
// @ts-expect-error Supplied-scope purge never reports committed.
const committed:ReceiptPayloadPurgeResult={...result,durability:'committed'};
// @ts-expect-error A pending purge is not an original committed observation.
const observation:ReceiptExpiryObservation=result;
// @ts-expect-error Unavailable observation cannot expose compact identity.
const leak:ReceiptExpiryObservation={outcome:'unavailable',reason:'authority',identity:result.identity};
