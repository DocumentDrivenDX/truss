/** Closed definition serialization only; no artifact custody or native/compiler qualification. */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
if (process.argv.length !== 3) throw Error('usage: bun check-reference-row-definition-shapes.cjs /absolute/path/to/ajv/dist/2020.js');
const Ajv = require(process.argv[2]).default;
const root = path.resolve(__dirname, '../../../02-design/contracts');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const pin = {identity:'shape-only',version:'0',sha256:'0'.repeat(64)};
const artifact = {identity:'shape-only',bytesBase64:'AA==',sha256:'0'.repeat(64)};
const presence = {
 interfaceVersion:'truss-row-home-presence/0.1.0',profile:pin,
 carrierSchema:'urn:truss:draft:exact-value:0.1.0#/$defs/presence',
 storageHome:'row_home_state/row_home_node/row_home_scalar',
 absent:'zero-owned-states-after-complete-authorized-applicability',
 presentNull:'one-owned-state-null-root-no-payload',
 presentScalar:'one-owned-state-scalar-root-one-qualified-payload',
 duplicateState:'complete-result-refusal',extraNodeOrPayload:'complete-result-refusal',
 incompleteVisibility:'unavailable-not-absence',sqlNullPayload:'integrity-refusal-not-logical-null',
 readDefault:'none',acceptedDefinition:artifact,physicalProfile:pin,physicalDefinition:artifact,
 authorityProfile:pin,authorityDefinition:artifact,valueDefinition:artifact,nullAdmission:'refuse'
};
const common = {
 interfaceVersion:'truss-reference-row-scalar-codec/0.1.0',storageHome:'row_home_scalar',
 coercion:'none',readDefault:'none',unusedPayloadSlots:'native-null',
 invalidStoredValue:'complete-result-refusal',workAdmission:'original-enclosing-account-before-scan-copy-conversion',
 profile:pin,nativeDomainProfile:pin,sourceInterpretationProfile:pin,resourceProfile:pin,
 authoredDefinition:artifact,nativeDomainDefinition:artifact,sourceInterpretationDefinition:artifact,
 resourceDefinition:artifact,presenceDefinition:artifact
};
const string = {...common,rule:{family:'string',payloadColumn:'text_value',encoding:'preserve-unicode-scalars',
 unpairedSurrogate:'refuse-before-utf8',nul:'unsupported-native-realization',emptyText:'admit',normalization:'none'}};
const decimal = {...common,rule:{family:'decimal',tokenColumn:'numeric_token',projectionColumn:'numeric_value',
 precision:'21',scale:'3',lexicalGrammar:'complete-ascii-json-number-token',sourceSpelling:'preserve-exact-token',
 coefficient:'existing-pinned-umf-schemaCoefficient',zeroExponent:'zero-before-nonzero-exponent-bound',
 projection:'bounded-coefficient-fixed-scale-three',projectionInputMaxBytes:'23',nonfinite:'refuse',
 rounding:'refuse',agreement:'exact-coefficient-divided-by-1000'}};
const omit = (obj,key) => Object.fromEntries(Object.entries(obj).filter(([k]) => k !== key));
const suites = [
 ['truss-row-home-presence-v0.1.proposal.schema.json','reference-row-presence-shapes.json',[
  ['required-null-refusal',presence,true],
  ['explicit-null-candidate',{...presence,nullAdmission:'explicit-null-under-original-definition'},true],
  ['props-root-substitution',{...presence,storageHome:'nonnull-jsonb-object'},false],
  ['missing-authority',omit(presence,'authorityDefinition'),false],
  ['sql-null-is-null-substitution',{...presence,sqlNullPayload:'logical-null'},false],
  ['unknown-rule',{...presence,defaultValue:''},false]]],
 ['truss-reference-row-scalar-codec-v0.1.proposal.schema.json','reference-row-scalar-codec-shapes.json',[
  ['string',string,true],['decimal21-3',decimal,true],
  ['domain-narrowing',{...decimal,rule:{...decimal.rule,precision:'28',scale:'2'}},false],
  ['rounding',{...decimal,rule:{...decimal.rule,rounding:'allow'}},false],
  ['null-string',{...string,rule:{...string.rule,encoding:'null-or-string'}},false],
  ['missing-resource',omit(decimal,'resourceDefinition'),false]]]
];
for (const [schemaFile,receiptFile,cases] of suites) {
 const ajv = new Ajv({strict:true});
 ajv.addSchema(JSON.parse(fs.readFileSync(path.join(root,'acceptance-input-v0.1.schema.json'))));
 const raw = fs.readFileSync(path.join(root,schemaFile));
 const validate = ajv.compile(JSON.parse(raw));
 const retained = JSON.parse(fs.readFileSync(path.join(__dirname,receiptFile)));
 if (hash(raw) !== retained.schemaSha256) throw Error('schema pin mismatch: '+schemaFile);
 const observed = cases.map(([name,input,expected]) => {
  if (validate(input) !== expected) throw Error(name+': '+JSON.stringify(validate.errors));
  return {name,expected,passed:true};
 });
 if (JSON.stringify(observed) !== JSON.stringify(retained.cases)) throw Error('probe receipt mismatch');
}
console.log('Twelve original row-home definition shape probes reproduced; semantic/native qualification remains open.');
