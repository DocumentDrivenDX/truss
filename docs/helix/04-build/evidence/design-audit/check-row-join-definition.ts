/** Closed join shape only. No physical identity resolution or native support. */
const {default:Ajv}=await import(process.argv[2]); const a=new Ajv({strict:true});
const base='docs/helix/02-design/contracts/';
for(const f of new Bun.Glob('*.schema.json').scanSync(base))a.addSchema(await Bun.file(base+f).json());
const file='truss-row-join-definition-v0.1.proposal.schema.json';
const schema=await Bun.file(base+file).json();
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const pin={identity:'fixture-profile',version:'0.1.0',sha256:'b'.repeat(64)};
function fixture():any {
 const x:any={};
 for(const [k,v] of Object.entries(schema.properties) as [string,any][]){
  if(v.const)x[k]=v.const;
  else if(v.$ref)x[k]=k==='profile'?pin:artifact;
 }
 x.recordKind='object'; delete x.edgeAssociationDefinition;
 x.owner={relationPhysicalIdentity:'object',relationName:'object',idColumnPhysicalIdentity:'object.id',discriminatorColumnPhysicalIdentity:'object.type_id'};
 for(const k of ['state','node','scalar']) {
  const d=schema.properties[k];const name=d.properties.relationName.const;
  x[k]={relationPhysicalIdentity:name,relationName:name,columns:Object.fromEntries(Object.keys(d.properties.columns.properties).map(c=>[c,name+'.'+c]))};
 }
 x.ownerJoin='object-id-and-type';x.constraintEvidence=[artifact];return x;
}
const v=a.getSchema(schema.$id)!;
const cases:[string,(x:any)=>void,boolean][]=[
 ['object join',()=>{},true],
 ['edge independent association',x=>{x.recordKind='edge';x.owner.relationName='edge';x.ownerJoin='edge-id-and-relationship';x.edgeAssociationDefinition=artifact;},true],
 ['edge association missing',x=>{x.recordKind='edge';x.owner.relationName='edge';x.ownerJoin='edge-id-and-relationship';},false],
 ['object association forbidden',x=>{x.edgeAssociationDefinition=artifact;},false],
 ['owner join mismatched',x=>{x.ownerJoin='edge-id-and-relationship';},false],
 ['owner relation mismatched',x=>{x.owner.relationName='edge';},false],
 ['raw SQL forbidden',x=>{x.sql='SELECT 1';},false],
 ['column missing',x=>{delete x.state.columns.property_owner_type_id;},false],
 ['optional absence collapsed',x=>{x.optionalAbsence='sql-null';},false],
 ['null payload demanded',x=>{x.nullRoot='requires-scalar-payload';},false],
 ['multiplicity changed',x=>{x.ownerMultiplicity='distinct-owner';},false],
 ['evidence empty',x=>{x.constraintEvidence=[];},false],
 ['foreign column IDs require semantic refusal',x=>{x.state.columns.property_id='unrelated.column';},true],
 ['unknown stored domain requires semantic refusal',x=>{x.storedDomainDefinition={...artifact,identity:'unknown'};},true]
];
const observations=cases.map(([name,mutate,expected])=>{const x=fixture();mutate(x);return {name,expected,actual:Boolean(v(x))};});
const failures=observations.filter(x=>x.actual!==x.expected);
await Bun.write('docs/helix/04-build/evidence/design-audit/row-join-definition-shapes.json',JSON.stringify({scope:'Closed join body shape only; original physical/profile/association and native integrity admission untested',bunVersion:Bun.version,source:{path:file,sha256:new Bun.CryptoHasher('sha256').update(await Bun.file(base+file).arrayBuffer()).digest('hex')},observations,failures},null,2)+'\n');
console.log(JSON.stringify({cases:cases.length,failures}));if(failures.length)process.exit(1);export {};
