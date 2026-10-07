import type {OperationResult} from './truss-group-result-v0.1';
const identity = {id: '1', typeId: '2', definitionPin: 'fixture', owner: {documentId: 'doc', moduleId: 'm'}};
const event = {sourceEpoch: 'epoch', historyProfile: 'draft', xid: '3', seq: '4'};
const noOp: OperationResult = {operation: 'update_object', outcome: 'unchanged', identity, version: '5', events: []};
// @ts-expect-error An unchanged result cannot claim a change event.
const falseEvent: OperationResult = {operation: 'update_object', outcome: 'unchanged', identity, version: '5', events: [event]};
// @ts-expect-error Changed result needs event evidence.
const missingEvent: OperationResult = {operation: 'update_object', outcome: 'changed', identity, version: '6', events: []};
// @ts-expect-error Exact result versions are text.
const rounded: OperationResult = {operation: 'update_object', outcome: 'unchanged', identity, version: 5, events: []};
void [noOp, falseEvent, missingEvent, rounded];
