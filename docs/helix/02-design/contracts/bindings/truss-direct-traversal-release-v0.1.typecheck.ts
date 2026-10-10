/** Design-only lifetime/error distinctions. */
import type {DirectReadCapability} from './truss-direct-read-capability-v0.1';
import type {TraversalStageHandle, TraversalReleaseResult, TraversalResult} from './truss-direct-traversal-v0.1';
declare const facade: DirectReadCapability; declare const handle: TraversalStageHandle;
void facade.releaseTraversal({handle});
// @ts-expect-error Cleanup cannot accept a hidden host rollback option.
void facade.releaseTraversal({handle,rollback:true});
// @ts-expect-error Unresolved cleanup must retain at least one original recovery reference.
const empty: TraversalReleaseResult = {outcome:'unresolved',recoveryReferences:[]};
// @ts-expect-error Invalid traversal cannot disclose partial records.
const partial: TraversalResult = {outcome:'invalid',code:'hops',path:[],records:[]};
void empty;void partial;
