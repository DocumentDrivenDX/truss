/** Nested graph/presence/context shape evidence, not interpreter qualification. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
for(const f of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))a.addSchema(await Bun.file('docs/helix/02-design/contracts/'+f).json());
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const pin={identity:'fixture-profile',version:'0.1.0',sha256:'b'.repeat(64)};
const identity={documentId:'d',revision:'r',module:'m',element:'e'};
const node=(nodeId:string,shape:unknown)=>({nodeId,authoredIdentity:{...identity,element:nodeId},authoredDefinition:artifact,codecProfile:pin,codecDefinition:artifact,shape});
const graph={interfaceVersion:'truss-value-definition/0.1.0',profile:pin,rootNodeId:'structured',acceptedDefinition:artifact,nodes:[node('structured',{kind:'structured',recordNodeId:'record'}),node('record',{kind:'record',members:[{fieldIdentity:identity,storedMemberName:'1',valueNodeId:'sequence',presenceDefinition:artifact}]}),node('sequence',{kind:'sequence',itemNodeId:'map'}),node('map',{kind:'map',itemNodeId:'scalar'}),node('scalar',{kind:'scalar',family:'string',storageRepresentation:'json-string'})]};
const presence={interfaceVersion:'truss-presence-definition/0.1.0',profile:pin,carrierSchema:'urn:truss:draft:exact-value:0.1.0#/$defs/presence',storageRoot:'nonnull-jsonb-object',absentMember:'present-false',jsonNullMember:'present-null-if-authored-nullable',emptyCollection:'present-empty-typed-value',sqlNullRoot:'integrity-refusal',nativeNullValue:'unsupported-without-separate-profile',defaultApplication:'none-on-read',acceptedDefinition:artifact};
const context={interfaceVersion:'truss-read-context-definition/0.1.0',profile:pin,contextSchema:'urn:truss:draft:direct-cursor:0.1.0#/$defs/context',allowedConsistency:['live','held_snapshot'],catalogAdmission:'original-binding-matches-admitted-view',layoutAdmission:'original-physical-and-encoding-profiles-match',authorityAdmission:'actual-current-role-and-effective-policy',transactionAdmission:'executor-issued-live-affine-context',snapshotAdmission:'original-registry-custody-and-retained-stores',publicationAdmission:'complete-result-current-disclosure-and-resource-check',onMismatch:'refuse-before-sql',resourceProfile:pin,resourceDefinition:artifact,requiredHostObligations:['fixture-obligation']};
const gv=a.getSchema('urn:truss:draft:value-definition:0.1.0')!,pv=a.getSchema('urn:truss:draft:presence-definition:0.1.0')!,cv=a.getSchema('urn:truss:draft:read-context-definition:0.1.0')!;
const cases:[string,Function,unknown,boolean][]=[
 ['structured record sequence map scalar graph',gv,graph,true],
 ['structured record reference missing',gv,{...graph,nodes:[node('structured',{kind:'structured'})]},false],
 ['unknown shape',gv,{...graph,nodes:[node('x',{kind:'native-anything'})]},false],
 ['missing graph reference requires semantic refusal',gv,{...graph,rootNodeId:'absent'},true],
 ['duplicate nodes require semantic refusal',gv,{...graph,nodes:[...graph.nodes,graph.nodes[0]]},true],
 ['presence definition',pv,presence,true],
 ['absence collapsed to null',pv,{...presence,absentMember:'present-null'},false],
 ['read default injected',pv,{...presence,defaultApplication:'apply-on-read'},false],
 ['native null advertised',pv,{...presence,nativeNullValue:'supported'},false],
 ['read context',cv,context,true],
 ['snapshot authority frozen',cv,{...context,authorityAdmission:'snapshot-grants'},false],
 ['serialized transaction',cv,{...context,transactionHandle:'caller-handle'},false],
 ['no consistency mode',cv,{...context,allowedConsistency:[]},false],
 ['unknown obligation requires semantic refusal',cv,{...context,requiredHostObligations:['unknown']},true]
];
const observations=cases.map(([name,v,x,expected])=>({name,expected,actual:Boolean(v(x))}));const failures=observations.filter(x=>x.expected!==x.actual);
const sourcePins=await Promise.all(['truss-value-definition-v0.1.proposal.schema.json','truss-presence-definition-v0.1.proposal.schema.json','truss-read-context-definition-v0.1.proposal.schema.json'].map(async path=>({path,sha256:new Bun.CryptoHasher('sha256').update(await Bun.file('docs/helix/02-design/contracts/'+path).arrayBuffer()).digest('hex')})));
await Bun.write('docs/helix/04-build/evidence/design-audit/binding-definition-shapes.json',JSON.stringify({scope:'Nested shape controls only; unresolved references, duplicate nodes and unknown obligations intentionally demonstrate missing semantic authority',bunVersion:Bun.version,sourcePins,observations,failures},null,2)+'\n');
console.log(JSON.stringify({cases:cases.length,failures}));if(failures.length)process.exit(1);export {};
