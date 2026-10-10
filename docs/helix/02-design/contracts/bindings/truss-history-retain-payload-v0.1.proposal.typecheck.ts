import type {RetainedAddition, HistoryRetainPayloadProposal} from './truss-history-retain-payload-v0.1.proposal';
import type {HistoricalEvent} from './truss-history-v0.1';
const member: RetainedAddition = {retainedName:'literal/name',before:{present:false},after:{present:true,value:{kind:'null'}},beforeDefinitionContext:'old',afterDefinitionContext:'new',sourceContext:'source'};
const payload: HistoryRetainPayloadProposal = {interfaceVersion:'truss-history-retain-payload/0.1.0',operation:'retain',retainedChanges:[member]};
const multiple: HistoryRetainPayloadProposal = {...payload,retainedChanges:[member,{...member,retainedName:'other'}]};
// @ts-expect-error Empty inventory is not an addition payload.
const empty: HistoryRetainPayloadProposal = {...payload,retainedChanges:[]};
// @ts-expect-error Replacement is outside addition semantics.
const replacement: RetainedAddition = {...member,before:{present:true,value:{kind:'null'}}};
// @ts-expect-error Removal is outside addition semantics.
const removal: RetainedAddition = {...member,after:{present:false}};
// @ts-expect-error Present requires a value, including explicit null.
const missingValue: RetainedAddition = {...member,after:{present:true}};
// @ts-expect-error Absent before cannot carry a stray value.
const strayValue: RetainedAddition = {...member,before:{present:false,value:{kind:'null'}}};
// @ts-expect-error Payload is not an event in the unchanged historical-event union.
const event: HistoricalEvent = payload;
void [multiple,empty,replacement,removal,missingValue,strayValue,event];
