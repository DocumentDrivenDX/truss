/** CONTRACT-004 candidate direct reads; not a compiler or authorization token. */
import type {ProfilePin} from './truss-acceptance-input-v0.1';
import type {HistoricalRecord, TypedIdentity, QualifiedOwner, ExactValue} from './truss-history-v0.1';
export interface ReadTypeReference {
  readonly typeId: string; readonly definitionPin: string; readonly owner: QualifiedOwner;
}
export interface ReadRelationshipReference {
  readonly relationshipId: string; readonly definitionPin: string; readonly owner: QualifiedOwner;
}
export interface DirectReadContext {
  readonly catalogRevision: string;
  readonly layoutProfile: ProfilePin;
  readonly readProfile: ProfilePin;
  readonly authorizedScopeIdentity: string;
  readonly consistency: {readonly kind: 'live'} | {
    readonly kind: 'held_snapshot'; readonly snapshotIdentity: string;
  };
}
/** Carrier shape reused; a live read does not certify retained history. */
export interface DirectRecord {
  readonly view: 'current';
  readonly readCatalogRevision: string;
  readonly record: HistoricalRecord;
}
export type DirectContinuation = {
  readonly interfaceVersion: 'truss-direct-cursor/0.1.0';
  readonly context: DirectReadContext;
  readonly selection: {readonly operation: 'objects'; readonly type: ReadTypeReference};
  readonly after: {readonly id: string};
} | {
  readonly interfaceVersion: 'truss-direct-cursor/0.1.0';
  readonly context: DirectReadContext;
  readonly selection: {
    readonly operation: 'edges'; readonly object: TypedIdentity;
    readonly direction: 'outgoing' | 'incoming' | 'both';
    readonly relationships: readonly ReadRelationshipReference[];
  };
  readonly after: {
    readonly id: string;
    readonly orderKey: {readonly state: 'null'} | {readonly state: 'text'; readonly text: string};
  };
};
export interface DirectPageRequest {
  readonly interfaceVersion: 'truss-direct-page-request/0.1.0';
  readonly context: DirectReadContext;
  readonly selection: DirectContinuation['selection'];
  readonly limit: string;
  readonly continuation: {readonly state: 'first'} | {readonly state: 'after'; readonly cursor: DirectContinuation};
}
export interface DirectPage {
  readonly context: DirectReadContext;
  readonly records: readonly DirectRecord[];
  readonly continuation: {readonly state: 'end'} | {readonly state: 'more'; readonly cursor: DirectContinuation};
}
/** Read admission result; executor transport failures remain CONTRACT-007 outcomes. */
export type DirectPageResult = {
  readonly outcome: 'page'; readonly page: DirectPage;
} | {
  readonly outcome: 'invalid'; readonly code: string; readonly path: readonly string[];
  readonly page?: never;
} | {
  readonly outcome: 'unavailable';
  readonly reason: 'context' | 'profile' | 'snapshot' | 'observation' | 'resource';
  readonly page?: never;
};
export type DirectLookupRequest = {
  readonly context: DirectReadContext;
  readonly selection: {readonly operation: 'object_id'; readonly type: ReadTypeReference; readonly id: string};
} | {
  readonly context: DirectReadContext;
  readonly selection: {readonly operation: 'edge_id'; readonly id: string};
} | {
  readonly context: DirectReadContext;
  readonly selection: {
    readonly operation: 'object_key'; readonly type: ReadTypeReference;
    readonly keyNumber: string; readonly keyDefinitionPin: string;
    readonly keyEncodingProfile: ProfilePin;
    readonly components: readonly [{readonly propertyId: string; readonly definitionPin: string; readonly value: ExactValue},
      ...{readonly propertyId: string; readonly definitionPin: string; readonly value: ExactValue}[]];
  };
};
export type DirectLookupResult = {
  readonly outcome: 'found'; readonly context: DirectReadContext; readonly record: DirectRecord;
} | {
  readonly outcome: 'not_found';
  readonly record?: never;
} | {
  readonly outcome: 'invalid'; readonly code: string; readonly path: readonly string[];
  readonly record?: never;
} | {
  readonly outcome: 'unavailable';
  readonly reason: 'context' | 'profile' | 'snapshot' | 'observation' | 'resource';
  readonly record?: never;
};
