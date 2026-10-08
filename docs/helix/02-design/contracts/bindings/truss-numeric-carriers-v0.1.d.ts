/** ADR-006 draft pure-core carriers; no runtime admission, native support or constructor claim. */
/** Structural subset of pinned UMF CoreLiteral numeric wrappers; semantics remain UMF-owned. */
export type ExactIntegerToken = {readonly integerToken:string;readonly decimalToken?:never};
export type ExactDecimalToken = {readonly decimalToken:string;readonly integerToken?:never};
export type ExactNumericToken = ExactIntegerToken | ExactDecimalToken;
/** The original declared field chooses meaning; neither spelling nor JS input type chooses a domain. */
export type NumericInput = number | bigint | ExactNumericToken;
/** Default admitted read carrier retains exact source spelling; no automatic number conversion. */
export type NumericReadValue = ExactNumericToken;
/** Created only after exact binary-rational equality/domain checks; type shape alone is not proof. */
export interface LosslessNumericNumberView {
 readonly original:ExactNumericToken;
 readonly value:number;
}
/** Number-origin provenance cannot invent authored spelling; exact tokens remain the value carrier. */
export type NumericInputOrigin = 'number' | 'bigint' | 'exact_token';
