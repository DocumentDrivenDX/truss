/** Locator shape only: original native/provenance/action admission remains separate. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
for(const file of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+file).json());
const check=ajv.getSchema('urn:truss:draft:key-migration-locator-correspondence:0.1.0')!;
const pin={identity:'fixture',version:'0.1.0',sha256:'0'.repeat(64)},artifact={identity:'fixture',bytesBase64:'eA==',sha256:'0'.repeat(64)};
const attempt={kind:'installed',databaseIdentity:'db',schemaName:'truss',installationId:'install',sourceEpoch:'epoch',migrationAttemptId:'attempt',procedure:pin,originalRequest:artifact};
const held=(storageRowId:string)=>({state:'held',storageRowId,rowEvidence:artifact}),omitted={state:'omitted',missingComponentEvidence:artifact};
const baseline={interfaceVersion:'truss-key-migration-locator-correspondence/0.1.0',originalAttempt:attempt,sourceInventory:artifact,targetCorrespondence:artifact,locatorProfile:pin,entries:[{sourceEntryId:'entry',kind:'live',action:'replaced',source:held('1'),target:held('2')}],originalObservation:artifact,completeCorrespondenceEvidence:artifact};
const results:any[]=[],failures:any[]=[];
function probe(name:string,expected:boolean,mutate:(value:any)=>void){const value=structuredClone(baseline);mutate(value);const actual=Boolean(check(value));const row={name,expected,actual};results.push(row);if(expected!==actual)failures.push(row);}
probe('live replacement',true,()=>{});
probe('reservation replacement',true,v=>v.entries[0].kind='reservation');
probe('unchanged projection',true,v=>{v.entries[0].action='unchanged';v.entries[0].target=held('1');});
probe('created live projection',true,v=>{v.entries[0].action='created';v.entries[0].source=omitted;});
probe('removed live projection',true,v=>{v.entries[0].action='removed';v.entries[0].target=omitted;});
probe('continuing omission',true,v=>{v.entries[0].action='omitted';v.entries[0].source=omitted;v.entries[0].target=omitted;});
probe('reservation removal forbidden',false,v=>{v.entries[0].kind='reservation';v.entries[0].action='removed';v.entries[0].target=omitted;});
probe('zero physical locator',false,v=>v.entries[0].source.storageRowId='0');
probe('host number locator',false,v=>v.entries[0].target.storageRowId=2);
probe('missing row evidence',false,v=>delete v.entries[0].target.rowEvidence);
probe('missing complete evidence',false,v=>delete v.completeCorrespondenceEvidence);
probe('future receipt is not grammar member',false,v=>v.receipt=artifact);
probe('duplicate source needs semantic refusal',true,v=>v.entries.push(v.entries[0]));
probe('replacement same locator needs semantic refusal',true,v=>v.entries[0].target.storageRowId='1');
probe('native overflow needs semantic refusal',true,v=>v.entries[0].target.storageRowId='9223372036854775808');
const receipt={scope:'Fifteen locator correspondence shapes including deliberately shape-valid native/semantic counterexamples; no native mapping/custody qualification',cases:results.length,results,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/migration-locators.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({scope:receipt.scope,cases:receipt.cases,failures}));if(failures.length)process.exit(1);export {};
