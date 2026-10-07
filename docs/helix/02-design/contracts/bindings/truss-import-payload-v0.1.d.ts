/** CONTRACT-004 candidate decoded payload; only eligible creates reach this boundary. */
import type {AuthoredValue, OrderKey} from './truss-group-input-v0.1';
import type {ExactValue} from './truss-history-v0.1';
import type {SingleMutationOperation} from './truss-mutation-capability-v0.1';
type SourceAssertions=Extract<ExactValue,{readonly kind:'map'}>;
type StoredOwnership=Extract<SingleMutationOperation,{readonly operation:'create_object'}>['ownership'];
export type ImportPayload = {
  readonly interfaceVersion:'truss-import-payload/0.1.0';
  readonly kind:'object';
  readonly values:readonly AuthoredValue[];
  readonly source?:SourceAssertions;
  readonly ownership:StoredOwnership;
} | {
  readonly interfaceVersion:'truss-import-payload/0.1.0';
  readonly kind:'edge';
  readonly values:readonly AuthoredValue[];
  readonly source?:SourceAssertions;
  readonly orderKey:OrderKey;
};
