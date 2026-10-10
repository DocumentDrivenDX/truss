/** CONTRACT-007 tooling projection over an existing assembly; inert construction. */
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {FeedAdministrativeTooling} from './truss-feed-administration-v0.1';
import type {FeedConsumerRegistration} from './truss-feed-registration-v0.1';
import type {FeedWorkerAdministration} from './truss-feed-worker-administration-v0.1';
import type {SeedExtractionTooling} from './truss-seed-extraction-v0.1';
import type {SeedSourceConfirmation} from './truss-seed-confirmation-v0.1';
import type {SeedAbandonmentTooling} from './truss-seed-abandonment-v0.1';
import type {SeedRestartTooling} from './truss-seed-restart-v0.1';
export interface FeedLifecycleTooling {
 readonly selection:CapabilitySelection & {readonly family:'feed'};
 readonly administration:FeedAdministrativeTooling;
 readonly registration:FeedConsumerRegistration;
 readonly workers:FeedWorkerAdministration;
 readonly extraction:SeedExtractionTooling;
 readonly confirmation:SeedSourceConfirmation;
 readonly abandonment:SeedAbandonmentTooling;
 readonly restart:SeedRestartTooling;
}
export type FeedToolingConstructionResult = {
 readonly status:'ok';readonly value:FeedLifecycleTooling;
} | {
 readonly status:'error';
 readonly code:'disposed'|'unsupported_profile'|'incompatible_selection';
};
/** No database/host service access, implicit worker, seed or transaction startup. */
export declare function createFeedLifecycleTooling(
 assembly:ReferenceAssembly,
 selection:CapabilitySelection & {readonly family:'feed'}
):FeedToolingConstructionResult;
