import type {AssemblyConstructionResult, AssemblyDisposalResult} from './truss-reference-assembly-v0.1';
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const invalid: AssemblyConstructionResult={status:'error',code:'invalid_configuration',diagnosticProfile:pin};
// @ts-expect-error Construction cannot report uncertain transaction commit.
const commit: AssemblyConstructionResult={status:'error',code:'commit_unknown',diagnosticProfile:pin};
// @ts-expect-error Quarantine must carry nonempty recovery references.
const empty: AssemblyDisposalResult={state:'quarantined',ownedResourcesReleased:false,reason:'native_work_unresolved',recoveryReferences:[]};
// @ts-expect-error Disposed cannot claim unresolved owned resources.
const leaked: AssemblyDisposalResult={state:'disposed',ownedResourcesReleased:false};
void [invalid,commit,empty,leaked];
