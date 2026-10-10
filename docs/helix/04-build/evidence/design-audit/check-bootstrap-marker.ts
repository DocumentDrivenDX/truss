/** Draft marker shape only; never establishes committed installation. */
import { readFileSync } from 'node:fs';
const modulePath = process.argv[2];
if (!modulePath) throw Error('Pass an installed Ajv Draft 2020-12 module path');
const { default: Ajv } = await import(modulePath);
const schema = JSON.parse(readFileSync(new URL('../../../02-design/contracts/bootstrap-marker-v0.1.schema.json', import.meta.url), 'utf8'));
const validate = new Ajv({ strict: true }).compile(schema);
const marker = {
  interfaceVersion: 'truss-bootstrap-marker/0.1.0', installationId: 'fixture-attempt',
  layoutVersion: 'fixture-only', bundleSha256: '0'.repeat(64),
  inventoryProfile: 'fixture-only', inventorySha256: '1'.repeat(64),
  namespace: {databaseIdentity: 'fixture-db', schemaName: 'truss'},
  installedAt: '2026-10-05T12:00:00Z',
};
const {inventorySha256: ignored, ...missingInventory} = marker;
const cases: readonly [string, unknown, boolean][] = [
  ['complete fixture', marker, true],
  ['missing inventory digest', missingInventory, false],
  ['numeric layout version', {...marker, layoutVersion: 2}, false],
  ['uppercase digest', {...marker, bundleSha256: 'A'.repeat(64)}, false],
  ['caller ready claim', {...marker, ready: true}, false],
  ['missing database identity', {...marker, namespace: {schemaName: 'truss'}}, false],
  ['unknown marker version', {...marker, interfaceVersion: 'truss-bootstrap-marker/2'}, false],
  ['syntactically valid forged digest', {...marker, inventorySha256: '2'.repeat(64)}, true],
];
const outcomes = cases.map(([name, input, expected]) => {
  const actual = Boolean(validate(input));
  if (actual !== expected) throw Error(name + ': unexpected schema verdict');
  return {name, expected, actual};
});
console.log(JSON.stringify({scope: 'Draft marker structure only; no digest, timestamp, namespace, inventory or commit qualification', cases: outcomes.length, outcomes}, null, 2));
