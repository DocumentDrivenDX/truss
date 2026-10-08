/** CONTRACT-004 candidate node traversal, distinct from Weft relational bags. */
import type {DirectReadContext, DirectRecord, ReadRelationshipReference} from './truss-direct-read-v0.1';
import type {TypedIdentity} from './truss-history-v0.1';
export interface TraversalHop {
  readonly relationship: ReadRelationshipReference;
  readonly direction: 'outgoing' | 'incoming' | 'both';
}
export interface TraversalRequest {
  readonly interfaceVersion: 'truss-direct-traversal/0.1.0';
  readonly context: DirectReadContext;
  readonly start: TypedIdentity;
  readonly hops: readonly [TraversalHop] | readonly [TraversalHop, TraversalHop] |
    readonly [TraversalHop, TraversalHop, TraversalHop];
  readonly resultLimit: string;
  readonly workLimits: {
    readonly examinedEdges: string;
    readonly pathStates: string;
    readonly retainedBytes: string;
  };
}
export interface TraversalStageHandle {
  readonly stageIdentity: string;
  readonly generation: string;
  readonly querySha256: string;
  readonly context: DirectReadContext;
}
export interface TraversalResultCursor {
  readonly handle: TraversalStageHandle;
  readonly after: {readonly typeId: string; readonly id: string};
}
export interface TraversalResumeRequest {
  readonly handle: TraversalStageHandle;
  readonly expectedWorkVersion: string;
  /** Cumulative counters survive resume; new bounds require host admission. */
  readonly workLimits: TraversalRequest['workLimits'];
  readonly resultLimit: string;
}
export interface TraversalNextPageRequest {
  readonly cursor: TraversalResultCursor;
  readonly resultLimit: string;
}
export type TraversalResult = {
  readonly outcome: 'page'; readonly context: DirectReadContext;
  readonly records: readonly DirectRecord[];
  readonly continuation: {readonly state: 'end'} | {
    readonly state: 'more'; readonly cursor: TraversalResultCursor;
  };
} | {
  readonly outcome: 'limited';
  readonly reason: 'examined_edges' | 'path_states' | 'retained_bytes' | 'active_work';
  readonly completeness: 'not_established';
  readonly continuation: {readonly state: 'restart'} | {
    readonly state: 'staged'; readonly handle: TraversalStageHandle; readonly workVersion: string;
  };
  readonly records?: never;
} | {
  readonly outcome: 'invalid'; readonly code: string; readonly path: readonly string[];
  readonly records?: never;
} | {
  readonly outcome: 'unavailable';
  readonly reason: 'context' | 'profile' | 'snapshot' | 'authorization' | 'observation' | 'resource';
  readonly records?: never;
};

/** Cleanup uses original stage registry custody even after the data snapshot ends. */
export interface TraversalReleaseRequest { readonly handle: TraversalStageHandle; }
export type TraversalReleaseResult = {
  readonly outcome: 'released';
} | {
  readonly outcome: 'unresolved';
  readonly recoveryReferences: readonly [string, ...string[]];
} | {
  readonly outcome: 'unavailable'; readonly reason: 'ownership' | 'profile';
};
