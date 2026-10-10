/** Snapshot shape only; complete original native/artifact parity is unproved. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
for(const f of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+f).json());
const validate=ajv.getSchema('urn:truss:draft:installation-admission:0.1.0')!;
const pin={identity:'fixture',version:'0.1.0',sha256:'0'.repeat(64)},artifact={identity:'fixture',bytesBase64:'eA==',sha256:'0'.repeat(64)};
const original={interfaceVersion:'truss-installation-admission/0.1.0',installationId:'install',sourceEpoch:'epoch',configurationGeneration:'0',keyReuse:'forbid',journalMode:'engine',configuration:artifact,selectedBinding:artifact,installedInventory:artifact,observationProfile:pin,originalObservation:artifact};
const results:any[]=[],failures:any[]=[];
function probe(name:string,expected:boolean,mutate:(v:any)=>void){const v=structuredClone(original);mutate(v);const actual=Boolean(validate(v));const row={name,expected,actual};results.push(row);if(expected!==actual)failures.push(row);}
probe('zero generation',true,()=>{});
probe('resulting generation',true,v=>v.configurationGeneration='1');
probe('negative generation',false,v=>v.configurationGeneration='-1');
probe('native numeric generation',false,v=>v.configurationGeneration=0);
probe('aliased generation',false,v=>v.configurationGeneration='00');
probe('unsupported policy',false,v=>v.keyReuse='unknown');
probe('missing configuration bytes',false,v=>delete v.configuration);
probe('missing original observation',false,v=>delete v.originalObservation);
probe('future commit excluded',false,v=>v.commitObservation=artifact);
probe('native bigint overflow needs semantic refusal',true,v=>v.configurationGeneration='9223372036854775808');
probe('configuration scalar mismatch needs semantic refusal',true,v=>v.journalMode='trigger');
probe('historical snapshot cannot confer current authority',true,v=>v.configurationGeneration='3');
const receipt={scope:'Twelve admission snapshot shape expectations; scalar/artifact/native/current-authority counterexamples deliberately shape-valid',cases:results.length,results,failures};await Bun.write('docs/helix/04-build/evidence/design-audit/installation-admission.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({scope:receipt.scope,cases:receipt.cases,failures}));if(failures.length)process.exit(1);export {};
