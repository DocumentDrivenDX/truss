/** Existing import result composition only; progress truth requires native evidence. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
const root='docs/helix/02-design/contracts/';
for(const n of ['acceptance-input-v0.1','execution-failure-v0.1','import-report-v0.1','import-resource-result-v0.1','import-execution-result-v0.1.proposal'])
 ajv.addSchema(await Bun.file(root+n+'.schema.json').json());
const pin={identity:'fixture',version:'0.1',sha256:'a'.repeat(64)};
const counts={createdCommitted:'0',createdPending:'0',createdRolledBack:'0',createdCommitUnknown:'0',createdTransactionUnresolved:'0',attemptUnknown:'0',skipped:'0',rejected:'0',unprocessed:'1'};
const report={interfaceVersion:'truss-import-report/0.1.0',attemptId:'fixture',inputCount:'1',executedCatalogRevision:'1',importProfile:pin,
 selectedConfiguration:{sourceEpoch:'fixture',installationId:'fixture',generation:'1',keyReuse:'forbid',journalMode:'trigger',configurationProfile:pin,installedProducerInventorySha256:pin.sha256},
 inputSha256:pin.sha256,execution:'engine_owned',status:'interrupted',outcomes:[],batches:[],unprocessedIndices:['0'],counts};
const error={code:'retry',retryScope:'whole_transaction',message:'fixture'};
let count=0;
for(const [name,mode,other] of [['engineOwned','engine_owned','host_adopted'],['inTransaction','host_adopted','engine_owned']] as const){
 const validate=ajv.getSchema('urn:truss:proposal:import-execution-result:0.1.0#/$defs/'+name);if(!validate)throw Error(name);
 const progress={...report,execution:mode};
 const cases:[string,unknown,boolean][]=[
  ['reported progress',{outcome:'reported',report:progress},true],
  ['execution failure preserves report',{outcome:'execution_failed',error,report:progress},true],
  ['pre-submission null report shape',{outcome:'execution_failed',error,report:null},true],
  ['missing report is not null',{outcome:'execution_failed',error},false],
  ['wrong ownership',{outcome:'reported',report:{...progress,execution:other}},false],
  ['outer engine scope distinction',{outcome:'reported',report:{...progress,execution:'outer_engine_scope'}},name==='inTransaction'],
  ['resource interruption requires progress',{outcome:'resource_limited',reason:'operation_deadline',resourceProfile:pin,report:progress},true],
  ['resource result cannot be processed',{outcome:'resource_limited',reason:'operation_deadline',resourceProfile:pin,report:{...progress,status:'processed'}},false],
  ['resource interruption cannot erase progress',{outcome:'resource_limited',reason:'operation_deadline',resourceProfile:pin},false],
  ['invalid diagnostic',{outcome:'invalid',diagnosticProfile:pin,diagnostic:{identity:'fixture',bytesBase64:'',sha256:pin.sha256}},true],
  ['invalid has no report',{outcome:'invalid',diagnosticProfile:pin,diagnostic:{identity:'fixture',bytesBase64:'',sha256:pin.sha256},report:progress},false],
  ['no generic Outcome',{status:'ok',value:{outcome:'reported',report:progress}},false]
 ];
 for(const [label,value,wanted] of cases){if(Boolean(validate(value))!==wanted)throw Error(name+' '+label+': '+JSON.stringify(validate.errors));count++;}
}
const library=ajv.getSchema('urn:truss:proposal:import-execution-result:0.1.0');
if(!library||library({outcome:'reported',report}))throw Error('Definitions-only root must refuse wires');count++;
console.log(count+' import composition controls passed. Null-before-submission, actual progress and native ownership/termination remain unqualified.');
export {};
