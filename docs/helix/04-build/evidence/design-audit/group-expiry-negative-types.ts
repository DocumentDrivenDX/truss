/** Expiry/refusal boundaries only; no native namespace or replay qualification. */
import type {GroupApplicationResult} from '../../../02-design/contracts/bindings/truss-group-capability-v0.1';
import type {GroupSemanticInput} from '../../../02-design/contracts/bindings/truss-group-input-v0.1';
import type {GroupResponse} from '../../../02-design/contracts/bindings/truss-group-result-v0.1';
declare const input:GroupSemanticInput;
declare const response:GroupResponse;
const expired:GroupApplicationResult={outcome:'unavailable',reason:'receipt_expired'};
// @ts-expect-error Expiry cannot expose a successful replay response.
const leaked:GroupApplicationResult={outcome:'unavailable',reason:'receipt_expired',response};
// @ts-expect-error Story-defined invalid empty input cannot be promoted to a valid group.
const empty:GroupSemanticInput={...input,operations:[]};
