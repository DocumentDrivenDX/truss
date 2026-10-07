/** Design inspection only: no database snapshot or seed qualification. */
import {readFileSync} from 'node:fs';
const modulePath = process.argv[2];
if (!modulePath) throw Error('Pass installed Ajv Draft 2020-12 module path');
const {default: Ajv} = await import(modulePath);
const schema = JSON.parse(readFileSync(new URL('../../../02-design/contracts/seed-visibility-v0.1.schema.json', import.meta.url), 'utf8'));
const validate = new Ajv({strict: true}).compile(schema);
const artifact = {reference: 'fixture', sha256: '0'.repeat(64)};
const fixture = {interfaceVersion: 'truss-seed-visibility/0.1.0', seedId: 'seed', sourceEpoch: 'epoch', feedProfile: 'draft', scopeIdentity: 'fixture', catalogRevision: '1', snapshot: {xmin: '10', xmax: '20', inProgress: ['10', '14']}, baseline: artifact, procedure: artifact};
const cases: readonly [string, unknown, boolean][] = [
  ['complete fixture', fixture, true],
  ['numeric xid', {...fixture, snapshot: {...fixture.snapshot, xmin: 10}}, false],
  ['duplicate in-progress xid', {...fixture, snapshot: {...fixture.snapshot, inProgress: ['10', '10']}}, false],
  ['leading-zero xid', {...fixture, snapshot: {...fixture.snapshot, xmin: '010'}}, false],
  ['missing baseline', {...fixture, baseline: undefined}, false],
  ['well-shaped reversed range', {...fixture, snapshot: {xmin: '20', xmax: '10', inProgress: []}}, true],
  ['well-shaped out-of-range member', {...fixture, snapshot: {...fixture.snapshot, inProgress: ['21']}}, true],
  ['well-shaped overflowing xid8', {...fixture, snapshot: {...fixture.snapshot, xmax: '18446744073709551616'}}, true],
];
const shapes = cases.map(([name, input, expected]) => {
  const actual = Boolean(validate(input));
  if (actual !== expected) throw Error(name + ': unexpected structure verdict');
  return {name, expected, actual};
});
// Abstract expected vectors are independent of any production seed reducer.
const vectors: readonly [string, boolean][] = [['9', true], ['10', false], ['12', true], ['14', false], ['19', true], ['20', false], ['21', false]];
const xmin = 10n, xmax = 20n, active = new Set([10n, 14n]);
const classification = vectors.map(([xid, represented]) => {
  const actual = BigInt(xid) < xmax && !active.has(BigInt(xid));
  if (actual !== represented) throw Error('Abstract visibility mismatch');
  return {xid, represented, actual, requiresReplayRange: BigInt(xid) >= xmin};
});
console.log(JSON.stringify({scope: 'draft structure and abstract top-level committed-xid vectors only; no server observation, authority, digest, complete-envelope, snapshot or native qualification', shapes, classification}, null, 2));
