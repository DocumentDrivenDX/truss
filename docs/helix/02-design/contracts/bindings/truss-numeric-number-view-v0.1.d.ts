/** Proposed standalone pure helper; no implementation or native/Field admission. */
import type {ExactNumericToken,LosslessNumericNumberView} from './truss-numeric-carriers-v0.1';
export type NumericNumberViewResult = {
 readonly status:'lossless';
 readonly view:LosslessNumericNumberView;
} | {
 readonly status:'refused';
 readonly reason:'invalid_token'|'lossy_number'|'nonfinite_number'|'unsupported_profile'|'resource_limited';
};
/** Fixed qualified standalone profile; no caller budget or domain override.
 * Toolkit operations use the same implementation with their enclosing account. */
export declare function viewNumericAsNumber(input:ExactNumericToken):NumericNumberViewResult;
