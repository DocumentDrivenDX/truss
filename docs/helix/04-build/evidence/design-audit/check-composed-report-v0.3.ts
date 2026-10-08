/** Combined report shape evidence only; original semantic/native admission remains separate. */
const {default:Ajv}=await import(process.argv[2]);
const root='docs/helix/02-design/contracts/';
const files=new Map<string,{path:string,schema:any}>();
for(const entry of new Bun.Glob('*.schema.json').scanSync(root)){const schema=await Bun.file(root+entry).json();if(schema.$id)files.set(schema.$id,{path:root+entry,schema});}
const ids=['urn:truss:proposal:acceptance-report:0.3.0','urn:truss:proposal:acceptance-report:0.2.0'];
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
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const input={interfaceVersion:'truss-acceptance-input/0.1.0',layoutProfile:pin,acceptanceProfile:pin,validatorProfile:pin,supportProfile:pin,documents:[{documentId:'doc',documentRevision:'r1',artifact,umfProfile:pin,ingress:{kind:'native'}}],binding:{state:'absent'},policy:{unknownEndpoint:'reject',loss:'strict',profile:pin},transforms:[]};
const originalReport={interfaceVersion:'truss-acceptance-report/0.1.0',reportProfile:pin,rev:'1',originalExecution:{installationId:'installation',sourceEpoch:'epoch',origin:{asserted:{operation:'accept'},databaseRole:'role'},journalOrigin:{asserted:{kind:'string',text:'origin'},databaseRole:'role'},originMappingProfile:pin,captureProfile:pin,contextEvidence:artifact},acceptedInput:input,transformRegistrations:[],umf:[{version:'0.7.0',interpretationProfile:pin,supportedSubset:artifact}],documents:[{doc_id:'doc',doc_revision:'r1',content_sha256:artifact.sha256,ord:'0'}],diagnostics:[],documentInterpretations:[{documentId:'doc',contentSha256:artifact.sha256,interpretationProfile:pin,completeness:'complete',evidence:artifact}],counts:{typesAdded:'0',propertiesAdded:'0',keysAdded:'0',relationshipsAdded:'0',endpointsAdded:'0',elementsRetired:'0'},provisional:[],rebinds:[],assertions:{interfaceVersion:'truss-enforcement-report/0.1.0',catalogRevision:'1',reportProfile:pin,layoutProfile:pin,scope:{kind:'complete'},assertionInventorySha256:artifact.sha256,entries:[]},pending_indexes:[],losses:[],extensions:[]};
const lifecycle={identity:{kind:'key',typeId:'1',keyNumber:'1'},owner:{documentId:'doc',moduleId:'module'},lineage:artifact,beforeRetiredRevision:'1',beforeDefinition:artifact,afterDefinition:artifact};
const wrapper={...originalReport,interfaceVersion:'truss-acceptance-report/0.3.0-proposal',rebinds:[rebind],lifecycleProfile:pin,reactivations:[lifecycle]};
const without=(key:string)=>Object.fromEntries(Object.entries(wrapper).filter(([k])=>k!==key));
const cases:[string,unknown,boolean][]=[
 ['combined complete wrapper',wrapper,true],
 ['empty lifecycle inventory remains a shape-valid non-reactivation report',{...wrapper,reactivations:[]},true],
 ['missing explicit lifecycle inventory',without('reactivations'),false],
 ['missing lifecycle profile',without('lifecycleProfile'),false],
 ['missing original execution',without('originalExecution'),false],
 ['missing before definition',{...wrapper,reactivations:[Object.fromEntries(Object.entries(lifecycle).filter(([k])=>k!=='beforeDefinition'))]},false],
 ['unowned key identity',{...wrapper,reactivations:[{...lifecycle,identity:{kind:'key',keyNumber:'1'}}]},false],
 ['old event discriminator',{...wrapper,rebinds:[{...rebind,interfaceVersion:'truss-history-event/0.1.0'}]},false],
 ['mixed event versions',{...wrapper,rebinds:[rebind,{...rebind,interfaceVersion:'truss-history-event/0.1.0'}]},false],
 ['retain cannot substitute for report rebind',{...wrapper,rebinds:[retain]},false],
 ['opaque lifecycle substitution',{...without('reactivations'),extensions:[{reactivations:[lifecycle]}]},false],
 ['old report discriminator with new fields',{...wrapper,interfaceVersion:'truss-acceptance-report/0.2.0-proposal'},false],
 ['unknown root field',{...wrapper,extra:true},false]
];
const validate=ajv.getSchema(ids[0])!;
const outcomes=cases.map(([name,value,expected])=>{const actual=Boolean(validate(value));if(actual!==expected)throw Error(name+' '+JSON.stringify(validate.errors));return {name,expected,actual};});
const old=ajv.getSchema(ids[1])!;
if(old(wrapper))throw Error('v0.2 implicitly accepts composed v0.3 report');
outcomes.push({name:'v0.2 refuses implicit composed upgrade',expected:false,actual:false});
const hash=(text:string)=>new Bun.CryptoHasher('sha256').update(text).digest('hex');
const helper='docs/helix/04-build/evidence/design-audit/check-composed-report-v0.3.ts';
const sourcePins=await Promise.all([...selected.values()].map(async({path})=>({path,sha256:hash(await Bun.file(path).text())})));
sourcePins.push({path:helper,sha256:hash(await Bun.file(helper).text())});
const receipt={scope:'complete composed report v0.3 schema shape controls; fixtures are synthetic and hashes are placeholders; no digest, identity range, transition completeness, actual effects or native qualification',bunVersion:Bun.version,sourcePins,outcomes,nativeExecuted:false,adopted:false};
await Bun.write('docs/helix/04-build/evidence/design-audit/composed-report-v0.3-shapes.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({cases:outcomes.length,passed:true,nativeExecuted:false}));
export {};
