/** Ordered transition shape only; no actual native effect/ordinal/custody evidence. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
const base='docs/helix/02-design/contracts/';for(const f of new Bun.Glob('*.schema.json').scanSync(base))a.addSchema(await Bun.file(base+f).json());
const v=a.getSchema('urn:truss:proposal:journal-ordered-transition:0.2.0')!;
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)},pin={identity:'fixture',version:'0.1.0',sha256:'b'.repeat(64)};
const context={interfaceVersion:'truss-row-operation-context/0.1.0',profile:pin,installationIdentity:'installation',originalInstallation:artifact,originalLayout:artifact,originalResourceProfile:artifact,originalWriterXid:'7',operationOrdinal:'0',originalOperationDefinition:artifact,originalExecutionContext:artifact,originalActingRoleContext:artifact,originalCatalogAuthorityCut:artifact,originalOwnerUnion:artifact,originalGroupAdmission:artifact,addressDomain:'truss-row-operation-address/0.1.0',authority:'actual-protected-native-registry-correspondence',durability:'transaction-local-until-original-commit-observation'};
const identity={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'doc',moduleId:'module'}};

const absent={present:false},present={present:true,value:{kind:'null'}};
const deltas=[
 {operation:'property',propertyId:'1',definitionPin:'fixture',before:absent,after:present},
 {operation:'transform',propertyId:'1',beforeDefinitionPin:'before',afterDefinitionPin:'after',before:absent,after:present},
 {operation:'rebind',retainedName:'a',propertyId:'1',beforeDefinitionContext:'before',afterDefinitionPin:'after',retainedBefore:present,retainedAfter:absent,propertyBefore:absent,propertyAfter:present},
 {operation:'retain',retainedChanges:[{retainedName:'a',before:absent,after:present,beforeDefinitionContext:'before',afterDefinitionContext:'after',sourceContext:'source'}]}
];
const fixture=(delta:any)=>structuredClone({interfaceVersion:'truss-journal-ordered-transition/0.2.0-proposal',producerProfile:pin,originalOperationContext:context,identity,kind:'object',targetRecordVersion:'2',effectOrdinal:'0',originalEffectEvidence:structuredClone(artifact),nativeTransitionEvidence:structuredClone(artifact),delta}) as any;
const outcomes:any[]=[];
for(const delta of deltas){const x=fixture(delta);if(!v(x))throw Error(delta.operation+' '+JSON.stringify(v.errors));outcomes.push({name:delta.operation,passed:true});}
const cases:[string,(x:any)=>void,boolean][]=[
 ['missing original evidence',x=>{delete x.originalEffectEvidence;},false],
 ['missing native transition',x=>{delete x.nativeTransitionEvidence;},false],
 ['numeric effect ordinal',x=>{x.effectOrdinal=0;},false],
 ['noncanonical effect ordinal',x=>{x.effectOrdinal='00';},false],
 ['future journal seq',x=>{x.seq='1';},false],
 ['future seq inside delta',x=>{x.delta.seq='1';},false],
 ['future manifest inside delta',x=>{x.delta.mutationGroup={};},false],
 ['metadata is a later boundary witness',x=>{x.delta={operation:'metadata'};},false],
 ['caller origin override',x=>{x.origin={};},false],
 ['substituted effect evidence needs semantic refusal',x=>{x.originalEffectEvidence.identity='foreign';},true],
 ['unknown target identity needs semantic refusal',x=>{x.identity.id='2';},true]
];
for(const [name,mutate,expected] of cases){const x=fixture(deltas[0]);mutate(x);const actual=Boolean(v(x));if(actual!==expected)throw Error(name+' '+JSON.stringify(v.errors));outcomes.push({name,expected,actual});}
const paths=['journal-ordered-transition-v0.2.proposal.schema.json','history-event-v0.2.proposal.schema.json','history-retain-payload-v0.1.proposal.schema.json','truss-row-operation-context-v0.1.proposal.schema.json','history-record-v0.1.schema.json','exact-value-v0.1.schema.json','acceptance-input-v0.1.schema.json'].map(n=>base+n);
paths.push('docs/helix/04-build/evidence/design-audit/check-journal-ordered-transition.ts');
const sourcePins=await Promise.all(paths.map(async path=>({path,sha256:new Bun.CryptoHasher('sha256').update(await Bun.file(path).text()).digest('hex')})));
await Bun.write('docs/helix/04-build/evidence/design-audit/journal-ordered-transition-audit.json',JSON.stringify({scope:'four delta variant and eleven custody/phase shape controls only; native effects/ordinal/source/context/version completeness untested',bunVersion:Bun.version,sourcePins,outcomes,nativeExecuted:false,adopted:false},null,2)+'\n');
console.log(JSON.stringify({cases:outcomes.length,passed:true,nativeExecuted:false,adopted:false}));
