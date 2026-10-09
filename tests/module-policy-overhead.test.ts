import {test,expect} from 'bun:test';
import {assessModulePolicyTimings} from '../packages/tooling/src/module-policy-overhead';
const blocks=()=>Array.from({length:3},()=>Array.from({length:1000},()=>({baselineNanoseconds:'10000000000000000',policyNanoseconds:'10000000000010000'})));
test('exact threshold passes every original block without float conversion',()=>{
 expect(assessModulePolicyTimings(blocks())).toEqual({outcome:'pass',scope:'timing_only',blockDifferencesNanoseconds:['10000000','10000000','10000000']});
});
test('one nanosecond over fails even with a passing pooled mean',()=>{
 const input=blocks();input[0]![0]!.policyNanoseconds='10000000000010001';
 input[1]![0]!.policyNanoseconds='10000000000009999';
 expect(assessModulePolicyTimings(input)).toMatchObject({outcome:'fail',blockDifferencesNanoseconds:['10000001','9999999','10000000']});
});
test('negative differences are retained and results frozen',()=>{
 const input=blocks();for(const block of input)for(const pair of block)pair.policyNanoseconds='9999999999999999';
 const result=assessModulePolicyTimings(input);
 expect(result).toEqual({outcome:'pass',scope:'timing_only',blockDifferencesNanoseconds:['-1000','-1000','-1000']});
 expect(Object.isFrozen(result)).toBe(true);
 if(result.outcome!=='invalid')expect(Object.isFrozen(result.blockDifferencesNanoseconds)).toBe(true);
});
test('missing samples, extra fields and invalid exact durations invalidate',()=>{
 const missing=blocks();missing[0]!.pop();expect(assessModulePolicyTimings(missing).outcome).toBe('invalid');
 expect(assessModulePolicyTimings(blocks().slice(1)).outcome).toBe('invalid');
 for(const invalid of [1,true,null,'01','-1','1.0','1e3','1'.repeat(21),'NaN']){
  const input:any=blocks();input[0][0].policyNanoseconds=invalid;
  expect(assessModulePolicyTimings(input).outcome).toBe('invalid');
 }
 const extra:any=blocks();extra[0][0].correct=true;
 expect(assessModulePolicyTimings(extra).outcome).toBe('invalid');
});
