/** Version boundary shape checks; no runtime/native qualification. */
import type {FeedTransactionManifest,FeedAssemblyAssessment,FeedFragmentCursor} from '../../../02-design/contracts/bindings/truss-feed-transaction-v0.1';
import type {FeedTransactionManifestV02,FeedAssemblyAssessmentV02,FeedFragmentCursorV02,FeedFragmentRequestV02} from '../../../02-design/contracts/bindings/truss-feed-key-transition-v0.2';
declare const oldManifest:FeedTransactionManifest;
declare const newManifest:FeedTransactionManifestV02;
declare const complete:Extract<FeedAssemblyAssessmentV02,{readonly state:'complete'}>;
declare const cursor:FeedFragmentCursor;
declare const request:FeedFragmentRequestV02;
// @ts-expect-error v0.1 manifest is not the selected v0.2 complete manifest.
const oldAsNew:FeedTransactionManifestV02=oldManifest;
// @ts-expect-error v0.2 required member cannot silently downcast to v0.1.
const newAsOld:FeedTransactionManifest=newManifest;
// @ts-expect-error Complete v0.2 assembly is not complete v0.1 evidence.
const assembly:FeedAssemblyAssessment=complete;
// @ts-expect-error Original v0.1 cursor cannot resume a v0.2 fragment.
const resume:FeedFragmentCursorV02=cursor;
// @ts-expect-error Request cannot mix v0.2 manifest and v0.1 continuation.
const mixed:FeedFragmentRequestV02={...request,continuation:{state:'after',cursor}};

import type {ConsumerAppliedBoundary} from '../../../02-design/contracts/bindings/truss-feed-worker-v0.1';
import type {ConsumerAppliedBoundaryV02,FeedDiscoveryRequestV02} from '../../../02-design/contracts/bindings/truss-feed-key-transition-v0.2';
declare const oldProgress:ConsumerAppliedBoundary;
declare const discovery:FeedDiscoveryRequestV02;
// @ts-expect-error Old progress lacks selected v0.2 domains or required seed profile.
const oldProgressAsNew:ConsumerAppliedBoundaryV02=oldProgress;
// @ts-expect-error Discovery cannot use an unqualified v0.1 progress boundary.
const mixedDiscovery:FeedDiscoveryRequestV02={...discovery,after:oldProgress};

import type {VerifiedApplication,ApplicationProofSubmission} from '../../../02-design/contracts/bindings/truss-feed-worker-v0.1';
import type {VerifiedApplicationV02,ApplicationProofSubmissionV02,ConsumerAcknowledgmentV02} from '../../../02-design/contracts/bindings/truss-feed-key-transition-v0.2';
declare const oldVerified:VerifiedApplication;
declare const oldProof:ApplicationProofSubmission;
declare const acknowledgment:ConsumerAcknowledgmentV02;
// @ts-expect-error v0.1 verifier custody cannot authorize v0.2 application.
const upgradedVerified:VerifiedApplicationV02=oldVerified;
// @ts-expect-error v0.1 proof cannot silently omit required transition coverage.
const upgradedProof:ApplicationProofSubmissionV02=oldProof;
// @ts-expect-error Acknowledgment must carry original v0.2 verified application.
const mixedAck:ConsumerAcknowledgmentV02={...acknowledgment,application:oldVerified};

import type {FeedApplicationRequestV02,FeedApplicationResultV02} from '../../../02-design/contracts/bindings/truss-feed-key-transition-v0.2';
import type {FeedApplicationRequest,FeedApplicationResult} from '../../../02-design/contracts/bindings/truss-feed-application-adapter-v0.1';
declare const oldApply:FeedApplicationRequest;
declare const oldApplied:Extract<FeedApplicationResult,{readonly outcome:'applied'|'equal'}>;
// @ts-expect-error Old installation/assembly cannot supply v0.2 application request.
const upgradedApply:FeedApplicationRequestV02=oldApply;
// @ts-expect-error v0.1 application proof cannot certify v0.2 applied result.
const upgradedApplied:FeedApplicationResultV02=oldApplied;

import type {SeedBaseline} from '../../../02-design/contracts/bindings/truss-seed-baseline-v0.1';
import type {SeedBaselineV02} from '../../../02-design/contracts/bindings/truss-feed-key-transition-v0.2';
declare const oldBaseline:SeedBaseline;
// @ts-expect-error Graph/configuration-only v0.1 seed lacks selected binding and transition closure.
const upgradedBaseline:SeedBaselineV02=oldBaseline;
