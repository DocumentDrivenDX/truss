/** R7 facade; the Python authority and registered-feed realizations is documented in the receipt design.
 * Syntax/types never grant receipt, read or publication authority. */
import type {Outcome,TransactionHandle} from './truss-execution-v0.1';
import type {ProfilePin} from './truss-acceptance-input-v0.1';
export interface ReceiptVisibilityRequest {
 readonly interfaceVersion:'truss-receipt-visibility-request/0.1.0';
 /** Opaque canonical locator. Consumers never compare or construct its fields. */
 readonly token:string;
 /** Optional registered caller-asserted feed; absence selects authority visibility. */
 readonly consumerId?:string;
 /** Canonical positive exact text; reductions of the selected profile ceilings. */
 readonly limits:Readonly<{
  tokenBytes:string; evidenceBytes:string;
 }>;
}
export type ReceiptVisibilityResult = Readonly<{
 interfaceVersion:'truss-receipt-visibility-result/0.1.0';
 outcome:'available';included:boolean;comparisonProfile:ProfilePin;
}> | Readonly<{
 interfaceVersion:'truss-receipt-visibility-result/0.1.0';
 outcome:'unavailable';
 reason:'authorization'|'epoch_profile'|'retention'|'observation_integrity'|'resource'|'invalid_token'|'invalid_consumer';
 included?:never;
}>;
/** Constructed only by original admitted read services. No public numeric xid API.
 * One supplied read-only transaction/snapshot; no wait, new connection or retry.
 * Outer Outcome preserves original execution/containment failures separately. */
export interface ReceiptVisibilityCapability {
 /** Default authority-mode pin; each available result reports its actual comparison pin. */
 readonly comparisonProfile:ProfilePin;
 reachedInTransaction(transaction:TransactionHandle,request:ReceiptVisibilityRequest):Promise<Outcome<ReceiptVisibilityResult>>;
}
