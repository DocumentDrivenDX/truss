/** Proposed ADR-004/007 binding; not installed layout or event qualification. */
export type ExactValue =
  {readonly kind: 'null'} |
  {readonly kind: 'boolean'; readonly value: boolean} |
  {readonly kind: 'string' | 'integer' | 'decimal' | 'binary' | 'timestamp'; readonly text: string} |
  {readonly kind: 'sequence'; readonly items: readonly ExactValue[]} |
  {readonly kind: 'map'; readonly entries: readonly {readonly key: string; readonly value: ExactValue}[]} |
  {readonly kind: 'record'; readonly definitionPin: string; readonly fields: readonly {readonly fieldId: string; readonly value: ExactValue}[]} |
  {readonly kind: 'opaque'; readonly format: string; readonly sourceText: string; readonly sha256: string};
export type Presence = {readonly present: false; readonly value?: never} |
  {readonly present: true; readonly value: ExactValue};
export interface QualifiedOwner {
  readonly documentId: string;
  readonly moduleId: string;
}
export interface TypedIdentity {
  readonly id: string;
  readonly typeId: string;
  readonly definitionPin: string;
  readonly owner: QualifiedOwner;
}
export interface CommonRecord {
  readonly interfaceVersion: 'truss-history-record/0.1.0';
  readonly identity: TypedIdentity;
  readonly recordVersion: string;
  readonly catalogRevision: string;
  readonly createdAt: string;
  readonly updatedAt: string;
  readonly properties: readonly {readonly propertyId: string; readonly definitionPin: string; readonly value: ExactValue}[];
  readonly retained: readonly {readonly name: string; readonly value: ExactValue}[];
}
export type HistoricalRecord = CommonRecord & ({
  readonly kind: 'object';
  readonly ownership: {readonly state: 'rootless'} | {readonly state: 'owned'; readonly root: TypedIdentity};
  readonly source?: never;
  readonly target?: never;
  readonly orderKey?: never;
} | {
  readonly kind: 'edge';
  readonly source: TypedIdentity;
  readonly target: TypedIdentity;
  readonly orderKey: {readonly state: 'null'} | {readonly state: 'text'; readonly text: string};
  readonly ownership?: never;
});
export interface DeleteEvidence {
  readonly kind: 'delete';
  readonly eventVersion: string;
  /** Prior record version is distinct from the deletion event version. */
  readonly before: HistoricalRecord;
}

export interface EventContext {
  readonly interfaceVersion: 'truss-history-event/0.1.0';
  readonly sourceEpoch: string;
  readonly historyProfile: string;
  readonly xid: string;
  readonly seq: string;
  readonly identity: TypedIdentity;
  readonly eventVersion: string;
  readonly eventCatalogRevision: string;
  readonly mutationGroup: {
    readonly profile: 'truss-history-group/0.1.0';
    readonly eventCount: string;
    readonly orderedEventDigest: string;
  };
  readonly origin: {
    readonly asserted: ExactValue;
    readonly databaseRole: string;
  };
}
/** Proposed representation; old journal rows do not inherit this profile. */
export type HistoricalEvent = EventContext & (
  {readonly operation: 'create'; readonly after: HistoricalRecord} |
  {readonly operation: 'delete'; readonly before: HistoricalRecord} |
  {
    readonly operation: 'property';
    readonly propertyId: string;
    readonly definitionPin: string;
    readonly before: Presence;
    readonly after: Presence;
  } |
  {
    readonly operation: 'transform';
    readonly propertyId: string;
    readonly beforeDefinitionPin: string;
    readonly afterDefinitionPin: string;
    readonly before: Presence;
    readonly after: Presence;
  } |
  {
    readonly operation: 'rebind';
    readonly retainedName: string;
    readonly propertyId: string;
    readonly beforeDefinitionContext: string;
    readonly afterDefinitionPin: string;
    readonly retainedBefore: Presence;
    readonly retainedAfter: Presence;
    readonly propertyBefore: Presence;
    readonly propertyAfter: Presence;
  } |
  {
    readonly operation: 'metadata';
    readonly before: HistoricalRecord;
    readonly after: HistoricalRecord;
  }
);
