import type {HistoricalEvent} from './truss-history-v0.1';
import type {HistoryRetainPayloadProposal,RetainedAddition} from './truss-history-retain-payload-v0.1.proposal';
import type {ProposedEventContext,ProposedHistoricalEvent} from './truss-history-v0.2.proposal';
declare const context: ProposedEventContext;
declare const member: RetainedAddition;
declare const old: HistoricalEvent;
declare const payload: HistoryRetainPayloadProposal;
const retained: ProposedHistoricalEvent = {...context,operation:'retain',retainedChanges:[member]};
const multiple: ProposedHistoricalEvent = {...retained,retainedChanges:[member,member]};
const priorVariant: ProposedHistoricalEvent = {...old,interfaceVersion:'truss-history-event/0.2.0-proposal'};
// @ts-expect-error The old event version is not silently upgraded.
const oldIntoNew: ProposedHistoricalEvent = old;
// @ts-expect-error The new event version is not accepted by old consumers.
const newIntoOld: HistoricalEvent = retained;
// @ts-expect-error Standalone payload has no complete custody context.
const payloadIntoEvent: ProposedHistoricalEvent = payload;
// @ts-expect-error Retained inventory must be nonempty.
const empty: ProposedHistoricalEvent = {...retained,retainedChanges:[]};
// @ts-expect-error Property shape must keep its property-specific members.
const missingProperty: ProposedHistoricalEvent = {...context,operation:'property'};
// @ts-expect-error Metadata retains complete before and after images.
const missingMetadata: ProposedHistoricalEvent = {...context,operation:'metadata'};
// @ts-expect-error No removal meaning is introduced by the new envelope.
const removal: ProposedHistoricalEvent = {...retained,retainedChanges:[{...member,after:{present:false}}]};
function narrow(event:ProposedHistoricalEvent){
 if(event.operation==='retain') return event.retainedChanges[0].sourceContext;
 if(event.operation==='property') return event.propertyId;
 if(event.operation==='metadata') return event.after.recordVersion;
 return event.identity.definitionPin;
}
void [multiple,priorVariant,oldIntoNew,newIntoOld,payloadIntoEvent,empty,missingProperty,missingMetadata,removal,narrow];
