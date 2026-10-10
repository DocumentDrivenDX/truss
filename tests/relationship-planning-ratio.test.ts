import {test,expect} from 'bun:test';
import {checkRelationshipPlanningRatio as ratio} from '../packages/tooling/src/relationship-planning-ratio';
const samples=(value:string)=>Array(1000).fill(value) as string[];
test('two-times threshold is inclusive and one exact unit above fails',()=>{
 expect(ratio(samples('9007199254740993'),samples('18014398509481986'),'1')).toBe('within_target');
 expect(ratio(samples('9007199254740993'),samples('18014398509481987'),'1')).toBe('above_target');
});
test('nearest-rank p95 uses the 950th ordered value without mutating samples',()=>{
 const candidate=[...Array(50).fill('999'),...Array(950).fill('200')];
 expect(ratio(samples('100'),candidate,'1')).toBe('within_target');
 expect(candidate[0]).toBe('999');
 expect(ratio(samples('100'),[...Array(51).fill('999'),...Array(949).fill('200')],'1')).toBe('above_target');
});
test('missing, incomparable and below-resolution baselines cannot pass',()=>{
 expect(ratio(samples('100').slice(1),samples('100'),'1')).toBe('invalid_samples');
 expect(ratio(samples('0'),samples('0'),'1')).toBe('invalid_samples');
 expect(ratio(samples('1'),samples('1'),'1')).toBe('invalid_samples');
 expect(ratio(samples('100'),samples('1.0'),'1')).toBe('invalid_samples');
 expect(ratio(samples('100'),samples('100'),'0')).toBe('invalid_samples');
});
test('sparse arrays refuse instead of skipping missing observations',()=>{
 expect(ratio(new Array<string>(1000),samples('100'),'1')).toBe('invalid_samples');
 const candidate=samples('100');delete candidate[999];
 expect(ratio(samples('100'),candidate,'1')).toBe('invalid_samples');
});
