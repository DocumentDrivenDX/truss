import type {DirectPageRequest, DirectPage, DirectReadContext, DirectLookupResult} from './truss-direct-read-v0.1';
declare const request: DirectPageRequest;
declare const page: DirectPage;
// @ts-expect-error Page limits use exact integer text.
const roundedLimit: DirectPageRequest = {...request, limit: 100};
// @ts-expect-error Snapshot consistency requires a registered handle identity.
const missingSnapshot: DirectReadContext['consistency'] = {kind: 'held_snapshot'};
// @ts-expect-error End of a page has no continuation cursor.
const falseEnd: DirectPage = {...page, continuation: {state: 'end', cursor: {}}};
void [roundedLimit, missingSnapshot, falseEnd];
// @ts-expect-error Not-found cannot reveal a hidden record.
const hiddenRecord: DirectLookupResult = {outcome: 'not_found', record: page.records[0]};
// @ts-expect-error Found result requires exact context and record.
const emptyFound: DirectLookupResult = {outcome: 'found'};
void [hiddenRecord, emptyFound];
