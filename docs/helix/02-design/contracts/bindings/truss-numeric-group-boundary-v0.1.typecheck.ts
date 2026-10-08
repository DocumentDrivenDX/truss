/** Compile-only adapter seam; supplied exact tokens are fixtures, not conversion/admission proof. */
import type {ExactIntegerToken,ExactDecimalToken} from './truss-numeric-carriers-v0.1';
import type {AuthoredValue} from './truss-group-input-v0.1';
const integer:ExactIntegerToken={integerToken:'9007199254740993'};
const decimal:ExactDecimalToken={decimalToken:'1.00'};
const values:readonly AuthoredValue[]=[
 {name:'count',value:{kind:'integer',text:integer.integerToken}},
 {name:'amount',value:{kind:'decimal',text:decimal.decimalToken}}
];
// @ts-expect-error Semantic group values cannot contain a raw JS number.
const rawNumber:AuthoredValue={name:'amount',value:0.1};
// @ts-expect-error Bigint must cross the exact typed-value text boundary before transport.
const rawBigint:AuthoredValue={name:'count',value:9007199254740993n};
// @ts-expect-error UMF-compatible convenience wrappers are not the semantic group wire carrier.
const unmappedToken:AuthoredValue={name:'amount',value:decimal};
void [values,rawNumber,rawBigint,unmappedToken];
