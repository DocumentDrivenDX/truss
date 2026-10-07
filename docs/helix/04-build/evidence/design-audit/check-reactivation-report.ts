/** Proposal fragment controls; no native range, custody or lifecycle proof. */
const {default:Ajv}=await import(process.argv[2]);
const ajv=new Ajv({strict:true});
for(const f of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))
  ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+f).json());
const id='urn:truss:draft:reactivation-acceptance-report:0.2.0';
const validate=ajv.getSchema(id+'#/properties/reactivations')!;
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const entry={identity:{kind:'key',typeId:'-2147483648',keyNumber:'-32768'},owner:{documentId:'d',moduleId:'m'},lineage:artifact,beforeRetiredRevision:'-1',beforeDefinition:artifact,afterDefinition:artifact};
const cases:[string,unknown,boolean][]=[
  ['owner-local signed key',[entry],true],
  ['same number distinct owner type',[entry,{...entry,identity:{...entry.identity,typeId:'2'}}],true],
  ['missing type owner',[{...entry,identity:{kind:'key',keyNumber:'1'}}],false],
  ['global key id substitution',[{...entry,identity:{kind:'key',keyId:'k'}}],false],
  ['unknown identity kind',[{...entry,identity:{kind:'endpoint',relationshipId:'1'}}],false],
  ['host-number identity',[{...entry,identity:{kind:'type',typeId:1}}],false],
  ['noncanonical signed identity',[{...entry,identity:{kind:'type',typeId:'-0'}}],false],
  ['missing original before source',[Object.fromEntries(Object.entries(entry).filter(([k])=>k!=='beforeDefinition'))],false],
  ['duplicate transitions require semantic rejection',[entry,entry],true],
  ['overflow requires semantic rejection',[{...entry,identity:{kind:'key',typeId:'2147483648',keyNumber:'32768'}}],true],
];
const failures=cases.filter(([,v,want])=>Boolean(validate(v))!==want).map(([name])=>name);
const oldVersion=ajv.getSchema('urn:truss:draft:acceptance-report:0.1.0#/properties/interfaceVersion')!;
if(oldVersion('truss-acceptance-report/0.2.0'))failures.push('old version accepted new version');
const receipt={scope:'reactivation proposal fragment shapes and old-version discriminator only',cases:cases.length+1,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/reactivation-report-shapes.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify(receipt,null,2));if(failures.length)process.exit(1);
export {};
