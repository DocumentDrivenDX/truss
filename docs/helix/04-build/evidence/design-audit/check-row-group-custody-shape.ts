/** Shape controls only: neither original artifact hashes nor native authority are established. */
const {default: Ajv} = await import(process.argv[2]);
const output = process.argv[3];
if (!output || await Bun.file(output).exists()) throw Error('fresh receipt path required');
const ajv = new Ajv({strict:true});
const sources:any[]=[];
for (const name of [...new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts')].sort()) {
  const raw=await Bun.file('docs/helix/02-design/contracts/'+name).text();
  const schema=JSON.parse(raw); ajv.addSchema(schema);
  sources.push({name,id:schema.$id,sha256:new Bun.CryptoHasher('sha256').update(raw).digest('hex')});
}
const validate=ajv.getSchema('urn:truss:proposal:row-group-custody:0.1.0')!;
const base={interfaceVersion:'truss-row-group-custody/0.1.0',profile:{identity:'fixture',version:'0.1',sha256:'0'.repeat(64)},addressDomain:'truss-row-operation-address/0.1.0',operationIdentity:'["truss-row-operation-address/0.1.0","fixture","123","7"]',operationKind:'create',originalGroupAdmission:{identity:'fixture-family',bytesBase64:'e30=',sha256:'0'.repeat(64)},authority:'actual-original-operation-admission-not-caller-address',completionEvidence:'resolved-independently-not-embedded-future-digest'};
// Use the existing operation-kind vocabulary rather than inventing a new family.
const custody=ajv.getSchema('urn:truss:draft:row-operation-custody:0.1.0')!.schema as any;
base.operationKind=custody.properties.operations.items.properties.operationKind.enum[0];
const checks:any[]=[];
function check(name:string,change:(v:any)=>void,expected:boolean){const value=structuredClone(base);change(value);const observed=!!validate(value);checks.push({name,expected,observed});if(observed!==expected)throw Error(name);}
check('complete-shape',()=>{},true);
check('missing-address',v=>delete v.operationIdentity,false);
check('numeric-address',v=>v.operationIdentity=123,false);
check('unknown-kind',v=>v.operationKind='unknown',false);
check('extra-field',v=>v.extra=true,false);
check('future-seal',v=>v.finalizationDigest='0'.repeat(64),false);
check('wrong-address-domain',v=>v.addressDomain='other',false);
check('missing-family-artifact',v=>delete v.originalGroupAdmission,false);
check('open-family-artifact',v=>v.originalGroupAdmission.extra=true,false);
check('missing-profile-pin',v=>delete v.profile.sha256,false);
check('empty-family-bytes-shape-does-not-prove-admission',v=>v.originalGroupAdmission.bytesBase64='',true);
check('noncanonical-address-shape-needs-original-codec',v=>v.operationIdentity='unresolved',true);
await Bun.write(output,JSON.stringify({checkedAt:new Date().toISOString(),bunVersion:Bun.version,scope:'closed schema shape only; no artifact hash correspondence, native scope, admission or completion qualification',checks,sources},null,2)+'\n');
console.log(JSON.stringify({checks:checks.length,passed:true}));
export {};
