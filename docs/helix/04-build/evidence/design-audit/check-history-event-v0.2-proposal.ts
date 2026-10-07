/** Complete proposal wire shape only; no semantic/native profile adoption. */
const {default:Ajv}=await import(process.argv[2]);
const root='docs/helix/02-design/contracts/';
const names=['exact-value-v0.1.schema.json','history-record-v0.1.schema.json','history-event-v0.1.schema.json','history-retain-payload-v0.1.proposal.schema.json','history-event-v0.2.proposal.schema.json'];
const ajv=new Ajv({strict:true});for(const name of names)ajv.addSchema(await Bun.file(root+name).json());
const current=ajv.getSchema('urn:truss:draft:history-event:0.1.0')!,proposal=ajv.getSchema('urn:truss:proposal:history-event:0.2.0')!;
const identity={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'doc',moduleId:'module'}};
const context={interfaceVersion:'truss-history-event/0.2.0-proposal',sourceEpoch:'epoch',historyProfile:'fixture',xid:'1',seq:'1',identity,eventVersion:'2',eventCatalogRevision:'1',mutationGroup:{profile:'truss-history-group/0.1.0',eventCount:'1',orderedEventDigest:'0'.repeat(64)},origin:{asserted:{kind:'null'},databaseRole:'role'}};
const absent={present:false},present={present:true,value:{kind:'null'}};
const record={interfaceVersion:'truss-history-record/0.1.0',identity,recordVersion:'1',catalogRevision:'1',createdAt:'fixture',updatedAt:'fixture',properties:[],retained:[],kind:'object',ownership:{state:'rootless'}};
const member={retainedName:'a/b',before:absent,after:present,beforeDefinitionContext:'before',afterDefinitionContext:'after',sourceContext:'source'};
const variants=[{operation:'create',after:record},{operation:'delete',before:record},{operation:'property',propertyId:'1',definitionPin:'fixture',before:absent,after:present},{operation:'transform',propertyId:'1',beforeDefinitionPin:'before',afterDefinitionPin:'after',before:absent,after:present},{operation:'rebind',retainedName:'retained',propertyId:'1',beforeDefinitionContext:'old',afterDefinitionPin:'new',retainedBefore:present,retainedAfter:absent,propertyBefore:absent,propertyAfter:present},{operation:'metadata',before:record,after:record}];
const outcomes=[];
for(const variant of variants){const old={...context,...variant,interfaceVersion:'truss-history-event/0.1.0'},next={...context,...variant};if(!current(old)||!proposal(next)||current(next)||proposal(old))throw Error('version isolation '+variant.operation);outcomes.push({name:variant.operation,oldAndNewShapeValid:true,versionIsolation:true});}
const retain={...context,operation:'retain',retainedChanges:[member]};
const cases:[string,unknown,boolean][]=[['complete retain',retain,true],['multiple names one event',{...retain,retainedChanges:[member,{...member,retainedName:'é'}]},true],['payload without custody',{interfaceVersion:context.interfaceVersion,operation:'retain',retainedChanges:[member]},false],['missing group',Object.fromEntries(Object.entries(retain).filter(([k])=>k!=='mutationGroup')),false],['missing original context',{...retain,retainedChanges:[{...member,sourceContext:''}]},false],['empty changes',{...retain,retainedChanges:[]},false],['replacement',{...retain,retainedChanges:[{...member,before:present}]},false],['removal',{...retain,retainedChanges:[{...member,after:absent}]},false],['unknown root',{...retain,extra:true},false],['duplicate names need semantic refusal',{...retain,retainedChanges:[member,member]},true],['forged original context needs semantic admission',{...retain,retainedChanges:[{...member,sourceContext:'forged'}]},true]];
for(const [name,value,expected] of cases){const actual=Boolean(proposal(value));if(actual!==expected)throw Error(name+' '+JSON.stringify(proposal.errors));outcomes.push({name,expected,actual});}
if(current(retain)||current({...retain,interfaceVersion:'truss-history-event/0.1.0'}))throw Error('retain entered old union');
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const helper='docs/helix/04-build/evidence/design-audit/check-history-event-v0.2-proposal.ts';
const pins=await Promise.all([...names.map(n=>root+n),helper].map(async path=>({path,sha256:hash(await Bun.file(path).text())})));
await Bun.write('docs/helix/04-build/evidence/design-audit/history-event-v0.2-proposal-audit.json',JSON.stringify({scope:'strict Draft 2020-12 complete event proposal shape and old/new version isolation only',bunVersion:Bun.version,sourcePins:pins,outcomes,nativeExecuted:false,adopted:false},null,2)+'\n');
console.log(JSON.stringify({priorVariants:6,retainCases:cases.length,oldVersionRejectsRetain:true,passed:true,nativeExecuted:false,adopted:false}));
