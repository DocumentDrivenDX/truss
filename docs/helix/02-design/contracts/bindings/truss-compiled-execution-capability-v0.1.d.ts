/** CONTRACT-007/SD-005 candidate; Weft owns the artifact/result decoding ABI. */
import type {ExactArtifact, ProfilePin} from './truss-acceptance-input-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {Outcome, TransactionHandle} from './truss-execution-v0.1';
export interface CompiledExecutionRequest {
 readonly interfaceVersion:'truss-compiled-execution/0.1.0';
 /** Exact registered Weft compiled response bytes, not arbitrary SQL. */
 readonly artifact:ExactArtifact;
 /** Pins artifact admission, native obligation discharge and exact output transport. */
 readonly bridgeProfile:ProfilePin;
}
export type CompiledExecutionResult = {
 readonly outcome:'executed';
 /** Exact admitted artifact identity; no rewritten compiler provenance. */
 readonly artifactSha256:string;
 readonly bridgeProfile:ProfilePin;
 /** Profile-defined ordered columns/rows, exact values and presence semantics. */
 readonly result:ExactArtifact;
 /** Per-call native context and obligation evidence, never a reusable authority token. */
 readonly observation:ExactArtifact;
} | {
 readonly outcome:'refused';
 readonly reason:'artifact'|'profile'|'provenance'|'pins'|'obligation'|'authority'|'resource';
 readonly diagnosticProfile:ProfilePin;
 readonly diagnostic:ExactArtifact;
 readonly result?:never;
} ;
export interface CompiledExecutionCapability {
 readonly selection:CapabilitySelection & {readonly family:'weft_execution'};
 executeInTransaction(transaction:TransactionHandle,request:CompiledExecutionRequest):Promise<Outcome<CompiledExecutionResult>>;
}
export type CompiledExecutionCapabilityResult = {
 readonly status:'ok';readonly capability:CompiledExecutionCapability;
} | {readonly status:'unavailable';readonly reason:'selection'|'disposed'};
