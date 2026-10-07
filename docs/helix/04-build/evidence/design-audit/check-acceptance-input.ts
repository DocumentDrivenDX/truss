/** Design-schema checks only; no UMF or native acceptance qualification. */
import {readFileSync} from 'node:fs';
const modulePath = process.argv[2];
if (!modulePath) throw Error('Pass an installed Ajv Draft 2020-12 module path');
const {default: Ajv} = await import(modulePath);
const schema = JSON.parse(readFileSync(new URL('../../../02-design/contracts/acceptance-input-v0.1.schema.json', import.meta.url), 'utf8'));
const validate = new Ajv({strict: true}).compile(schema);
const pin = {identity: 'fixture', version: 'draft', sha256: '0'.repeat(64)};
const artifact = {identity: 'fixture', bytesBase64: 'e30=', sha256: '0'.repeat(64)};
const document = {documentId: 'doc', documentRevision: 'revision', artifact, umfProfile: pin, ingress: {kind: 'native'}};
const input = {interfaceVersion: 'truss-acceptance-input/0.1.0', layoutProfile: pin,
  acceptanceProfile: pin, validatorProfile: pin, supportProfile: pin,
  documents: [document], binding: {state: 'absent'},
  policy: {unknownEndpoint: 'reject', loss: 'strict', profile: pin}, transforms: []};
const conversion = {kind: 'converted', adapterProfile: pin, source: artifact, lossReport: artifact};
const transform = {registration: pin, targetDefinitionIdentity: 'property', parameters: {integer: '9007199254740993'}};
const cases: readonly [string, unknown, boolean][] = [
  ['native fixture', input, true],
  ['complete conversion', {...input, documents: [{...document, ingress: conversion}]}, true],
  ['conversion missing source and losses', {...input, documents: [{...document, ingress: {kind: 'converted', adapterProfile: pin}}]}, false],
  ['empty import set', {...input, documents: []}, false],
  ['missing present binding artifact', {...input, binding: {state: 'present', vocabulary: pin}}, false],
  ['attempt origin excluded', {...input, assertedOrigin: {}}, false],
  ['exact text transform parameter', {...input, transforms: [transform]}, true],
  ['host number transform parameter', {...input, transforms: [{...transform, parameters: {integer: 42}}]}, false],
  ['unsupported policy', {...input, policy: {...input.policy, unknownEndpoint: 'invent'}}, false],
  ['forged digest remains structurally valid', {...input, documents: [{...document, artifact: {...artifact, sha256: '1'.repeat(64)}}]}, true],
  ['duplicate document identity requires semantic rejection', {...input, documents: [document, document]}, true],
  ['noncanonical base64 pad bits require semantic rejection', {...input, documents: [{...document, artifact: {...artifact, bytesBase64: 'Zh=='}}]}, true],
];
const outcomes = cases.map(([name, value, expected]) => {
  const actual = Boolean(validate(value));
  if (actual !== expected) throw Error(name + ': unexpected schema verdict');
  return {name, expected, actual};
});
console.log(JSON.stringify({scope: 'Draft input shape only; not digest, ordering, provenance, upstream validity, resource or authority validation', cases: outcomes.length, outcomes}, null, 2));
