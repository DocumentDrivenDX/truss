/** Structural envelope examples; no native/history/owner qualification. */
import {readFileSync} from 'node:fs';
const modulePath = process.argv[2];
if (!modulePath) throw Error('Pass an installed Ajv Draft 2020-12 module path');
const {default: Ajv} = await import(modulePath);
const read = (name: string) => JSON.parse(readFileSync(new URL('../../../02-design/contracts/' + name, import.meta.url), 'utf8'));
const ajv = new Ajv({strict: true});
ajv.addSchema(read('exact-value-v0.1.schema.json'));
const validate = ajv.compile(read('history-record-v0.1.schema.json'));
const identity = {id: '9007199254740993', typeId: '1', definitionPin: 'fixture', owner: {documentId: 'doc', moduleId: 'module'}};
const base = {interfaceVersion: 'truss-history-record/0.1.0', identity, recordVersion: '1', catalogRevision: '2', createdAt: '2026-10-05T12:00:00Z', updatedAt: '2026-10-05T12:00:00Z', properties: [], retained: []};
const object = {...base, kind: 'object', ownership: {state: 'rootless'}};
const edge = {...base, kind: 'edge', source: identity, target: {...identity, id: '2'}, orderKey: {state: 'null'}};
const {target: ignored, ...missingTarget} = edge;
const property = {propertyId: '1', definitionPin: 'fixture', value: {kind: 'decimal', text: '1.00'}};
const cases: readonly [string, unknown, boolean][] = [
  ['rootless object', object, true],
  ['owned object', {...object, ownership: {state: 'owned', root: identity}}, true],
  ['complete edge', edge, true],
  ['edge missing endpoint', missingTarget, false],
  ['object with edge metadata', {...object, source: identity}, false],
  ['rounded host identity', {...object, identity: {...identity, id: 42}}, false],
  ['null order with stray text', {...edge, orderKey: {state: 'null', text: ''}}, false],
  ['exact property token', {...object, properties: [property]}, true],
  ['host numeric token', {...object, properties: [{...property, value: {kind: 'decimal', text: 1}}]}, false],
  ['duplicate property requires semantic rejection', {...object, properties: [property, property]}, true],
  ['unresolved owner requires semantic rejection', {...object, identity: {...identity, owner: {documentId: 'unknown', moduleId: 'unknown'}}}, true],
  ['invalid timestamp requires semantic rejection', {...object, createdAt: 'not-a-time'}, true],
];
const outcomes = cases.map(([name, input, expected]) => {
  const actual = Boolean(validate(input));
  if (actual !== expected) throw Error(name + ': unexpected shape verdict');
  return {name, expected, actual};
});
console.log(JSON.stringify({scope: 'Draft historical carrier shape only; no native owner/domain/time/uniqueness/history qualification', cases: outcomes.length, outcomes}, null, 2));
