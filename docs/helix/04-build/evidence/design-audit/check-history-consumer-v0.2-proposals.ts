/** Proposal schema compilation and embedded event-array controls, not complete runtime consumers. */
const {default:Ajv}=await import(process.argv[2]);
const root='docs/helix/02-design/contracts/';
const files=new Map<string,{path:string,schema:any}>();
for(const entry of new Bun.Glob('*.schema.json').scanSync(root)){const schema=await Bun.file(root+entry).json();if(schema.$id)files.set(schema.$id,{path:root+entry,schema});}
const stems=['journal-page-result','retained-history-archive','acceptance-report'];
const ids=stems.map(stem=>'urn:truss:proposal:'+stem+':0.2.0');
const selected=new Map<string,{path:string,schema:any}>();
function collect(id:string){if(selected.has(id))return;const source=files.get(id);if(!source)throw Error('missing schema '+id);selected.set(id,source);function walk(v:any){if(v&&typeof v==='object'){if(typeof v.$ref==='string'&&!v.$ref.startsWith('#'))collect(v.$ref.split('#')[0]);for(const x of Object.values(v))walk(x);}}walk(source.schema);}
ids.forEach(collect);
const ajv=new Ajv({strict:true});for(const [id,{schema}] of selected)ajv.addSchema(schema,id);
for(const id of ids)if(!ajv.getSchema(id))throw Error('missing compiled consumer');
const identity={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'doc',moduleId:'module'}};
const context={interfaceVersion:'truss-history-event/0.2.0-proposal',sourceEpoch:'epoch',historyProfile:'fixture',xid:'1',seq:'1',identity,eventVersion:'2',eventCatalogRevision:'1',mutationGroup:{profile:'truss-history-group/0.1.0',eventCount:'1',orderedEventDigest:'0'.repeat(64)},origin:{asserted:{kind:'null'},databaseRole:'role'}};
const absent={present:false},present={present:true,value:{kind:'null'}};
const retain={...context,operation:'retain',retainedChanges:[{retainedName:'a',before:absent,after:present,beforeDefinitionContext:'before',afterDefinitionContext:'after',sourceContext:'source'}]};
const rebind={...context,operation:'rebind',retainedName:'a',propertyId:'1',beforeDefinitionContext:'before',afterDefinitionPin:'after',retainedBefore:present,retainedAfter:absent,propertyBefore:absent,propertyAfter:present};
const outcomes=[];
for(const [index,id] of ids.entries()){
 const pointer=index===0?'#/oneOf/0/properties/events':index===1?'#/properties/events':'#/properties/rebinds';
 const validate=ajv.getSchema(id+pointer);if(!validate)throw Error('missing event-array validator');
 for(const [name,events,expected] of [['new rebind',[rebind],true],['new retain',[retain],index!==2],['old version',[{...rebind,interfaceVersion:'truss-history-event/0.1.0'}],false],['mixed versions',[rebind,{...rebind,interfaceVersion:'truss-history-event/0.1.0'}],false]] as const){const actual=Boolean(validate(events));if(actual!==expected)throw Error(id+' '+name);outcomes.push({consumer:id,name,expected,actual});}
}
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const input={interfaceVersion:'truss-acceptance-input/0.1.0',layoutProfile:pin,acceptanceProfile:pin,validatorProfile:pin,supportProfile:pin,documents:[{documentId:'doc',documentRevision:'r1',artifact,umfProfile:pin,ingress:{kind:'native'}}],binding:{state:'absent'},policy:{unknownEndpoint:'reject',loss:'strict',profile:pin},transforms:[]};
const originalReport={interfaceVersion:'truss-acceptance-report/0.1.0',reportProfile:pin,rev:'1',originalExecution:{installationId:'installation',sourceEpoch:'epoch',origin:{asserted:{operation:'accept'},databaseRole:'role'},journalOrigin:{asserted:{kind:'string',text:'origin'},databaseRole:'role'},originMappingProfile:pin,captureProfile:pin,contextEvidence:artifact},acceptedInput:input,transformRegistrations:[],umf:[{version:'0.7.0',interpretationProfile:pin,supportedSubset:artifact}],documents:[{doc_id:'doc',doc_revision:'r1',content_sha256:artifact.sha256,ord:'0'}],diagnostics:[],documentInterpretations:[{documentId:'doc',contentSha256:artifact.sha256,interpretationProfile:pin,completeness:'complete',evidence:artifact}],counts:{typesAdded:'0',propertiesAdded:'0',keysAdded:'0',relationshipsAdded:'0',endpointsAdded:'0',elementsRetired:'0'},provisional:[],rebinds:[],assertions:{interfaceVersion:'truss-enforcement-report/0.1.0',catalogRevision:'1',reportProfile:pin,layoutProfile:pin,scope:{kind:'complete'},assertionInventorySha256:artifact.sha256,entries:[]},pending_indexes:[],losses:[],extensions:[]};

