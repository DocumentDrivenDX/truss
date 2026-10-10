/** Public extraction/staging witnesses; no snapshot or durable custody proof. */
import type {SeedExtractionTooling,SeedExtractionRequest,SeedExtractionResult,ReplacementSeedExtractionRequest} from './truss-seed-extraction-v0.1';
import type {HostSeedStagingAdapter,SeedStagingRequest,SeedStagingResult} from './truss-seed-staging-v0.1';
declare const tooling:SeedExtractionTooling;
declare const adapter:HostSeedStagingAdapter;
declare const request:SeedExtractionRequest;
declare const stageRequest:SeedStagingRequest;
declare const replacement:ReplacementSeedExtractionRequest;
void tooling.extract(request);
void tooling.extractReplacement(replacement);
void adapter.stage(stageRequest);
void adapter.reconcileStage('trusted-original-reference');
// @ts-expect-error Failed extraction cannot expose a partial visibility classifier.
const partial:SeedExtractionResult={outcome:'unavailable',reason:'resource',visibility:stageRequest.extraction.visibility};
// @ts-expect-error Unresolved extraction cannot feed staging as a completed baseline.
adapter.stage({...stageRequest,extraction:{outcome:'recovery_required',recoveryReference:'fixture',originalAttemptEvidence:stageRequest.extraction.extractionEvidence}});
// @ts-expect-error Staged success requires durable custody evidence.
const unretained:SeedStagingResult={outcome:'staged',stage:{state:'staged',attempt:stageRequest.extraction.attempt,pins:{visibilityManifestSha256:'v',baselineInventorySha256:'i',baselineSha256:'b'},inclusiveReplayXmin:'1',validationEvidenceSha256:'e',downstreamStageIdentity:'s'}};
// @ts-expect-error Recovery cannot claim an ordinary staged descriptor.
const uncertain:SeedStagingResult={outcome:'recovery_required',recoveryReference:'fixture',originalAttemptEvidence:stageRequest.extraction.extractionEvidence,stage:unretained.stage};
void [partial,unretained,uncertain];

// @ts-expect-error Initial registration admission cannot substitute for a durable reseed receipt.
tooling.extractReplacement(request);
// @ts-expect-error Removal outcome cannot authorize replacement extraction.
const removed:ReplacementSeedExtractionRequest={...replacement,reseedReceipt:{...replacement.reseedReceipt,result:{outcome:'removed',retiredRegistrationId:'old',finalGeneration:'1',downstreamStatus:'fenced',auditEvidence:stageRequest.sourceAdmission}}};
// @ts-expect-error The receipt must contain the original begin_reseed request, not just result hashes.
const abbreviated:ReplacementSeedExtractionRequest={...replacement,reseedReceipt:{interfaceVersion:'truss-feed-administration-receipt/0.1.0',sourceEpoch:'fixture',administrativeNamespace:'fixture',canonicalInputSha256:'digest',result:replacement.reseedReceipt.result,actualDatabaseRole:'fixture',authorizationEvidence:stageRequest.sourceAdmission}};
void [removed,abbreviated];
