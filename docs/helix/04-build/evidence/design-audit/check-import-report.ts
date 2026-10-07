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
const cases:readonly [string,unknown,boolean][]=[
 ['outer engine scope pending',{...base,execution:'outer_engine_scope',outcomes:[{inputIndex:'0',batchId:'b',outcome:'created',identity,version:'1'}],batches:[{batchId:'b',inputIndices:['0'],disposition:'pending',hostTransactionId:'outer'}],counts:{...counts,attemptUnknown:'0',createdPending:'1'}},true],
 ['outer engine scope committed needs semantic rejection',{...base,execution:'outer_engine_scope',batches:[{batchId:'b',inputIndices:['0'],disposition:'committed',commitEvidenceSha256:sha}]},true],
 ['missing configuration',{...base,selectedConfiguration:undefined},false],
 ['native numeric configuration generation',{...base,selectedConfiguration:{...selectedConfiguration,generation:1}},false],
 ['unknown reuse policy',{...base,selectedConfiguration:{...selectedConfiguration,keyReuse:'reuse'}},false],
 ['shape does not prove producer inventory installed',{...base,selectedConfiguration:{...selectedConfiguration,installedProducerInventorySha256:'b'.repeat(64)}},true],
 ['unresolved writer attempt',base,true],
 ['observed create with commit uncertainty',{...base,outcomes:[{inputIndex:'0',batchId:'b',outcome:'created',identity,version:'1'}],batches:[{...batch,disposition:'commit_unknown'}],counts:{...counts,attemptUnknown:'0',createdCommitUnknown:'1'}},true],
 ['rejected input',{...base,outcomes:[{inputIndex:'0',batchId:'b',outcome:'rejected',code:'invalid'}]},true],
 ['skipped identity',{...base,outcomes:[{inputIndex:'0',batchId:'b',outcome:'skipped',reason:'live_identity',identity}]},true],
 ['created missing identity',{...base,outcomes:[{inputIndex:'0',batchId:'b',outcome:'created',version:'1'}]},false],
 ['committed missing proof',{...base,batches:[{batchId:'b',inputIndices:['0'],disposition:'committed'}]},false],
 ['native numeric count',{...base,counts:{...counts,attemptUnknown:1}},false],
 ['unknown outcome',{...base,outcomes:[{...outcome,outcome:'success'}]},false],
 ['duplicate index needs semantic rejection',{...base,outcomes:[outcome,outcome]},true],
 ['false count needs semantic rejection',{...base,counts:{...counts,createdCommitted:'99'}},true],
 ['host committed disposition needs semantic rejection',{...base,execution:'host_adopted',batches:[{batchId:'b',inputIndices:['0'],disposition:'committed',commitEvidenceSha256:sha}]},true],
 ['processed unresolved attempt cannot qualify full-load success',{...base,status:'processed'},true]
];
const outcomes=cases.map(([name,input,expected])=>{const actual=Boolean(validate(input));if(actual!==expected)throw Error(name);return {name,expected,actual}});
console.log(JSON.stringify({scope:'Import report shape only; no count, index coverage, ownership, evidence trust or native qualification',cases:outcomes.length,outcomes},null,2));
