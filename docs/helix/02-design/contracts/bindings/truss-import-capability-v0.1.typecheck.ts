/** Public consumer witnesses only; no import/native durability claim. */
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {ImportInput} from './truss-import-input-v0.1';
import type {ImportReport} from './truss-import-report-v0.1';
import type {ImportExecutionResult} from './truss-import-capability-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
declare const assembly:ReferenceAssembly;
declare const selection:CapabilitySelection & {readonly family:'import'};
declare const input:ImportInput;
declare const transaction:TransactionHandle;
declare const report:ImportReport;
const capability=assembly.imports(selection);
if(capability.status==='ok') {
 void capability.capability.applyInTransaction(transaction,input);
 void capability.capability.runBatches(input,{isolation:'read_committed',accessMode:'read_write'});
 // @ts-expect-error Batch-owning imports cannot request a read-only writer scope.
 capability.capability.runBatches(input,{isolation:'read_committed',accessMode:'read_only'});
}
// @ts-expect-error Invalid envelope cannot return prior writer progress.
const mixed:ImportExecutionResult<ImportReport>={outcome:'invalid',diagnosticProfile:{identity:'fixture',version:'0.1.0',sha256:'digest'},diagnostic:{identity:'fixture',bytesBase64:'e30=',sha256:'digest'},report};
// @ts-expect-error Execution failure must explicitly preserve report or prove no submission via null.
const lost:ImportExecutionResult<ImportReport>={outcome:'execution_failed',error:{code:'cancelled',retryScope:'none',message:'fixture'}};
void [mixed,lost];

// @ts-expect-error Resource interruption cannot omit coherent progress.
const noProgress:ImportExecutionResult<ImportReport>={outcome:'resource_limited',reason:'candidate_bytes',resourceProfile:{identity:'fixture',version:'0.1.0',sha256:'digest'}};
// @ts-expect-error A processed report cannot represent resource interruption.
const falseComplete:ImportExecutionResult<ImportReport>={outcome:'resource_limited',reason:'operation_deadline',resourceProfile:{identity:'fixture',version:'0.1.0',sha256:'digest'},report:{...report,status:'processed'}};
void noProgress;void falseComplete;
