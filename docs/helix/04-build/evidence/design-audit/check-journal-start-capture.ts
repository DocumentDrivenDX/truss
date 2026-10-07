/** Start phase shape proposal only; original native inventory/phase/authority untested. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
const base='docs/helix/02-design/contracts/';for(const f of new Bun.Glob('*.schema.json').scanSync(base))a.addSchema(await Bun.file(base+f).json());
const v=a.getSchema('urn:truss:proposal:journal-start-capture:0.2.0')!;
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)},pin={identity:'fixture',version:'0.1.0',sha256:'b'.repeat(64)};
const context={interfaceVersion:'truss-row-operation-context/0.1.0',profile:pin,installationIdentity:'installation',originalInstallation:artifact,originalLayout:artifact,originalResourceProfile:artifact,originalWriterXid:'7',operationOrdinal:'0',originalOperationDefinition:artifact,originalExecutionContext:artifact,originalActingRoleContext:artifact,originalCatalogAuthorityCut:artifact,originalOwnerUnion:artifact,originalGroupAdmission:artifact,addressDomain:'truss-row-operation-address/0.1.0',authority:'actual-protected-native-registry-correspondence',durability:'transaction-local-until-original-commit-observation'};
const identity={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'doc',moduleId:'module'}};
const record={interfaceVersion:'truss-history-record/0.1.0',identity:structuredClone(identity),recordVersion:'1',catalogRevision:'1',createdAt:'fixture',updatedAt:'fixture',properties:[],retained:[],kind:'object',ownership:{state:'rootless'}};
const entity={identity,kind:'object',originalDefinitionContext:artifact,originalHomeInventory:artifact,start:{state:'present',record}};
const fixture=()=>structuredClone({interfaceVersion:'truss-journal-start-capture/0.2.0-proposal',producerProfile:pin,collectorProfile:pin,originalOperationContext:context,affectedInventory:artifact,entities:[entity]}) as any;
const cases:[string,(x:any)=>void,boolean][]=[
 ['complete present shape',()=>{},true],
 ['qualified absent shape',x=>{x.entities[0].start={state:'absent',absenceEvidence:artifact};},true],
 ['empty scope requires independent completeness',x=>{x.entities=[];},true],
 ['missing original context',x=>{delete x.originalOperationContext;},false],
 ['missing original role',x=>{delete x.originalOperationContext.originalActingRoleContext;},false],
 ['missing affected inventory',x=>{delete x.affectedInventory;},false],
 ['present without record',x=>{delete x.entities[0].start.record;},false],
 ['absent without evidence',x=>{x.entities[0].start={state:'absent'};},false],
 ['unknown physical kind',x=>{x.entities[0].kind='edge';},false],
 ['future group digest',x=>{x.orderedEventDigest='0'.repeat(64);},false],
 ['allocated position at start',x=>{x.entities[0].seq='1';},false],
 ['commit assertion at start',x=>{x.committed=true;},false],
 ['duplicate identities need semantic refusal',x=>{x.entities.push(structuredClone(x.entities[0]));},true],
 ['foreign record identity needs semantic refusal',x=>{x.entities[0].start.record.identity.id='2';},true],
 ['record kind mismatch needs semantic refusal',x=>{x.entities[0].kind='relationship';},true],
 ['forged native original context needs semantic refusal',x=>{x.originalOperationContext.installationIdentity='foreign';},true]
];
const outcomes=cases.map(([name,mutate,expected])=>{const x=fixture();mutate(x);const actual=Boolean(v(x));if(actual!==expected)throw Error(name+' '+JSON.stringify(v.errors));return {name,expected,actual};});
const files=['journal-start-capture-v0.2.proposal.schema.json','truss-row-operation-context-v0.1.proposal.schema.json','history-record-v0.1.schema.json','exact-value-v0.1.schema.json','acceptance-input-v0.1.schema.json'].map(n=>base+n);
files.push('docs/helix/04-build/evidence/design-audit/check-journal-start-capture.ts');
const sourcePins=await Promise.all(files.map(async path=>({path,sha256:new Bun.CryptoHasher('sha256').update(await Bun.file(path).text()).digest('hex')})));
await Bun.write('docs/helix/04-build/evidence/design-audit/journal-start-capture-audit.json',JSON.stringify({scope:'private start-capture shape with original context references only; empty/duplicate/foreign/kind/custody meanings require actual semantic admission',bunVersion:Bun.version,sourcePins,outcomes,nativeExecuted:false,adopted:false},null,2)+'\n');
console.log(JSON.stringify({cases:outcomes.length,passed:true,nativeExecuted:false,adopted:false}));
