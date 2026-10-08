import type {NumericAdmissionResult} from './truss-numeric-admission-v0.1';
const pin={identity:'fixture',version:'1',sha256:'a'.repeat(64)};
const admitted:NumericAdmissionResult={status:'admitted',field:{documentId:'d',moduleId:'m',fieldId:'f'},originalDocumentSha256:'a'.repeat(64),token:{decimalToken:'12.5'},origin:'number',value:{kind:'decimal',text:'12.5'}};
const refused:NumericAdmissionResult={status:'refused',code:'out_of_domain',diagnosticProfile:pin,diagnostics:{state:'available',artifact:{identity:'conversion-refusal-fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)}}};
// @ts-expect-error Pure admission does not certify a native committed transaction.
const committed:NumericAdmissionResult={...admitted,durability:'committed'};
// @ts-expect-error Refusal cannot publish a converted semantic value.
const partial:NumericAdmissionResult={...refused,value:{kind:'decimal',text:'0.1'}};
void [admitted,refused,committed,partial];

// @ts-expect-error Token family and exact semantic value family must agree.
const crossed:NumericAdmissionResult={status:'admitted',field:{documentId:'d',moduleId:'m',fieldId:'f'},originalDocumentSha256:'a'.repeat(64),token:{integerToken:'1'},origin:'exact_token',value:{kind:'decimal',text:'1'}};
void crossed;

// @ts-expect-error Refusal cannot silently omit diagnostic preservation state.
const omitted:NumericAdmissionResult={status:'refused',code:'resource',diagnosticProfile:pin};
// @ts-expect-error Available diagnostics require their exact original artifact.
const emptyDiagnostics:NumericAdmissionResult={status:'refused',code:'out_of_domain',diagnosticProfile:pin,diagnostics:{state:'available'}};
void [omitted,emptyDiagnostics];
