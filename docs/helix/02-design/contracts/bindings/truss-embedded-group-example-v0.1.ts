/** Compile-only public draft usage example; no driver/native implementation. */
import type {Executor,Adoption,Outcome} from './truss-execution-v0.1';
import type {GroupCapability,GroupApplicationResult,GroupRequestSelection} from './truss-group-capability-v0.1';
import type {GroupSemanticInput} from './truss-group-input-v0.1';

/** Host supplies its original live transaction. The host alone ends it. */
export async function applyEmbeddedBatch<HostTransaction>(
  executor:Executor<HostTransaction>, group:GroupCapability,
  adoption:Adoption<HostTransaction>, input:GroupSemanticInput,
  request:GroupRequestSelection,
):Promise<Outcome<GroupApplicationResult>> {
  const adopted=await executor.adoptTransaction(adoption);
  if(adopted.status==='error')return adopted;
  return group.applyInTransaction(adopted.value,input,request);
}

/** Example consumer narrowing; it does not authorize durable publication. */
export function pendingCreatedIdentities(result:Outcome<GroupApplicationResult>) {
  if(result.status!=='ok'||result.value.outcome!=='success')return [];
  const response=result.value.response;
  if(response.durability!=='pending')return [];
  return response.semantic.results.flatMap(operation=>
    operation.outcome==='created'?[operation.identity]:[]);
}
// Returned identities require original live-transaction custody at runtime.
// Do not persist/send them externally until qualified actual outer commit.
// No string transaction ID, commit method or caller callback retry is invented.
