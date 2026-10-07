/** Exact candidate arithmetic witnesses only; no complete producer/allocator/native qualification. */
const candidate=await Bun.file('docs/helix/02-design/contracts/bindings/conformance-resource-v0.1.candidate.json').json();
function integer(value:unknown):bigint {if(typeof value!=='string'||!/^(0|[1-9][0-9]*)$/.test(value))throw Error('noncanonical count');return BigInt(value);}
const limits=candidate.limits;
const maximum=integer(limits.requiredCases),context=integer(limits.receiptContextBytes),entry=integer(limits.receiptPerRequiredCaseBytes),outcome=integer(limits.receiptPerCaseOutcomeBytes),ceiling=integer(limits.completeReceiptBytes);
function reservation(value:unknown):string {try{const count=integer(value);if(count===0n||count>maximum)return 'refused';const bytes=context+count*(entry+outcome);return bytes<=ceiling?bytes.toString():'refused';}catch{return 'refused';}}
const cases:[string,unknown,string][]=[['empty required manifest','0','refused'],['one case','1','1069056'],['maximum complete manifest','1000','21528576'],['one over required cases','1001','refused'],['leading zero alias','01','refused'],['rounded host number',1000,'refused'],['huge exact count','1000000000000000000000000000000000000000','refused']];
const failures=cases.filter(([,value,expected])=>reservation(value)!==expected).map(([name])=>name);
if(candidate.receiptReservation!=='receiptContextBytes_plus_requiredCases_times_sum_of_receiptPerRequiredCaseBytes_and_receiptPerCaseOutcomeBytes')failures.push('candidate formula changed');
console.log(JSON.stringify({scope:'conditional candidate required-entry/outcome receipt reservation arithmetic only',cases:cases.length,maximumReservationBytes:reservation('1000'),failures},null,2));if(failures.length)process.exit(1);export {};
