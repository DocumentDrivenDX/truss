/** Exact reference-profile capacity arithmetic only; no allocation/producer evidence. */
const profile=await Bun.file('docs/helix/02-design/contracts/bindings/import-resource-v0.1.candidate.json').json();
const l=profile.limits;const failures:string[]=[];
function reserve(count:string):bigint|null{
 if(!/^(0|[1-9][0-9]*)$/.test(count))return null;const n=BigInt(count);
 if(n>BigInt(l.inputRecords))return null;
 const bytes=BigInt(l.reportContextBytes)+n*(BigInt(l.reportOutcomeBytes)+BigInt(l.reportBatchBytes)+BigInt(l.unprocessedIndexBytes));
 return bytes<=BigInt(l.reportBytes)?bytes:null;
}
const cases:[string,string,bigint|null][]=[['empty','0',1048576n],['one','1',1060872n],['maximum','1000',13344576n],['input maximum independent of report capacity','1001',null],['no count alias','010',null],['host-sized extreme refuses before multiplication','9223372036854775807',null]];
for(const [name,count,want] of cases)if(reserve(count)!==want)failures.push(name);
console.log(JSON.stringify({scope:'reference profile exact reservation arithmetic, not producer/physical feasibility',cases:cases.length,failures},null,2));if(failures.length)process.exit(1);export {};
