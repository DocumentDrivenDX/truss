import type {ReceiptVisibilityResult,ReceiptVisibilityRequest} from './truss-receipt-visibility-v0.1.proposal';
const result:ReceiptVisibilityResult={interfaceVersion:'truss-receipt-visibility-result/0.1.0',outcome:'unavailable',reason:'observation_integrity'};
// @ts-expect-error Unavailable evidence cannot carry a false inclusion answer.
const falseUnavailable:ReceiptVisibilityResult={...result,included:false};
const request:ReceiptVisibilityRequest={interfaceVersion:'truss-receipt-visibility-request/0.1.0',token:'opaque',limits:{tokenBytes:'16384',evidenceBytes:'1024',retainedBytes:'2048',workUnits:'1000',nativeStatements:'4'}};
// @ts-expect-error Limits never pass through JavaScript numbers.
const rounded:ReceiptVisibilityRequest={...request,limits:{...request.limits,workUnits:1000}};
void falseUnavailable;void rounded;
