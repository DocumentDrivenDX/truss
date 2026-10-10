/** Structural operation distinctions only; no history/manifest native proof. */
import {readFileSync} from 'node:fs';
const modulePath = process.argv[2];
if (!modulePath) throw Error('Pass an installed Ajv Draft 2020-12 module path');
const {default: Ajv} = await import(modulePath);
const read = (name: string) => JSON.parse(readFileSync(new URL('../../../02-design/contracts/' + name, import.meta.url), 'utf8'));
const ajv = new Ajv({strict: true});
ajv.addSchema(read('exact-value-v0.1.schema.json'));
ajv.addSchema(read('history-record-v0.1.schema.json'));
const validate = ajv.compile(read('history-event-v0.1.schema.json'));
const identity = {id: '1', typeId: '1', definitionPin: 'fixture', owner: {documentId: 'doc', moduleId: 'module'}};
const record = {interfaceVersion: 'truss-history-record/0.1.0', identity, recordVersion: '1', catalogRevision: '1', createdAt: 'fixture', updatedAt: 'fixture', properties: [], retained: [], kind: 'object', ownership: {state: 'rootless'}};
const base = {interfaceVersion: 'truss-history-event/0.1.0', sourceEpoch: 'fixture', historyProfile: 'draft', xid: '1', seq: '1', identity, eventVersion: '2', eventCatalogRevision: '1', mutationGroup: {profile: 'truss-history-group/0.1.0', eventCount: '1', orderedEventDigest: '0'.repeat(64)}, origin: {asserted: {kind: 'null'}, databaseRole: 'fixture'}};
const absent = {present: false};
const present = {present: true, value: {kind: 'decimal', text: '1.00'}};
const property = {...base, operation: 'property', propertyId: '1', definitionPin: 'fixture', before: absent, after: present};
const rebind = {...base, operation: 'rebind', retainedName: 'authored', propertyId: '1', beforeDefinitionContext: 'fixture', afterDefinitionPin: 'fixture', retainedBefore: present, retainedAfter: absent, propertyBefore: absent, propertyAfter: present};
const {propertyBefore: ignored, ...missingHome} = rebind;
const cases: readonly [string, unknown, boolean][] = [
  ['create', {...base, operation: 'create', after: record}, true],
  ['delete', {...base, operation: 'delete', before: record}, true],
  ['property presence', property, true],
  ['transform pins', {...base, operation: 'transform', propertyId: '1', beforeDefinitionPin: 'old', afterDefinitionPin: 'new', before: present, after: present}, true],
  ['rebind four homes', rebind, true],
  ['metadata envelopes', {...base, operation: 'metadata', before: record, after: record}, true],
  ['create missing full record', {...base, operation: 'create'}, false],
  ['rebind missing home', missingHome, false],
  ['absent with stray value', {...property, before: {...absent, value: {kind: 'null'}}}, false],
  ['empty group', {...property, mutationGroup: {...base.mutationGroup, eventCount: '0'}}, false],
  ['unknown operation', {...base, operation: 'guess'}, false],
  ['forged manifest needs semantic rejection', {...property, mutationGroup: {...base.mutationGroup, eventCount: '9'}}, true],
];
const outcomes = cases.map(([name, input, expected]) => {
  const actual = Boolean(validate(input));
  if (actual !== expected) throw Error(name + ': unexpected shape verdict');
  return {name, expected, actual};
});
console.log(JSON.stringify({scope: 'Draft operation shape only; no identity/owner/definition/group/continuity/native qualification', cases: outcomes.length, outcomes}, null, 2));
