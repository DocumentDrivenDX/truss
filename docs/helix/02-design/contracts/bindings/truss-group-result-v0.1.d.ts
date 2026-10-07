/** Proposed complete semantic results; receipt storage/authority remains gated. */
import type {TypedIdentity} from './truss-history-v0.1';
import type {ProfilePin, ExactArtifact} from './truss-acceptance-input-v0.1';
export interface JournalEventReference {
  readonly sourceEpoch: string;
  readonly historyProfile: string;
  readonly xid: string;
  readonly seq: string;
}
export type OperationResult = {
  readonly operation: 'create_object' | 'create_edge';
  readonly outcome: 'created';
  readonly identity: TypedIdentity;
  readonly version: string;
  readonly alias?: string;
  readonly events: readonly [JournalEventReference, ...JournalEventReference[]];
} | {
  readonly operation: 'update_object' | 'update_edge';
  readonly outcome: 'changed';
  readonly identity: TypedIdentity;
  readonly version: string;
  readonly events: readonly [JournalEventReference, ...JournalEventReference[]];
} | {
  readonly operation: 'update_object' | 'update_edge';
  readonly outcome: 'unchanged';
  readonly identity: TypedIdentity;
  readonly version: string;
  readonly events: readonly [];
} | {
  readonly operation: 'delete_object' | 'delete_edge';
  readonly outcome: 'deleted';
  readonly identity: TypedIdentity;
  readonly deletionVersion: string;
  /** Includes every owned descendant/edge effect required by the protocol. */
  readonly deleted: readonly {readonly identity: TypedIdentity; readonly deletionVersion: string}[];
  readonly events: readonly [JournalEventReference, ...JournalEventReference[]];
};
export interface GroupSemanticResult {
  readonly interfaceVersion: 'truss-group-result/0.1.0';
  readonly executedCatalogRevision: string;
  readonly layoutProfile: ProfilePin;
  readonly mutationProfile: ProfilePin;
  /** Exactly one result per original operation, including unchanged entries. */
  readonly results: readonly [OperationResult, ...OperationResult[]];
  readonly aliases: readonly {readonly alias: string; readonly identity: TypedIdentity}[];
}
export type GroupResponse = {
  readonly semantic: GroupSemanticResult;
} & ({
  readonly disposition:'applied';
  readonly durability:'pending' | 'committed';
  readonly replay?:never;
} | {
  readonly disposition:'replayed';
  readonly durability:'pending';
  readonly replay:{readonly basis:'same_transaction'; readonly observationProfile:ProfilePin; readonly evidence:ExactArtifact};
} | {
  readonly disposition:'replayed';
  readonly durability:'committed';
  readonly replay:{readonly basis:'committed_receipt'; readonly observationProfile:ProfilePin; readonly evidence:ExactArtifact};
});
