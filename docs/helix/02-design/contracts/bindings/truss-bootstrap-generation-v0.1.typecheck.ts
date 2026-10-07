import type {BootstrapBundle,BootstrapGenerationTooling,BootstrapGenerationResult,BootstrapGenerationRequest} from './truss-bootstrap-generation-v0.1';
declare const bundle:BootstrapBundle;
declare const tooling:BootstrapGenerationTooling;
declare const candidate:Extract<BootstrapGenerationResult,{readonly outcome:'candidate'}>;
declare const request:BootstrapGenerationRequest;
void tooling.generate(request);
// @ts-expect-error Blocked generation never exposes installable SQL.
const blocked:BootstrapGenerationResult={outcome:'blocked',diagnosticProfile:tooling.generationProfile,diagnostics:candidate.sql,sql:candidate.sql};
// @ts-expect-error A generated candidate is not an installed layout marker.
const ready:BootstrapGenerationResult={...candidate,installed:true};
// @ts-expect-error Generator identity cannot be an executable callback in model content.
const executable:BootstrapBundle={...bundle,generator:()=>candidate};
void [blocked,ready,executable];

const {statementInventory:omitted,...withoutInventory}=candidate;
// @ts-expect-error Candidate SQL needs complete exporter statement correspondence.
const incomplete:BootstrapGenerationResult=withoutInventory;
// @ts-expect-error Every emitted statement needs original source paths.
const sourceless:typeof candidate.statementInventory={...candidate.statementInventory,statements:[{ordinal:'0',sql:candidate.sql,sources:[]}]};
// @ts-expect-error Blocked generation cannot expose partial executable statements.
const partial:BootstrapGenerationResult={outcome:'blocked',diagnosticProfile:tooling.generationProfile,diagnostics:candidate.sql,statementInventory:candidate.statementInventory};
void [omitted,incomplete,sourceless,partial];

// @ts-expect-error A bare bundle omits the operation resource contract.
tooling.generate(bundle);
// @ts-expect-error Exact output byte bounds cannot be host numbers.
tooling.generate({...request,limits:{...request.limits,outputBytes:1024}});

// @ts-expect-error Supplied native qualification must carry exact original evidence.
tooling.generate({...request,qualification:{state:'supplied',targetProfile:tooling.generationProfile}});

// @ts-expect-error Undifferentiated source pins cannot define an acyclic qualification basis.
const circular:BootstrapGenerationResult={...candidate,sourcePins:[candidate.sql]};
// @ts-expect-error Complete generation has nonempty original source inventory.
const noOriginal:BootstrapGenerationResult={...candidate,sourcePins:{generation:[],qualification:[]}};
void [circular,noOriginal];

const {bundleArtifact:omittedBundleArtifact,...withoutBundleArtifact}=candidate;
// @ts-expect-error A candidate retains the actual canonical bundle digest preimage bytes.
const noPreimage:BootstrapGenerationResult=withoutBundleArtifact;
void [omittedBundleArtifact,noPreimage];