const baseline={interfaceVersion:'truss-history-record/0.1.0',identity,recordVersion:'1',catalogRevision:'1',createdAt:'fixture',updatedAt:'fixture',properties:[],retained:[],kind:'object',ownership:{state:'rootless'}};
const readContext={sourceEpoch:'epoch',scopeIdentity:'scope',journalProfile:pin,observationProfile:pin,snapshot:{state:'statement'}};
const wrappers=[
 {outcome:'page',context:readContext,events:[retain,rebind],safeWatermarkXid:'2',continuation:{state:'end'},observation:artifact},
 {interfaceVersion:'truss-retained-history-archive/0.2.0-proposal',sourceEpoch:'epoch',archiveProfile:pin,identity,baseline,throughVersion:'2',events:[retain,rebind],definitions:[{definitionPin:'fixture',interpretationProfile:pin,artifact}],baselineEvidence:artifact,completeEventInventory:artifact,retainedOwnerInventory:artifact,retentionEvidence:artifact},
 {...originalReport,interfaceVersion:'truss-acceptance-report/0.2.0-proposal',rebinds:[rebind]}
];
const wrapperOutcomes=[];
for(const [index,id] of ids.entries()){
 const validate=ajv.getSchema(id)!;
 const wrapper=wrappers[index];
 const eventKey=index===2?'rebinds':'events';
 const missingKey=index===0?'observation':index===1?'completeEventInventory':'originalExecution';
 const controls:[string,unknown,boolean][]=[
  ['complete positive wrapper',wrapper,true],
  ['unknown root member',{...wrapper,extra:true},false],
  ['missing required evidence',Object.fromEntries(Object.entries(wrapper).filter(([k])=>k!==missingKey)),false],
  ['old event in complete wrapper',{...wrapper,[eventKey]:[{...rebind,interfaceVersion:'truss-history-event/0.1.0'}]},false],
  ['mixed events in complete wrapper',{...wrapper,[eventKey]:[rebind,{...rebind,interfaceVersion:'truss-history-event/0.1.0'}]},false]
 ];
 if(index===2)controls.push(['retain in complete report',{...wrapper,rebinds:[retain]},false]);
 if(index===0)controls.push(['unavailable with partial rows',{outcome:'unavailable',reason:'profile',events:[retain]},false],['unavailable without payload',{outcome:'unavailable',reason:'profile'},true]);
 for(const [name,value,expected] of controls){const actual=Boolean(validate(value));if(actual!==expected)throw Error(id+' '+name+' '+JSON.stringify(validate.errors));wrapperOutcomes.push({consumer:id,name,expected,actual});}
}
const hash=(text:string)=>new Bun.CryptoHasher('sha256').update(text).digest('hex');
const pins=await Promise.all([...selected.values()].map(async({path})=>({path,sha256:hash(await Bun.file(path).text())})));
const helper='docs/helix/04-build/evidence/design-audit/check-history-consumer-v0.2-proposals.ts';pins.push({path:helper,sha256:hash(await Bun.file(helper).text())});
await Bun.write('docs/helix/04-build/evidence/design-audit/history-consumer-v0.2-proposal-audit.json',JSON.stringify({scope:'three complete proposal schemas compile; twelve embedded event-array and complete positive/negative wrapper shape controls only; no runtime or native semantic adoption',bunVersion:Bun.version,sourcePins:pins,outcomes,wrapperOutcomes,nativeExecuted:false,adopted:false},null,2)+'\n');
console.log(JSON.stringify({compiledConsumers:3,eventArrayCases:outcomes.length,wrapperCases:wrapperOutcomes.length,passed:true,nativeExecuted:false,adopted:false}));
