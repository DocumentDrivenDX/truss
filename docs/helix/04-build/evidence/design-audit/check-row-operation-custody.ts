/** Operation manifest shape controls; original native custody/coverage untested. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
const base='docs/helix/02-design/contracts/';for(const f of new Bun.Glob('*.schema.json').scanSync(base))a.addSchema(await Bun.file(base+f).json());
const path='truss-row-operation-custody-v0.1.proposal.schema.json';const schema=await Bun.file(base+path).json(),v=a.getSchema(schema.$id)!;
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)},pin={identity:'fixture-profile',version:'0.1.0',sha256:'b'.repeat(64)};
const operation=(ordinal:string)=>({ordinal,operationIdentity:'operation-'+ordinal,operationKind:'mutation',originalOperationDefinition:artifact,originalInput:artifact,originalPrestate:artifact,admittedCandidate:artifact,nativeGroupCustodyIdentity:'group-'+ordinal,effectObligationDefinition:artifact});
const fixture=()=>({interfaceVersion:'truss-row-operation-custody/0.1.0',profile:pin,originalLayout:artifact,originalHome:artifact,originalOwnerProperty:artifact,operations:[operation('0'),operation('1')],groupResolution:'original-native-effects-readiness-before-seal',completionEvidence:'resolved-independently-not-embedded-future-digest',transactionAuthority:'actual-native-touch-context-not-caller-manifest'} as any);
const cases:[string,(x:any)=>void,boolean][]=[
 ['two ordered contributions',()=>{},true],
 ['catalog acceptance row contribution shape',x=>{x.operations[0].operationKind='catalog-acceptance';},true],
 ['missing original prestate',x=>{delete x.operations[0].originalPrestate;},false],
 ['empty contribution list',x=>{x.operations=[];},false],
 ['future group digest',x=>{x.operations[0].groupDigest='a'.repeat(64);},false],
 ['caller transaction identity',x=>{x.transactionId='1';},false],
 ['committed receipt required before seal',x=>{x.groupResolution='committed-receipt-before-seal';},false],
 ['completion asserted by manifest',x=>{x.completionEvidence='already-complete';},false],
 ['unknown operation kind',x=>{x.operations[0].operationKind='raw-sql';},false],
 ['noncanonical ordinal',x=>{x.operations[0].ordinal='01';},false],
 ['duplicate operations require semantic refusal',x=>{x.operations[1]=x.operations[0];},true],
 ['reordered operations require semantic refusal',x=>{x.operations.reverse();},true],
 ['unknown native group requires semantic refusal',x=>{x.operations[0].nativeGroupCustodyIdentity='unknown';},true]
];
const contextPath='truss-row-operation-context-v0.1.proposal.schema.json';
const contextSchema=await Bun.file(base+contextPath).json(),cv=a.getSchema(contextSchema.$id)!;
const contextFixture=()=>{
 const x:any={};for(const [name,rule] of Object.entries(contextSchema.properties) as [string,any][]){
  x[name]=rule.const??(rule.$ref?(name==='profile'?pin:artifact):name==='originalWriterXid'?'7':name==='operationOrdinal'?'0':'fixture-installation');
 }return x;
};
const contextCases:[string,(x:any)=>void,boolean][]=[
 ['original native context shape',()=>{},true],
 ['original acting role missing',x=>{delete x.originalActingRoleContext;},false],
 ['caller authority advertised',x=>{x.authority='caller-context';},false],
 ['committed context advertised',x=>{x.durability='committed';},false],
 ['numeric native xid',x=>{x.originalWriterXid=7;},false],
 ['noncanonical native ordinal',x=>{x.operationOrdinal='00';},false],
 ['foreign installation requires semantic refusal',x=>{x.installationIdentity='foreign';},true],
 ['ordinal beyond bigint requires semantic refusal',x=>{x.operationOrdinal='9223372036854775808';},true]
];
const observations=[...cases.map(([name,mutate,expected])=>{const x=fixture();mutate(x);return {name,expected,actual:Boolean(v(x))};}),...contextCases.map(([name,mutate,expected])=>{const x=contextFixture();mutate(x);return {name,expected,actual:Boolean(cv(x))};})];const failures=observations.filter(x=>x.actual!==x.expected);
const sourcePins=await Promise.all([path,contextPath].map(async path=>({path,sha256:new Bun.CryptoHasher('sha256').update(await Bun.file(base+path).arrayBuffer()).digest('hex')})));
await Bun.write('docs/helix/04-build/evidence/design-audit/row-operation-custody-shapes.json',JSON.stringify({scope:'Decoded manifest/context closed shape only; duplicate/order/native custody/range/artifact correspondence intentionally require semantic admission',bunVersion:Bun.version,sourcePins,observations,failures},null,2)+'\n');console.log(JSON.stringify({cases:observations.length,failures}));if(failures.length)process.exit(1);export {};
