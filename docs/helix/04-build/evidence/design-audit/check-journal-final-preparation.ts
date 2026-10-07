/** Final preparation shape only; no independent native state/candidate/manifest authority. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
const base='docs/helix/02-design/contracts/';for(const f of new Bun.Glob('*.schema.json').scanSync(base))a.addSchema(await Bun.file(base+f).json());
const v=a.getSchema('urn:truss:proposal:journal-final-preparation:0.2.0')!;
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)},pin={identity:'fixture',version:'0.1.0',sha256:'b'.repeat(64)};
const context={interfaceVersion:'truss-row-operation-context/0.1.0',profile:pin,installationIdentity:'installation',originalInstallation:artifact,originalLayout:artifact,originalResourceProfile:artifact,originalWriterXid:'7',operationOrdinal:'0',originalOperationDefinition:artifact,originalExecutionContext:artifact,originalActingRoleContext:artifact,originalCatalogAuthorityCut:artifact,originalOwnerUnion:artifact,originalGroupAdmission:artifact,addressDomain:'truss-row-operation-address/0.1.0',authority:'actual-protected-native-registry-correspondence',durability:'transaction-local-until-original-commit-observation'};
const identity={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'doc',moduleId:'module'}};

const before={interfaceVersion:'truss-history-record/0.1.0',identity:structuredClone(identity),recordVersion:'1',catalogRevision:'1',createdAt:'fixture',updatedAt:'fixture',properties:[],retained:[],kind:'object',ownership:{state:'rootless'}};
const after={...structuredClone(before),recordVersion:'2'};
const state=(record:any)=>({state:'present',record:structuredClone(record)});
const fixture=()=>({interfaceVersion:'truss-journal-final-preparation/0.2.0-proposal',producerProfile:pin,originalOperationContext:structuredClone(context),originalStartCapture:structuredClone(artifact),completeEffectInventory:structuredClone(artifact),origin:{asserted:{kind:'null'},databaseRole:'role'},entities:[{identity:structuredClone(identity),kind:'object',changed:true,recordVersion:'2',start:state(before),candidateFinal:state(after),observedFinal:state(after),originalDefinitionContext:structuredClone(artifact),completeNativeFinalEvidence:structuredClone(artifact),siblingOrdinals:['0']}],siblings:[{ordinal:'0',identity:structuredClone(identity),kind:'object',recordVersion:'2',catalogRevision:'1',originalSemanticEvidence:structuredClone(artifact),payload:{operation:'metadata',before:structuredClone(before),after:structuredClone(after)}}]}) as any;
const cases:[string,(x:any)=>void,boolean][]=[
 ['complete boundary shape',()=>{},true],
 ['unchanged boundary requires native no-effect proof',x=>{const e=x.entities[0];e.changed=false;e.recordVersion='1';e.candidateFinal=state(before);e.observedFinal=state(before);e.siblingOrdinals=[];x.siblings=[];},true],
 ['empty scope requires independent completeness',x=>{x.entities=[];x.siblings=[];},true],
 ['missing original capture',x=>{delete x.originalStartCapture;},false],
 ['missing full effect inventory',x=>{delete x.completeEffectInventory;},false],
 ['missing independent final',x=>{delete x.entities[0].observedFinal;},false],
 ['missing candidate final',x=>{delete x.entities[0].candidateFinal;},false],
 ['changed boundary missing sibling membership',x=>{x.entities[0].siblingOrdinals=[];},false],
 ['unchanged boundary with sibling membership',x=>{x.entities[0].changed=false;},false],
 ['future allocated position',x=>{x.siblings[0].seq='1';},false],
 ['future position inside payload',x=>{x.siblings[0].payload.seq='1';},false],
 ['future group digest',x=>{x.mutationGroup={};},false],
 ['candidate-final disagreement needs semantic refusal',x=>{x.entities[0].observedFinal.record.recordVersion='3';},true],
 ['missing required entity needs semantic refusal',x=>{x.entities=[];},true],
 ['missing actual sibling needs semantic refusal',x=>{x.siblings=[];},true],
 ['duplicate original sibling needs semantic refusal',x=>{x.siblings.push(structuredClone(x.siblings[0]));},true],
 ['wrong original membership needs semantic refusal',x=>{x.entities[0].siblingOrdinals=['1'];},true]
];
const outcomes=cases.map(([name,mutate,expected])=>{const x=fixture();mutate(x);const actual=Boolean(v(x));if(actual!==expected)throw Error(name+' '+JSON.stringify(v.errors));return {name,expected,actual};});
const paths=['journal-final-preparation-v0.2.proposal.schema.json','journal-start-capture-v0.2.proposal.schema.json','history-event-v0.2.proposal.schema.json','history-retain-payload-v0.1.proposal.schema.json','truss-row-operation-context-v0.1.proposal.schema.json','history-record-v0.1.schema.json','exact-value-v0.1.schema.json','acceptance-input-v0.1.schema.json'].map(n=>base+n);
paths.push('docs/helix/04-build/evidence/design-audit/check-journal-final-preparation.ts');
const sourcePins=await Promise.all(paths.map(async path=>({path,sha256:new Bun.CryptoHasher('sha256').update(await Bun.file(path).text()).digest('hex')})));
await Bun.write('docs/helix/04-build/evidence/design-audit/journal-final-preparation-audit.json',JSON.stringify({scope:'private pre-reservation boundary/sibling shape controls only; native completeness/parity/context/authority/resource untested',bunVersion:Bun.version,sourcePins,outcomes,nativeExecuted:false,adopted:false},null,2)+'\n');
console.log(JSON.stringify({cases:outcomes.length,passed:true,nativeExecuted:false,adopted:false}));
