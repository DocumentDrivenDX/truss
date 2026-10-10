/** Pure protocol0.1.0 timing adjudication; no native/profile/correctness authority. */
export interface PolicyTimingPair {
 readonly baselineNanoseconds:string;
 readonly policyNanoseconds:string;
}
export type PolicyTimingAssessment = Readonly<{
 outcome:'pass'|'fail';scope:'timing_only';blockDifferencesNanoseconds:readonly string[];
}> | Readonly<{outcome:'invalid';scope:'timing_only'}>;
const invalid=():PolicyTimingAssessment=>Object.freeze({outcome:'invalid',scope:'timing_only'});
function duration(value:unknown):bigint {
 if(typeof value!=='string'||!(/^(0|[1-9][0-9]{0,19})$/).test(value))throw Error('invalid duration');
 return BigInt(value);
}
/** Input order is retained. Caller must independently admit original registration,
 * complete correctness and raw arm/sample custody before using this assessment.
 * This numeric function cannot recognize copied/reordered/misclassified samples. */
export function assessModulePolicyTimings(blocks:unknown):PolicyTimingAssessment {
 try{
  if(!Array.isArray(blocks)||blocks.length!==3)return invalid();
  const sums:bigint[]=[];
  for(const block of blocks){
   if(!Array.isArray(block)||block.length!==1000)return invalid();
   let sum=0n;
   for(const sample of block){
    if(!sample||typeof sample!=='object'||Array.isArray(sample))return invalid();
    const keys=Object.keys(sample);
    if(keys.length!==2||!keys.includes('baselineNanoseconds')||!keys.includes('policyNanoseconds'))return invalid();
    sum+=duration(sample.policyNanoseconds)-duration(sample.baselineNanoseconds);
   }
   sums.push(sum);
  }
  return Object.freeze({outcome:sums.every(sum=>sum<=10000000n)?'pass':'fail',scope:'timing_only',
   blockDifferencesNanoseconds:Object.freeze(sums.map(String))});
 }catch{return invalid()}
}
