/** Design-only consumer witnesses; no acceptance/native qualification. */
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {AcceptanceInput, AcceptanceAttemptContext} from './truss-acceptance-input-v0.1';
import type {AcceptanceReport, AcceptanceSemanticResult, AcceptanceRejection} from './truss-acceptance-report-v0.1';
import type {EnforcementReport} from './truss-enforcement-report-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
declare const assembly:ReferenceAssembly;
declare const selection:CapabilitySelection & {readonly family:'catalog'};
declare const transaction:TransactionHandle;
declare const input:AcceptanceInput;
declare const origin:AcceptanceAttemptContext['assertedOrigin'];
declare const report:AcceptanceReport;
declare const rejection:AcceptanceRejection;
const selected=assembly.catalog(selection);
if(selected.status==='ok')void selected.capability.acceptInTransaction(transaction,input,origin);
// @ts-expect-error Rejection cannot carry an accepted report.
const falseAccepted:AcceptanceSemanticResult={outcome:'rejected',rejection,report};
// @ts-expect-error Rejection cannot claim an accepted revision.
const falseRevision:AcceptanceRejection={...rejection,acceptedRevision:'2'};
declare const projection:EnforcementReport & {readonly scope:{readonly kind:'authorized_projection';readonly authorizedScopeIdentity:string}};
// @ts-expect-error A projection cannot be the accepted report's complete assertion inventory.
const falseComplete:AcceptanceReport={...report,assertions:projection};
// @ts-expect-error Semantic acceptance cannot itself declare committed durability.
const prematureCommit:AcceptanceSemanticResult={outcome:'accepted',disposition:'new',report,durability:'committed'};
void [falseAccepted,falseRevision,falseComplete,prematureCommit];
