/** Shape only; original native snapshot/protection/authority remain unqualified. */
const {default:Ajv}=await import(process.argv[2]);
const base=await Bun.file('docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json').json();
const schema=await Bun.file('docs/helix/02-design/contracts/seed-snapshot-evidence-v0.1.schema.json').json();
const validate=new Ajv({strict:true}).addSchema(base).compile(schema);
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const fixture={interfaceVersion:'truss-seed-snapshot-evidence/0.1.0',attempt:{interfaceVersion:'truss-seed-activation/0.1.0',seedId:'seed',worker:{context:{sourceEpoch:'epoch',feedProfile:'draft',scopeIdentity:'scope'},consumerId:'consumer',registrationId:'registration',generation:'1'},activationProfile:pin},snapshotProfile:pin,layoutProfile:pin,valueProfile:pin,interpretationProfile:pin,catalogRevision:'1',snapshot:{xmin:'10',xmax:'20',inProgress:['10','14']},procedure:artifact,protection:artifact,currentAuthority:artifact};
const cases:[string,unknown,boolean][]=[
 ['complete',fixture,true],['empty classifier',{...fixture,snapshot:{xmin:'20',xmax:'20',inProgress:[]}},true],
 ['baseline reverse dependency',{...fixture,baseline:artifact},false],
 ['missing protection',{...fixture,protection:undefined},false],
 ['duplicate xid',{...fixture,snapshot:{...fixture.snapshot,inProgress:['10','10']}},false],
 ['numeric xid',{...fixture,snapshot:{...fixture.snapshot,xmin:10}},false],
 ['reverse interval requires semantic refusal',{...fixture,snapshot:{xmin:'20',xmax:'10',inProgress:[]}},true],
 ['out of range requires semantic refusal',{...fixture,snapshot:{...fixture.snapshot,inProgress:['99']}},true],
 ['forged authority requires semantic refusal',{...fixture,currentAuthority:{...artifact,identity:'forged'}},true]
];
const failures=cases.filter(([,v,e])=>Boolean(validate(v))!==e).map(([n])=>n);
const receipt={scope:'Snapshot evidence shape only; no native authority/protection/classifier truth',cases:cases.length,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/seed-snapshot-evidence.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
