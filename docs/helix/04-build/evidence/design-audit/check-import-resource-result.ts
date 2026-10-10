/** Shape evidence only; no native import/durability qualification. */
import {readFileSync} from 'node:fs';
const path=process.argv[2];if(!path)throw Error('Pass installed Ajv Draft 2020-12 path');
const {default:Ajv}=await import(path);
const schema=JSON.parse(readFileSync(new URL('../../../02-design/contracts/import-report-v0.1.schema.json',import.meta.url),'utf8'));
const validate=new Ajv({strict:true}).compile(schema);
const sha='a'.repeat(64),pin={identity:'fixture',version:'0.1.0',sha256:sha};
const counts={createdCommitted:'0',createdPending:'0',createdRolledBack:'0',createdCommitUnknown:'0',createdTransactionUnresolved:'0',attemptUnknown:'1',skipped:'0',rejected:'0',unprocessed:'0'};
const outcome={inputIndex:'0',batchId:'b',outcome:'attempt_unknown',recoveryReference:'recovery'};
const batch={batchId:'b',inputIndices:['0'],disposition:'transaction_unresolved',recoveryReference:'recovery'};
const selectedConfiguration={sourceEpoch:'fixture',installationId:'fixture',generation:'1',keyReuse:'forbid',journalMode:'trigger',configurationProfile:pin,installedProducerInventorySha256:sha};
const base={interfaceVersion:'truss-import-report/0.1.0',attemptId:'attempt',inputCount:'1',executedCatalogRevision:'1',importProfile:pin,selectedConfiguration,inputSha256:sha,execution:'engine_owned',status:'interrupted',outcomes:[outcome],batches:[batch],unprocessedIndices:[],counts};
const identity={id:'9007199254740993',typeId:'1',definitionPin:'fixture',owner:{documentId:'d',moduleId:'m'}};
const a=new Ajv({strict:true});a.addSchema(schema);a.addSchema(await Bun.file('docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json').json());
const resource=a.compile(await Bun.file('docs/helix/02-design/contracts/import-resource-result-v0.1.schema.json').json());
const progress={...base,outcomes:[],batches:[],unprocessedIndices:['0'],counts:{...counts,attemptUnknown:'0',unprocessed:'1'}};
const value={outcome:'resource_limited',reason:'operation_deadline',resourceProfile:pin,report:progress};
const cases:[string,unknown,boolean][]=[['coherent no-writer interruption',value,true],['processed cannot be limited',{...value,report:{...progress,status:'processed'}},false],['report mandatory',{outcome:'resource_limited',reason:'candidate_bytes',resourceProfile:pin},false],['no database error contamination',{...value,error:{code:'cancelled'}},false],['reason closed',{...value,reason:'unknown'},false],['unresolved cleanup needs execution refusal',{...value,report:base},true],['false unprocessed inventory semantic refusal',{...value,report:{...progress,unprocessedIndices:[]}},true]];
const failures=cases.filter(([,v,e])=>Boolean(resource(v))!==e).map(([n])=>n);console.log(JSON.stringify({scope:'resource interruption shape, not actual containment/progress',cases:cases.length,failures},null,2));if(failures.length)process.exit(1);export {};
