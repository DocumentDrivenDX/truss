/** Proposed CONTRACT-004/009 input; full runtime/domain validation remains gated. */
import type {ExactValue, TypedIdentity} from './truss-history-v0.1';
import type {ProfilePin} from './truss-acceptance-input-v0.1';
export type ObjectReference = {
  readonly state: 'stored'; readonly identity: TypedIdentity;
} | {readonly state: 'alias'; readonly alias: string};
export interface AuthoredValue {
  readonly name: string;
  readonly value: ExactValue;
}
export type OwnershipSelection = {readonly state: 'rootless'} |
  {readonly state: 'owned'; readonly root: ObjectReference};
export type OrderKey = {readonly state: 'null'} | {readonly state: 'text'; readonly text: string};
export type GroupOperation = {
  readonly operation: 'create_object';
  readonly typeDefinitionPin: string;
  readonly alias?: string;
  readonly values: readonly AuthoredValue[];
  readonly ownership: OwnershipSelection;
} | {
  readonly operation: 'create_edge';
  readonly relationshipDefinitionPin: string;
  readonly alias?: string;
  readonly source: ObjectReference;
  readonly target: ObjectReference;
  readonly values: readonly AuthoredValue[];
  readonly orderKey: OrderKey;
} | {
  readonly operation: 'update_object';
  readonly target: {readonly state: 'stored'; readonly identity: TypedIdentity} | {readonly state: 'alias'; readonly alias: string};
  readonly expectedVersion?: string;
  readonly set: readonly AuthoredValue[];
  readonly unset: readonly string[];
  readonly ownershipChange?: OwnershipSelection;
} | {
  readonly operation: 'update_edge';
  readonly target: {readonly state: 'stored'; readonly identity: TypedIdentity} | {readonly state: 'alias'; readonly alias: string};
  readonly expectedVersion?: string;
  readonly set: readonly AuthoredValue[];
  readonly unset: readonly string[];
  readonly endpointChange?: {readonly source: ObjectReference; readonly target: ObjectReference};
  readonly orderKeyChange?: OrderKey;
} | {
  readonly operation: 'delete_object' | 'delete_edge';
  readonly target: {readonly state: 'stored'; readonly identity: TypedIdentity} | {readonly state: 'alias'; readonly alias: string};
  readonly expectedVersion?: string;
};
export interface GroupSemanticInput {
  readonly interfaceVersion: 'truss-group-input/0.1.0';
  readonly layoutProfile: ProfilePin;
  readonly mutationProfile: ProfilePin;
  readonly valueProfile: ProfilePin;
  /** Current-head observation is execution context, not a rewritten retry input. */
  readonly catalog: {readonly selection: 'current'} |
    {readonly selection: 'pinned'; readonly revision: string; readonly modelBundleSha256: string};
  readonly operations: readonly [GroupOperation, ...GroupOperation[]];
  readonly assertedOrigin: ExactValue;
}
export interface RequestIdentity {
  readonly interfaceVersion: 'truss-request-identity/0.1.0';
  readonly authorizedScopeIdentity: string;
  readonly requestId: string;
  readonly inputProfile: 'truss-group-input/0.1.0';
  /** Claimed hash is runtime verified from input; never equality authority. */
  readonly claimedSha256?: string;
}
