/** Design-only original issuer and role distinctions. */
import type {TraversalStageLease,TraversalStageRegistration,TraversalStageConfiguration,TraversalStageOpenRequest,TraversalStagePublishResult} from './truss-traversal-stage-service-v0.1';
import type {TraversalStageHandle} from './truss-direct-traversal-v0.1';
declare const handle:TraversalStageHandle;declare const config:TraversalStageConfiguration;
// @ts-expect-error Public wire handle cannot mint an original store lease.
const forged:TraversalStageLease=handle;
// @ts-expect-error Configuration cannot mint registration custody.
const registration:TraversalStageRegistration={configuration:config};
// @ts-expect-error Direct stage service cannot select a group family.
const wrong:TraversalStageConfiguration={...config,selection:{...config.selection,family:'group'}};
// @ts-expect-error Resume requires original adopted transaction and exact request.
const incomplete:TraversalStageOpenRequest={intent:'resume',handle};
// @ts-expect-error Unresolved publication retains nonempty recovery custody.
const empty:TraversalStagePublishResult={outcome:'unresolved',recoveryReferences:[]};
void forged;void registration;void wrong;void incomplete;void empty;

import type {TraversalWorkPermit,TraversalWorkAdmission} from './truss-traversal-stage-service-v0.1';
// @ts-expect-error Store lease is not a pre-work resource permit.
const uncharged:TraversalWorkPermit=forged;
// @ts-expect-error Refused capacity cannot retain a usable work permit.
const refused:TraversalWorkAdmission={outcome:'unavailable',reason:'resource',permit:uncharged};
void uncharged;void refused;

import type {TraversalStagePublication} from './truss-traversal-stage-service-v0.1';
declare const publication:TraversalStagePublication;
const {expectedAccountingVersion: omitted, ...stalePublication}=publication;
// @ts-expect-error Frontier version alone cannot select a resource ledger cut.
const unbound:TraversalStagePublication=stalePublication;
void omitted;void unbound;
