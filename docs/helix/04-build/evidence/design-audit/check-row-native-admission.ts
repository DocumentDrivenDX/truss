/** Native admission shape only; actual allocator/custody correspondence is not tested. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
const base='docs/helix/02-design/contracts/';for(const f of new Bun.Glob('*.schema.json').scanSync(base))a.addSchema(await Bun.file(base+f).json());
const path='truss-row-native-admission-v0.1.proposal.schema.json',schema=await Bun.file(base+path).json(),v=a.getSchema(schema.$id)!;
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)},pin={identity:'fixture-profile',version:'0.1.0',sha256:'b'.repeat(64)};
const fixture=()=>{const x:any={};for(const [name,rule] of Object.entries(schema.properties) as [string,any][]){if(name==='originalRequestAdmission')continue;x[name]=rule.const??(rule.$ref?(name==='profile'?pin:artifact):name==='invocationKind'?'mutation-group':name==='requestParticipation'?'none':name==='orderedCommandDefinitions'?[artifact]:[]);}return x;};
const row=()=>({ownerKind:'object',ownerLocator:{kind:'creation-alias',aliasIdentity:'new-owner',originalAliasDefinition:artifact},ownerDiscriminatorId:'1',propertyOwnerTypeId:'1',propertyId:'2',originalOwnerProperty:artifact,originalHome:artifact,originalPrestate:artifact,admittedCandidate:artifact} as any);
const cases:[string,(x:any)=>void,boolean][]=[
 ['request-free no-row shape',()=>{},true],
 ['creation alias before allocation',x=>{x.orderedRequiredRowScopes=[row()];},true],
 ['existing native owner',x=>{const r=row();r.ownerLocator={kind:'existing-native',ownerId:'7'};x.orderedRequiredRowScopes=[r];},true],
 ['mixed alias and persistent ID',x=>{const r=row();r.ownerLocator.ownerId='7';x.orderedRequiredRowScopes=[r];},false],
 ['missing original alias definition',x=>{const r=row();delete r.ownerLocator.originalAliasDefinition;x.orderedRequiredRowScopes=[r];},false],
 ['empty alias identity',x=>{const r=row();r.ownerLocator.aliasIdentity='';x.orderedRequiredRowScopes=[r];},false],
 ['request-free with receipt admission',x=>{x.originalRequestAdmission=artifact;},false],
 ['request present without admission',x=>{x.requestParticipation='present';},false],
 ['request present with admission',x=>{x.requestParticipation='present';x.originalRequestAdmission=artifact;},true],
 ['empty command list',x=>{x.orderedCommandDefinitions=[];},false],
 ['future seal field',x=>{x.sealDigest='a'.repeat(64);},false],
 ['foreign alias requires semantic refusal',x=>{const r=row();r.ownerLocator.aliasIdentity='foreign';x.orderedRequiredRowScopes=[r];},true],
 ['duplicate scope requires semantic refusal',x=>{x.orderedRequiredRowScopes=[row(),row()];},true]
];
const observations=cases.map(([name,mutate,expected])=>{const x=fixture();mutate(x);return {name,expected,actual:Boolean(v(x))};}),failures=observations.filter(x=>x.actual!==x.expected);
await Bun.write('docs/helix/04-build/evidence/design-audit/row-native-admission-shapes.json',JSON.stringify({scope:'Decoded closed shape only; no artifact/alias allocation/order/complete scope/native authority proof',bunVersion:Bun.version,sourcePin:{path,sha256:new Bun.CryptoHasher('sha256').update(await Bun.file(base+path).arrayBuffer()).digest('hex')},observations,failures},null,2)+'\n');console.log(JSON.stringify({cases:observations.length,failures}));if(failures.length)process.exit(1);export {};
