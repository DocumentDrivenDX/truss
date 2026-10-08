/** Compile-only distinction; no import/receipt runtime evidence. */
import type {ImportInput} from './truss-import-input-v0.1';
import type {GroupSemanticInput,RequestIdentity} from './truss-group-input-v0.1';
declare const originalImport:ImportInput;
declare const receiptIdentity:RequestIdentity;
// @ts-expect-error Import load identity is not the group request-receipt identity API.
const receiptImport:ImportInput={...originalImport,requestIdentity:receiptIdentity};
// @ts-expect-error An import body is not a semantic atomic group request.
const group:GroupSemanticInput=originalImport;
void [receiptImport,group];
