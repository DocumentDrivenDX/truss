/** CONTRACT-007 draft bound facade; obtaining a handle performs no native I/O. */
import type {Outcome, TransactionHandle} from './truss-execution-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {DirectLookupRequest, DirectLookupResult, DirectPageRequest, DirectPageResult} from './truss-direct-read-v0.1';
import type {CatalogViewRequest, CatalogViewResult} from './truss-catalog-view-v0.1';
import type {TraversalRequest, TraversalResumeRequest, TraversalNextPageRequest, TraversalResult, TraversalReleaseRequest, TraversalReleaseResult} from './truss-direct-traversal-v0.1';
export interface DirectReadCapability {
  readonly selection: CapabilitySelection & {readonly family: 'direct_read'};
  lookup(transaction: TransactionHandle, request: DirectLookupRequest): Promise<Outcome<DirectLookupResult>>;
  page(transaction: TransactionHandle, request: DirectPageRequest): Promise<Outcome<DirectPageResult>>;
  catalogView(transaction: TransactionHandle, request: CatalogViewRequest): Promise<Outcome<CatalogViewResult>>;
  traverse(transaction: TransactionHandle, request: TraversalRequest): Promise<Outcome<TraversalResult>>;
  resumeTraversal(transaction: TransactionHandle, request: TraversalResumeRequest): Promise<Outcome<TraversalResult>>;
  releaseTraversal(request: TraversalReleaseRequest): Promise<Outcome<TraversalReleaseResult>>;
  nextTraversalPage(transaction: TransactionHandle, request: TraversalNextPageRequest): Promise<Outcome<TraversalResult>>;
}
export type DirectReadCapabilityResult = {
  readonly status: 'ok'; readonly capability: DirectReadCapability;
} | {
  readonly status: 'unavailable';
  readonly reason: 'selection' | 'disposed';
};
