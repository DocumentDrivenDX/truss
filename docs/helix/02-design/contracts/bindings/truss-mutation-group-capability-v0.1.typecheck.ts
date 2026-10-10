/** Design-only facade consumer; no runtime mutation/receipt qualification. */
import type {ReferenceAssembly} from './truss-reference-assembly-v0.1';
import type {CapabilitySelection} from './truss-capability-readiness-v0.1';
import type {TransactionHandle} from './truss-execution-v0.1';
import type {MutationSemanticInput, SingleMutationOperation, MutationApplicationResult} from './truss-mutation-capability-v0.1';
import type {GroupSemanticInput} from './truss-group-input-v0.1';
import type {GroupSemanticResult, GroupResponse} from './truss-group-result-v0.1';
import type {InTransactionGroupResponse} from './truss-group-capability-v0.1';
declare const assembly:ReferenceAssembly;
declare const mutationSelection:CapabilitySelection & {readonly family:'mutation'};
declare const groupSelection:CapabilitySelection & {readonly family:'group'};
declare const transaction:TransactionHandle;
declare const mutation:MutationSemanticInput;
declare const group:GroupSemanticInput;
declare const semantic:GroupSemanticResult;
const m=assembly.mutations(mutationSelection);
if(m.status==='ok')void m.capability.applyInTransaction(transaction,mutation);
const g=assembly.groups(groupSelection);
if(g.status==='ok')void g.capability.applyInTransaction(transaction,group,{state:'none'});
// @ts-expect-error Standalone update cannot resolve a group alias.
const alias:SingleMutationOperation={operation:'update_object',target:{state:'alias',alias:'created'},set:[],unset:[]};
// @ts-expect-error In-transaction applied group cannot claim committed.
const premature:InTransactionGroupResponse={disposition:'applied',durability:'committed',semantic};
// @ts-expect-error Same-transaction replay cannot claim committed durability.
const wrongReplay:GroupResponse={semantic,disposition:'replayed',durability:'committed',replay:{basis:'same_transaction',observationProfile:{identity:'fixture',version:'0.1.0',sha256:'digest'},evidence:{identity:'fixture',bytesBase64:'e30=',sha256:'digest'}}};
// @ts-expect-error Mutation failure cannot carry a successful operation result.
const mixed:MutationApplicationResult={outcome:'unavailable',reason:'resource',result:{operation:'update_object',outcome:'unchanged',identity:{id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'doc',moduleId:'module'}},version:'1',events:[]}};
void [alias,premature,wrongReplay,mixed];

import type {GroupCapability,RequestFreeGroupApplicationResult,GroupRequestSelection} from './truss-group-capability-v0.1';
import type {Outcome} from './truss-execution-v0.1';
declare const groupCapability:GroupCapability;
declare const requestSelection:GroupRequestSelection;
declare const requestFreeResult:RequestFreeGroupApplicationResult;
declare const replayResponse:Extract<InTransactionGroupResponse,{readonly disposition:'replayed'}>;
const requestFreeCall:Promise<Outcome<RequestFreeGroupApplicationResult>>=
  groupCapability.applyInTransaction(transaction,group,{state:'none'});
void groupCapability.applyInTransaction(transaction,group,requestSelection);
// @ts-expect-error Request-free success cannot be replayed.
const requestFreeReplay:RequestFreeGroupApplicationResult={outcome:'success',response:replayResponse};
// @ts-expect-error Request-free execution cannot expire a nonexistent receipt.
const requestFreeExpired:RequestFreeGroupApplicationResult={outcome:'unavailable',reason:'receipt_expired'};
// @ts-expect-error Request-free execution cannot require receipt observation.
const requestFreeReceipt:RequestFreeGroupApplicationResult={outcome:'unavailable',reason:'receipt'};
if(requestFreeResult.outcome==='failed') {
  // @ts-expect-error Request-free failure does not have a request conflict code.
  const conflict:'request_conflict'=requestFreeResult.failure.code;
  void conflict;
}
void [requestFreeCall,requestFreeReplay,requestFreeExpired,requestFreeReceipt];
