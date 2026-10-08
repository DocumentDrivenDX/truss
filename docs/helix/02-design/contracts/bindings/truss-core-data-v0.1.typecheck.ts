import type {ExactValue,NumericInput,ProfilePin,AuthoredValue} from './truss-core-data-v0.1';
// @ts-expect-error Transaction handles belong to the PostgreSQL execution surface.
import type {TransactionHandle} from './truss-core-data-v0.1';
// @ts-expect-error Core data exports do not expose host executor implementations.
import type {Executor} from './truss-core-data-v0.1';
const pin:ProfilePin={identity:'fixture',version:'1',sha256:'a'.repeat(64)};
const token:ExactValue={kind:'integer',text:'9007199254740993'};
const input:NumericInput=9007199254740993n;
const value:AuthoredValue={name:'count',value:token};
void [pin,input,value];
