import {expect, test} from 'bun:test';
import {checkAdmittedConformanceObservationCoverage as covers,
  type ConformanceObservationKey as Key} from '../packages/tooling/src/conformance-observation-coverage';

const required: Key[] = [
  {surface:'result',step:'write',boundary:'pending'},
  {surface:'state',step:'write',boundary:'committed'},
  {surface:'journal',step:'write',boundary:'committed'},
  {surface:'report',step:'write',boundary:'committed'},
];
test('complete coverage permits ordering differences', () => {
  expect(covers(required, [...required].reverse())).toBe(true);
});
test('empty expectations do not prove an empty native inventory', () => {
  expect(covers(required, [])).toBe(false);
  expect(covers(required, required.slice(0, 3))).toBe(false);
});
test('extra observations and duplicates cannot replace required checks', () => {
  expect(covers(required, [...required, {...required[0],step:'other'}])).toBe(false);
  expect(covers(required, [...required, required[0]])).toBe(false);
  expect(covers([...required, required[0]], required)).toBe(false);
});
test('surface, step and boundary all participate in coverage', () => {
  for (const replacement of [
    {...required[3],surface:'state' as const},
    {...required[3],step:'other'},
    {...required[3],boundary:'pending'},
  ]) expect(covers(required, [...required.slice(0,3),replacement])).toBe(false);
});
test('explicitly admitted no-observation procedure has empty coverage', () => {
  expect(covers([], [])).toBe(true);
  expect(covers([], [required[0]])).toBe(false);
});

test('performance evidence cannot be omitted or replaced by behavioral evidence', () => {
  const performance: Key = {surface:'performance',step:'read',boundary:'committed'};
  const benchmark = [...required, performance];
  expect(covers(benchmark, [...benchmark].reverse())).toBe(true);
  expect(covers(benchmark, required)).toBe(false);
  expect(covers(benchmark, [...required, {...performance,surface:'result'}])).toBe(false);
  expect(covers(benchmark, [...required, {...performance,boundary:'pending'}])).toBe(false);
  expect(covers(benchmark, [...benchmark,performance])).toBe(false);
  expect(covers(required, benchmark)).toBe(false);
});
