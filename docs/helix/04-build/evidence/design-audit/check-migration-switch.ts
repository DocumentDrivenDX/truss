/** Switch shape only; original native effect/custody arithmetic remains semantic. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
for(const file of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+file).json());
const check=ajv.getSchema('urn:truss:draft:key-migration-switch-evidence:0.1.0')!;
const pin={identity:'fixture',version:'0.1.0',sha256:'0'.repeat(64)},artifact={identity:'fixture',bytesBase64:'eA==',sha256:'0'.repeat(64)};
const attempt={kind:'installed',databaseIdentity:'db',schemaName:'truss',installationId:'install',sourceEpoch:'epoch',migrationAttemptId:'attempt',procedure:pin,originalRequest:artifact};
const baseline={interfaceVersion:'truss-key-migration-switch-evidence/0.1.0',originalAttempt:attempt,procedure:pin,originalExclusion:artifact,locatorCorrespondence:artifact,guardEffects:[{namespaceSha256:'0'.repeat(64),keySha256:'1'.repeat(64),original:{state:'existing',generation:'5'},deletions:'1',insertions:'1',resultingGeneration:'7',actualEffectEvidence:artifact}],priorAdmission:artifact,resultingAdmission:artifact,installedInventory:artifact,originalObservation:artifact,completeEffectEvidence:artifact};
const results:any[]=[],failures:any[]=[];
function probe(name:string,expected:boolean,mutate:(v:any)=>void){const v=structuredClone(baseline);mutate(v);const actual=Boolean(check(v));const row={name,expected,actual};results.push(row);if(actual!==expected)failures.push(row);}
probe('existing guard effects',true,()=>{});
probe('created guard effects',true,v=>{v.guardEffects[0].original={state:'created'};v.guardEffects[0].deletions='0';v.guardEffects[0].resultingGeneration='1';});
probe('missing exclusion',false,v=>delete v.originalExclusion);
probe('missing locator artifact',false,v=>delete v.locatorCorrespondence);
probe('missing actual guard evidence',false,v=>delete v.guardEffects[0].actualEffectEvidence);
probe('native numeric generation',false,v=>v.guardEffects[0].resultingGeneration=7);
probe('future receipt excluded',false,v=>v.receipt=artifact);
probe('future commit excluded',false,v=>v.commitObservation=artifact);
probe('duplicate route needs semantic refusal',true,v=>v.guardEffects.push(v.guardEffects[0]));
probe('wrong sum needs semantic refusal',true,v=>v.guardEffects[0].resultingGeneration='5');
probe('created guard deletion needs semantic refusal',true,v=>v.guardEffects[0].original={state:'created'});
probe('native overflow needs semantic refusal',true,v=>v.guardEffects[0].resultingGeneration='9223372036854775808');
const receipt={scope:'Twelve switch evidence shapes including deliberate semantic/native counterexamples; no native producer/guard/commit qualification',cases:results.length,results,failures};await Bun.write('docs/helix/04-build/evidence/design-audit/migration-switch.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({scope:receipt.scope,cases:receipt.cases,failures}));if(failures.length)process.exit(1);export {};
