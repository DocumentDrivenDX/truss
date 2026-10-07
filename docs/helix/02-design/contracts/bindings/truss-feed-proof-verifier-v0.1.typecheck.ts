/** Host-service consumer witnesses only; runtime trust remains profile-qualified. */
import type {HostFeedProofVerifier,FeedProofVerifierRegistration} from './truss-feed-proof-verifier-v0.1';
import type {ApplicationProofSubmission,VerifiedApplication} from './truss-feed-worker-v0.1';
import type {HostRecoveryRegistry} from './truss-recovery-registry-v0.1';
import type {ReferenceAssemblyConfiguration} from './truss-reference-assembly-v0.1';
import {createReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {Executor} from './truss-execution-v0.1';
declare const verifier:HostFeedProofVerifier;
declare const submission:ApplicationProofSubmission;
declare const application:VerifiedApplication;
declare const registration:FeedProofVerifierRegistration;
declare const recoveryRegistry:HostRecoveryRegistry;
declare const configuration:ReferenceAssemblyConfiguration;
declare const executor:Executor<unknown>;
void verifier.assess(submission);
void verifier.recognizes(application);
void createReferenceAssembly(configuration,executor,{recoveryRegistry});
void createReferenceAssembly(configuration,executor,{recoveryRegistry,feedProofVerifiers:[registration]});
// @ts-expect-error A submitted proof has not acquired issuer custody.
verifier.recognizes(submission);
// @ts-expect-error Registration requires explicit feed capability-profile selection.
const unbound:FeedProofVerifierRegistration={verifier};
// @ts-expect-error Host service cannot replace an unavailable assessment with unverified submission.
const fake:HostFeedProofVerifier={...verifier,assess:async()=>({outcome:'verified',application:submission})};
void [unbound,fake];
