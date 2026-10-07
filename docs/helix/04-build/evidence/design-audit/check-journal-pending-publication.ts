/** Pending publication shape only; placeholder artifacts are not authentic append evidence. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
const base='docs/helix/02-design/contracts/';for(const f of new Bun.Glob('*.schema.json').scanSync(base))a.addSchema(await Bun.file(base+f).json());
const v=a.getSchema('urn:truss:proposal:journal-pending-publication:0.2.0')!;
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)},pin={identity:'fixture',version:'0.1.0',sha256:'b'.repeat(64)};
const context={interfaceVersion:'truss-row-operation-context/0.1.0',profile:pin,installationIdentity:'installation',originalInstallation:artifact,originalLayout:artifact,originalResourceProfile:artifact,originalWriterXid:'7',operationOrdinal:'0',originalOperationDefinition:artifact,originalExecutionContext:artifact,originalActingRoleContext:artifact,originalCatalogAuthorityCut:artifact,originalOwnerUnion:artifact,originalGroupAdmission:artifact,addressDomain:'truss-row-operation-address/0.1.0',authority:'actual-protected-native-registry-correspondence',durability:'transaction-local-until-original-commit-observation'};
const identity={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'doc',moduleId:'module'}};

const before={interfaceVersion:'truss-history-record/0.1.0',identity:structuredClone(identity),recordVersion:'1',catalogRevision:'1',createdAt:'fixture',updatedAt:'fixture',properties:[],retained:[],kind:'object',ownership:{state:'rootless'}};
const event={interfaceVersion:'truss-history-event/0.2.0-proposal',sourceEpoch:'epoch',historyProfile:'fixture',xid:'7',seq:'41',identity:structuredClone(identity),eventVersion:'2',eventCatalogRevision:'1',mutationGroup:{profile:'truss-history-group/0.1.0',eventCount:'1',orderedEventDigest:'0'.repeat(64)},origin:{asserted:{kind:'null'},databaseRole:'role'},operation:'metadata',before:structuredClone(before),after:{...structuredClone(before),recordVersion:'2'}};
const component=(kind:string)=>({interfaceVersion:'truss-journal-exact-bytes/0.2.0-proposal',eventInterfaceVersion:'truss-history-event/0.2.0-proposal',component:kind,canonicalizationProfile:structuredClone(pin),bytesBase64:'e30=',bytesSha256:'a'.repeat(64)});
const fixture=()=>({interfaceVersion:'truss-journal-pending-publication/0.2.0-proposal',producerProfile:structuredClone(pin),observationProfile:structuredClone(pin),originalOperationContext:structuredClone(context),originalPrepared:structuredClone(artifact),originalReservedMapping:structuredClone(artifact),completeGroupInventory:structuredClone(artifact),pendingPublicationEvidence:structuredClone(artifact),rows:[{ordinal:'0',event:structuredClone(event),physical:{entityKind:'o',entityId:'1',entityType:'1',recordVersion:'2',catalogRevision:'1',xid:'7',seq:'41',op:'metadata',propertyId:null,atText:'2026-10-06 00:00:00+00',dateStyle:'ISO, MDY',timeZone:'UTC',oldValue:null,newValue:component('event'),origin:component('origin')},nativeDescriptorEvidence:structuredClone(artifact),actualAppendEvidence:structuredClone(artifact)}],durability:'pending-original-host-settlement'}) as any;
const cases:[string,(x:any)=>void,boolean][]=[
 ['complete pending shape with placeholder artifacts',()=>{},true],
 ['empty scope requires original complete proof',x=>{x.rows=[];},true],
 ['missing original preparation',x=>{delete x.originalPrepared;},false],
 ['missing original reservation',x=>{delete x.originalReservedMapping;},false],
 ['missing actual append evidence',x=>{delete x.rows[0].actualAppendEvidence;},false],
 ['missing native descriptors',x=>{delete x.rows[0].nativeDescriptorEvidence;},false],
 ['NULL event carrier',x=>{x.rows[0].physical.newValue=null;},false],
 ['non-NULL old-value shadow',x=>{x.rows[0].physical.oldValue={};},false],
 ['event/origin carrier confusion',x=>{x.rows[0].physical.origin.component='event';},false],
 ['numeric physical seq',x=>{x.rows[0].physical.seq=41;},false],
 ['commit acknowledgment',x=>{x.durability='committed';},false],
 ['feed application acknowledgment',x=>{x.feedApplied=true;},false],
 ['missing physical clock context',x=>{delete x.rows[0].physical.timeZone;},false],
 ['semantic/physical seq mismatch needs refusal',x=>{x.rows[0].physical.seq='42';},true],
 ['semantic/physical kind mismatch needs refusal',x=>{x.rows[0].physical.entityKind='e';},true],
 ['semantic/physical op mismatch needs refusal',x=>{x.rows[0].physical.op='create';},true],
 ['duplicate actual row needs semantic refusal',x=>{x.rows.push(structuredClone(x.rows[0]));},true],
 ['noncanonical pad bits need semantic refusal',x=>{x.rows[0].physical.newValue.bytesBase64='Zh==';},true],
 ['substituted native role needs semantic refusal',x=>{x.rows[0].event.origin.databaseRole='foreign';},true]
];
const outcomes=cases.map(([name,mutate,expected])=>{const x=fixture();mutate(x);const actual=Boolean(v(x));if(actual!==expected)throw Error(name+' '+JSON.stringify(v.errors));return {name,expected,actual};});
const paths=['journal-pending-publication-v0.2.proposal.schema.json','journal-exact-bytes-v0.2.proposal.schema.json','history-event-v0.2.proposal.schema.json','history-retain-payload-v0.1.proposal.schema.json','truss-row-operation-context-v0.1.proposal.schema.json','history-record-v0.1.schema.json','exact-value-v0.1.schema.json','acceptance-input-v0.1.schema.json'].map(n=>base+n);paths.push('docs/helix/04-build/evidence/design-audit/check-journal-pending-publication.ts');
const sourcePins=await Promise.all(paths.map(async path=>({path,sha256:new Bun.CryptoHasher('sha256').update(await Bun.file(path).text()).digest('hex')})));
await Bun.write('docs/helix/04-build/evidence/design-audit/journal-pending-publication-audit.json',JSON.stringify({scope:'private pending row/event/component shape only; placeholder bytes/artifacts are not authentic source/append/canonical/native/group/role/resource evidence',bunVersion:Bun.version,sourcePins,outcomes,nativeExecuted:false,adopted:false},null,2)+'\n');
console.log(JSON.stringify({cases:outcomes.length,passed:true,nativeExecuted:false,adopted:false}));
