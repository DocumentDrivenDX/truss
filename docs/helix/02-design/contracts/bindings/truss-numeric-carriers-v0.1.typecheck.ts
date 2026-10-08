import type {NumericInput,NumericReadValue,LosslessNumericNumberView} from './truss-numeric-carriers-v0.1';
const safe:NumericInput=12.5;
const big:NumericInput=9007199254740993n;
const token:NumericReadValue={decimalToken:'1.00'};
const view:LosslessNumericNumberView={original:token,value:1};
// @ts-expect-error Default read cannot replace its exact token with a number.
const lossyRead:NumericReadValue=0.1;
// @ts-expect-error A number view cannot discard original token custody.
const missingOriginal:LosslessNumericNumberView={value:1};
// @ts-expect-error One numeric leaf cannot carry conflicting integer and decimal tags.
const ambiguous:NumericInput={integerToken:'1',decimalToken:'1.0'};
// @ts-expect-error Explicit float domains do not inherit this integer/decimal profile.
const float:NumericInput={floatToken:'0.1'};
void [safe,big,token,view,lossyRead,missingOriginal,ambiguous,float];
