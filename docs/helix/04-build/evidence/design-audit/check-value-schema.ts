/** Design schema structure only; not semantic/native conformance. */
import { readFileSync } from 'node:fs';
const modulePath = process.argv[2];
if (!modulePath) throw Error('Pass an installed Ajv Draft 2020-12 module path');
const { default: Ajv } = await import(modulePath);
const schema = JSON.parse(readFileSync(new URL('../../../02-design/contracts/exact-value-v0.1.schema.json', import.meta.url), 'utf8'));
const validate = new Ajv({ strict: true }).compile(schema);
const cases: readonly [string, unknown, boolean][] = [
  ['absence', {present:false}, true],
  ['present null', {present:true,value:{kind:'null'}}, true],
  ['lexical decimal', {present:true,value:{kind:'decimal',text:'1.00'}}, true],
  ['nested exact values', {present:true,value:{kind:'sequence',items:[{kind:'integer',text:'9007199254740993'},{kind:'string',text:'1.00'}]}}, true],
  ['empty map', {present:true,value:{kind:'map',entries:[]}}, true],
  ['record descriptor', {present:true,value:{kind:'record',definitionPin:'pin-1',fields:[{fieldId:'f',value:{kind:'boolean',value:true}}]}}, true],
  ['opaque source', {present:true,value:{kind:'opaque',format:'json',sourceText:'1.00',sha256:'0'.repeat(64)}}, true],
  ['missing present value', {present:true}, false],
  ['value on absence', {present:false,value:{kind:'null'}}, false],
  ['host decimal number', {present:true,value:{kind:'decimal',text:1}}, false],
  ['unknown selected tag', {present:true,value:{kind:'unknown',text:'x'}}, false],
  ['unexpected member', {present:true,value:{kind:'null',text:'null'}}, false],
  ['map missing key', {present:true,value:{kind:'map',entries:[{value:{kind:'null'}}]}}, false],
  ['record missing pin', {present:true,value:{kind:'record',fields:[]}}, false],
  ['opaque malformed digest', {present:true,value:{kind:'opaque',format:'json',sourceText:'1',sha256:'ABC'}}, false],
];
const outcomes = cases.map(([name,input,expected]) => {
  const actual = Boolean(validate(input));
  if (actual !== expected) throw Error(name + ': unexpected schema verdict');
  return {name, expected, actual};
});
console.log(JSON.stringify({scope:'Draft 2020-12 structure only; no token/domain/digest/bounds/native qualification', cases:outcomes.length, outcomes}, null, 2));
