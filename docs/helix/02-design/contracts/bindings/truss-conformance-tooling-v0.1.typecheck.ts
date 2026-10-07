import type {ConformanceRunResult,ConformanceAssessment,ConformanceRunRequest} from './truss-conformance-tooling-v0.1';
declare const request:ConformanceRunRequest;
declare const recorded:Extract<ConformanceRunResult,{readonly outcome:'recorded'}>;
// @ts-expect-error Recorded execution does not by itself qualify a support claim.
const qualified:ConformanceAssessment=recorded;
// @ts-expect-error Input content cannot nominate a shell command or trusted runner.
const command:ConformanceRunRequest={...request,command:'run arbitrary'};
// @ts-expect-error An unavailable run cannot expose a receipt as executed evidence.
const missing:ConformanceRunResult={outcome:'unavailable',reason:'custody',receipt:recorded.receipt};
void [qualified,command,missing];

import {createConformanceEvidenceTooling} from './truss-conformance-tooling-v0.1';
import type {ConformanceEvidenceConfiguration,HostConformanceAssessor} from './truss-conformance-tooling-v0.1';
declare const configuration:ConformanceEvidenceConfiguration;
declare const assessor:HostConformanceAssessor;
void createConformanceEvidenceTooling(configuration,assessor);
// @ts-expect-error Empty approved manifests cannot permit vacuous qualification.
createConformanceEvidenceTooling({...configuration,approvedManifests:[]},assessor);
// @ts-expect-error A receipt trust flag cannot replace the registered host assessor.
createConformanceEvidenceTooling(configuration,{trusted:true});

import type {HostConformanceRunner,PreparedConformanceRun} from './truss-conformance-tooling-v0.1';
declare const runner:HostConformanceRunner;
declare const prepared:PreparedConformanceRun;
void runner.prepareRun(request);void runner.run(prepared);void runner.reconcileRun(prepared.recoveryReference);
// @ts-expect-error A request has no original registered prepared-run custody.
void runner.run(request);
// @ts-expect-error Recovery metadata alone cannot mint run authority.
const forgedPrepared:PreparedConformanceRun={recoveryReference:'claimed'};
void forgedPrepared;

import type {ConformanceReconciliationResult} from './truss-conformance-tooling-v0.1';
// @ts-expect-error Preparation evidence alone cannot prove original abandonment.
const unprovenAbandonment:ConformanceReconciliationResult={outcome:'abandoned',originalPreparation:recorded.receipt};
// @ts-expect-error Prepared observation cannot claim recorded execution evidence.
const preparedReceipt:ConformanceReconciliationResult={outcome:'prepared',run:prepared,receipt:recorded.receipt};
void [unprovenAbandonment,preparedReceipt];

import {createConformanceRunTooling} from './truss-conformance-tooling-v0.1';
import type {ConformanceRunConfiguration} from './truss-conformance-tooling-v0.1';
declare const runConfiguration:ConformanceRunConfiguration;
void createConformanceRunTooling(runConfiguration,runner);
// @ts-expect-error Runner manifest approval cannot be empty.
createConformanceRunTooling({...runConfiguration,approvedManifests:[]},runner);
// @ts-expect-error Caller trust metadata cannot supply original runner methods/custody.
createConformanceRunTooling(runConfiguration,{trusted:true});
