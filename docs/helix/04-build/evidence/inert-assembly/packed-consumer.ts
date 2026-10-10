import {createReferenceAssembly,INERT_ASSEMBLY_PROFILE} from '@documentdrivendx/truss-postgresql';
import type {Executor,TransactionHandle,ReferenceAssembly,ProfilePin} from '@documentdrivendx/truss-postgresql';
const p:ProfilePin={identity:'fixture-unqualified',version:'0.12',sha256:'a'.repeat(64)};
let calls=0;const fail=async():Promise<never>=>{calls++;throw Error('Unexpected native call')};
const executor:Executor<unknown>={withTransaction:fail,adoptTransaction:fail,execute:fail,savepoint:fail,rollbackToSavepoint:fail,releaseSavepoint:fail};
const selection={family:'direct_read' as const,capabilityProfile:p,layoutProfile:p,adapterProfile:p,valueProfile:p,policyProfile:p};
const result=createReferenceAssembly({interfaceVersion:'truss-reference-assembly/0.1.0',assemblyId:'packed-fixture',assemblyProfile:INERT_ASSEMBLY_PROFILE,recovery:{registryProfile:p,retention:'process_lifetime'},databaseIdentity:'uninstalled-fixture',schema:'truss',capabilities:[selection]},executor,{recoveryRegistry:{profile:p,retention:'process_lifetime',register:fail,append:fail,inspect:fail}});
if(result.status!=='ok')throw Error('Inert construction failed');
const assembly:ReferenceAssembly=result.value;
// The adapter's and public assembly's transaction parameter share one brand.
type Direct=Extract<ReturnType<ReferenceAssembly['directReads']>,{status:'ok'}>['capability'];
function useAdapterTransaction(transaction:TransactionHandle,request:Parameters<Direct['lookup']>[1]){const direct=assembly.directReads(selection);if(direct.status==='ok'){return direct.capability.lookup(transaction,request)}};
void useAdapterTransaction;
const readiness=await assembly.observeReadiness(selection);
if(readiness.status!=='ok'||readiness.value.state!=='unverified')throw Error('Fabricated readiness');
await assembly.dispose({});if(calls!==0)throw Error('Construction invoked host services');
console.log('Packed inert consumer passed; native calls='+calls);
