/** Public application witnesses; native fence/dedup/atomicity remains open. */
import type {HostFeedApplicationAdapter,FeedApplicationRequest,FeedApplicationResult,FeedCoverageApplicationRequest} from './truss-feed-application-adapter-v0.1';
import type {ConsumerAcknowledgment} from './truss-feed-worker-v0.1';
declare const adapter:HostFeedApplicationAdapter;
declare const request:FeedApplicationRequest;
declare const result:Extract<FeedApplicationResult,{readonly outcome:'applied'|'equal'}>;
declare const acknowledgment:ConsumerAcknowledgment;
void adapter.apply(request);
void adapter.reconcileApplication('trusted-original-reference');
// @ts-expect-error Incomplete fragment assembly cannot be applied.
adapter.apply({...request,transaction:{state:'incomplete',missingOrdinals:['1']}});
// @ts-expect-error Uncertain downstream commit cannot issue application proof.
const uncertain:FeedApplicationResult={outcome:'commit_unknown',recoveryReference:'fixture',originalAttemptEvidence:result.committedApplicationEvidence,proofSubmission:result.proofSubmission};
// @ts-expect-error Submitted evidence is not a host-issued verified application capability.
const unverified:ConsumerAcknowledgment={...acknowledgment,application:result.proofSubmission};
// @ts-expect-error Confirmed application must retain exact committed evidence.
const lost:FeedApplicationResult={outcome:'applied',proofSubmission:result.proofSubmission};
void [uncertain,unverified,lost];

declare const coverage:FeedCoverageApplicationRequest;
void adapter.advanceCoverage(coverage);
// @ts-expect-error A discovery interval alone omits durable downstream accounting.
adapter.advanceCoverage({...coverage,coverage:{fromInclusiveXid:'10',throughExclusiveXid:'20'}});
// @ts-expect-error Coverage cannot be submitted as a complete transaction assembly.
adapter.apply({...request,transaction:coverage.coverage});
