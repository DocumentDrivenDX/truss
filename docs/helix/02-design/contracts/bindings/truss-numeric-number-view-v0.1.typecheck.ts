/** Compile-only public surface witness; no runtime conversion evidence. */
import {viewNumericAsNumber,type NumericNumberViewResult} from './truss-numeric-number-view-v0.1';
const result:NumericNumberViewResult=viewNumericAsNumber({decimalToken:'0.5'});
if(result.status==='lossless')void [result.view.original,result.view.value];
else void result.reason;
// @ts-expect-error Raw numbers are not exact read tokens.
viewNumericAsNumber(0.5);
// @ts-expect-error Conflicting numeric tags cannot choose a domain.
viewNumericAsNumber({integerToken:'1',decimalToken:'1.0'});
// @ts-expect-error Caller limits cannot enlarge the fixed standalone profile.
viewNumericAsNumber({integerToken:'42'},{work:Infinity});
// @ts-expect-error A refused result cannot discard its reason.
const incomplete:NumericNumberViewResult={status:'refused'};
void incomplete;
