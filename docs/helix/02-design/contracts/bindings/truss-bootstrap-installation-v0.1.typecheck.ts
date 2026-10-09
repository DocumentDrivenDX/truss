import type {BootstrapInstallationTooling,BootstrapInstallationRequest,BootstrapInstallationResult} from './truss-bootstrap-installation-v0.1';
declare const tooling:BootstrapInstallationTooling;
declare const request:BootstrapInstallationRequest;
declare const installed:Extract<BootstrapInstallationResult,{readonly outcome:'installed'}>;
void tooling.installFresh(request);
void tooling.reconcileInstallation('trusted-original-reference');
// @ts-expect-error An uncertain original commit cannot expose an installed marker.
const unknown:BootstrapInstallationResult={outcome:'commit_unknown',recoveryReference:'fixture',originalAttempt:installed.originalAttempt,originalAttemptEvidence:installed.commitObservation,marker:installed.marker};
// @ts-expect-error Installed state requires independent committed inventory.
const incomplete:BootstrapInstallationResult={outcome:'installed',marker:installed.marker,originalAttempt:installed.originalAttempt,commitObservation:installed.commitObservation};
// @ts-expect-error Fresh installation does not take ownership of a caller transaction.
tooling.installFresh({...request,transaction:{}});
void [unknown,incomplete];

import {createBootstrapInstallationTooling} from './truss-bootstrap-installation-v0.1';
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
declare const assembly:ReferenceAssembly;
declare const selection:CapabilitySelection & {readonly family:'bootstrap'};
const constructed=createBootstrapInstallationTooling(assembly,selection);
if(constructed.status==='ok')void constructed.value.installFresh(request);
// @ts-expect-error Runtime mutations are not a bootstrap tooling selection.
createBootstrapInstallationTooling(assembly,{...selection,family:'mutation'});
// @ts-expect-error Tool construction is synchronous and does not await native readiness.
const promise:Promise<typeof constructed>=constructed;
void promise;

const cleanup:BootstrapInstallationResult={outcome:'recovery_required',reason:'cleanup_unknown',recoveryReference:'fixture',originalAttempt:installed.originalAttempt,originalAttemptEvidence:installed.commitObservation};
// @ts-expect-error Cleanup uncertainty cannot expose installed marker authority.
const exposed:BootstrapInstallationResult={...cleanup,marker:installed.marker};
// @ts-expect-error Unresolved cleanup needs exact original attempt evidence.
const lostCleanup:BootstrapInstallationResult={outcome:'recovery_required',reason:'cleanup_unknown',recoveryReference:'fixture',originalAttempt:installed.originalAttempt};
void [cleanup,exposed,lostCleanup];

const {namespaceLockProfile:omittedLock,...withoutLock}=request;
// @ts-expect-error Installation request must pin the actual shared exclusion procedure.
tooling.installFresh(withoutLock);
// @ts-expect-error Display-name lock identity cannot replace a complete profile pin.
tooling.installFresh({...request,namespaceLockProfile:'truss-bootstrap-namespace-lock/0.1.0'});
void omittedLock;

import type {BootstrapReconciliationResult} from './truss-bootstrap-installation-v0.1';
// @ts-expect-error Refusal after preflight requires native containment/termination evidence.
const uncontained:BootstrapInstallationResult={outcome:'refused',reason:'namespace_nonempty'};
// @ts-expect-error Unavailable observation cannot prove the original attempt was refused.
const unavailable:BootstrapReconciliationResult={outcome:'refused',reason:'integrity',containment:{phase:'pre_native'}};
// @ts-expect-error Authorization-unavailable recovery observation exposes no original target.
const disclosed:BootstrapReconciliationResult={outcome:'observation_unavailable',reason:'authorization',originalAttempt:installed.originalAttempt};
void [uncontained,unavailable,disclosed];

const committedUnverified:BootstrapInstallationResult={
 outcome:'committed_unverified',recoveryReference:'trusted-original-reference',
 originalAttempt:installed.originalAttempt,commitObservation:installed.commitObservation,
 originalAttemptEvidence:installed.commitObservation,reason:'drift'
};
const observedCommittedUnverified:BootstrapReconciliationResult=committedUnverified;
// @ts-expect-error Confirmed commit alone cannot publish a ready marker.
const falseReadiness:BootstrapInstallationResult={...committedUnverified,marker:installed.marker};
// @ts-expect-error Unverified current readiness cannot expose complete committed inventory.
const falseInventory:BootstrapInstallationResult={...committedUnverified,committedInventory:installed.committedInventory};
// @ts-expect-error The confirmed-commit branch requires original commit evidence.
const lostCommit:BootstrapInstallationResult={outcome:'committed_unverified',recoveryReference:'fixture',originalAttempt:installed.originalAttempt,originalAttemptEvidence:installed.commitObservation,reason:'profile'};
void [observedCommittedUnverified,falseReadiness,falseInventory,lostCommit];

// @ts-expect-error Unverified generation cannot be submitted for qualified fresh installation.
tooling.installFresh({...request,candidate:{...request.candidate,qualification:{state:'unverified'}}});
