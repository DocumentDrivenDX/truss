/** Pending/committed/protection correspondence types only; no native qualifier. */
import type {ReceiptProtectionUpdateRequest,ReceiptProtectionUpdateResult,ReceiptProtectionObservation} from '../../../02-design/contracts/bindings/truss-receipt-protection-tooling-v0.1';
import type {ReceiptProtection} from '../../../02-design/contracts/bindings/truss-request-receipt-v0.1';
declare const request:ReceiptProtectionUpdateRequest;
declare const protection:ReceiptProtection;
declare const success:Extract<ReceiptProtectionUpdateResult,{readonly outcome:'updated'|'equal'}>;
// @ts-expect-error Expected present state must preserve its exact original artifact.
const missingExpected:ReceiptProtectionUpdateRequest={...request,expected:{state:'present'}};
// @ts-expect-error New deadline request is explicit rather than an unqualified current clock field.
const missingDeadline:ReceiptProtectionUpdateRequest={...request,extension:{state:'requested'}};
// @ts-expect-error Supplied scope never commits its own protection update.
const falseCommit:ReceiptProtectionUpdateResult={...success,durability:'committed'};
// @ts-expect-error Conflict must not disclose a success protection payload.
const conflict:ReceiptProtectionUpdateResult={outcome:'conflict',protection};
// @ts-expect-error Pending update cannot substitute for native committed observation.
const observed:ReceiptProtectionObservation=success;
// @ts-expect-error Unavailable observation cannot leak protected original payload.
const leaked:ReceiptProtectionObservation={outcome:'unavailable',reason:'authority',protection};
