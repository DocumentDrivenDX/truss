/** Independent public consumer witnesses; no compiler/native qualification. */
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
import type {CompiledExecutionRequest,CompiledExecutionResult} from './truss-compiled-execution-capability-v0.1';
declare const assembly:ReferenceAssembly;
declare const selection:CapabilitySelection & {readonly family:'weft_execution'};
declare const transaction:TransactionHandle;
declare const request:CompiledExecutionRequest;
const selected=assembly.compiledExecution(selection);
if(selected.status==='ok') {
 void selected.capability.executeInTransaction(transaction,request);
 // @ts-expect-error Arbitrary SQL is not an exact registered compilation artifact.
 selected.capability.executeInTransaction(transaction,{interfaceVersion:'truss-compiled-execution/0.1.0',sql:'select 1',bridgeProfile:request.bridgeProfile});
}
// @ts-expect-error A refused artifact cannot expose partial decoded output.
const partial:CompiledExecutionResult={outcome:'refused',reason:'pins',diagnosticProfile:request.bridgeProfile,diagnostic:request.artifact,result:request.artifact};
// @ts-expect-error Execution observation is mandatory, not inferred from successful artifact admission.
const missing:CompiledExecutionResult={outcome:'executed',artifactSha256:'digest',bridgeProfile:request.bridgeProfile,result:request.artifact};
void [partial,missing];
