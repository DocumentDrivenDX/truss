/** Reserved position shape only; actual native allocator/complete prepared mapping untested. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
const base='docs/helix/02-design/contracts/';for(const f of new Bun.Glob('*.schema.json').scanSync(base))a.addSchema(await Bun.file(base+f).json());
const v=a.getSchema('urn:truss:proposal:journal-reserved-positions:0.2.0')!;
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)},pin={identity:'fixture',version:'0.1.0',sha256:'b'.repeat(64)};
const context={interfaceVersion:'truss-row-operation-context/0.1.0',profile:pin,installationIdentity:'installation',originalInstallation:artifact,originalLayout:artifact,originalResourceProfile:artifact,originalWriterXid:'7',operationOrdinal:'0',originalOperationDefinition:artifact,originalExecutionContext:artifact,originalActingRoleContext:artifact,originalCatalogAuthorityCut:artifact,originalOwnerUnion:artifact,originalGroupAdmission:artifact,addressDomain:'truss-row-operation-address/0.1.0',authority:'actual-protected-native-registry-correspondence',durability:'transaction-local-until-original-commit-observation'};
const identity={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'doc',moduleId:'module'}};

const entry=(ordinal:string,seq:string)=>({ordinal,identity:structuredClone(identity),kind:'object',recordVersion:'2',seq,originalAllocationEvidence:structuredClone(artifact)});
const fixture=()=>({interfaceVersion:'truss-journal-reserved-positions/0.2.0-proposal',producerProfile:pin,allocationProfile:pin,originalOperationContext:structuredClone(context),originalPrepared:structuredClone(artifact),mapping:[entry('0','41'),entry('1','43')]}) as any;
const cases:[string,(x:any)=>void,boolean][]=[
 ['nonconsecutive native positions shape',()=>{},true],
 ['empty mapping requires complete empty prepared scope',x=>{x.mapping=[];},true],
 ['int8 maximum shape still needs native allocation',x=>{x.mapping[1].seq='9223372036854775807';},true],
 ['missing original preparation',x=>{delete x.originalPrepared;},false],
 ['missing allocation evidence',x=>{delete x.mapping[0].originalAllocationEvidence;},false],
 ['numeric sequence',x=>{x.mapping[0].seq=41;},false],
 ['zero sequence',x=>{x.mapping[0].seq='0';},false],
 ['noncanonical ordinal',x=>{x.mapping[0].ordinal='00';},false],
 ['group digest before append',x=>{x.orderedEventDigest='0'.repeat(64);},false],
 ['commit assertion',x=>{x.committed=true;},false],
 ['skipped original sibling needs semantic refusal',x=>{x.mapping[1].ordinal='2';},true],
 ['duplicate reserved position needs semantic refusal',x=>{x.mapping[1].seq='41';},true],
 ['decreasing position needs semantic refusal',x=>{x.mapping[1].seq='40';},true],
 ['substituted group version needs semantic refusal',x=>{x.mapping[1].recordVersion='3';},true],
 ['int8 overflow needs native-domain refusal',x=>{x.mapping[1].seq='9223372036854775808';},true]
];
const outcomes=cases.map(([name,mutate,expected])=>{const x=fixture();mutate(x);const actual=Boolean(v(x));if(actual!==expected)throw Error(name+' '+JSON.stringify(v.errors));return {name,expected,actual};});
const paths=['journal-reserved-positions-v0.2.proposal.schema.json','truss-row-operation-context-v0.1.proposal.schema.json','history-record-v0.1.schema.json','exact-value-v0.1.schema.json','acceptance-input-v0.1.schema.json'].map(n=>base+n);paths.push('docs/helix/04-build/evidence/design-audit/check-journal-reserved-positions.ts');
const sourcePins=await Promise.all(paths.map(async path=>({path,sha256:new Bun.CryptoHasher('sha256').update(await Bun.file(path).text()).digest('hex')})));
await Bun.write('docs/helix/04-build/evidence/design-audit/journal-reserved-positions-audit.json',JSON.stringify({scope:'private reserved-mapping shape only; actual allocation, uniqueness/order/native ranges and complete prepared-sibling correspondence require semantic admission',bunVersion:Bun.version,sourcePins,outcomes,nativeExecuted:false,adopted:false},null,2)+'\n');
console.log(JSON.stringify({cases:outcomes.length,passed:true,nativeExecuted:false,adopted:false}));
