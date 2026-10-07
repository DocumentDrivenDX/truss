/** Existing v0.2 manifest schema reuse; structural evidence only. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
const root='docs/helix/02-design/contracts/';
for await(const file of new Bun.Glob('*.schema.json').scan(root))ajv.addSchema(await Bun.file(root+file).json());
const check=ajv.getSchema('urn:truss:draft:feed-transaction:0.2.0')!;
const vectors=await Bun.file(root+'bindings/feed-manifest-canonical.proposal.vectors.json').json();
const vector=vectors.vectors.find((v:any)=>v.domain==='truss-feed-manifest/0.2.0');
const original=JSON.parse(vector.completeWireCanonicalToken);const cases:any[]=[];
function probe(name:string,expected:boolean,mutate:(v:any)=>void){const v=structuredClone(original);mutate(v);const actual=Boolean(check(v));if(actual!==expected)throw new Error(name+': '+JSON.stringify(check.errors));cases.push({name,shapeAccepted:actual,requiresSemanticAdmission:actual});}
probe('complete canonical original v0.2 shape',true,()=>{});
probe('digest-excluded private tree is incomplete wire',false,v=>delete v.manifestSha256);
probe('foreign manifest interface version',false,v=>v.interfaceVersion='truss-feed-transaction/0.1.0');
probe('host-number xid',false,v=>v.xid=9007199254740992);
probe('missing configuration prerequisites',false,v=>delete v.configurationPrerequisites);
probe('unknown outer member',false,v=>v.nativeExtra='unadmitted');
probe('direct artifact hash substituted for semantic digest remains shape valid',true,v=>v.manifestSha256=vector.completeWireArtifactSha256);
probe('wrong original payload hash remains shape valid',true,v=>v.members[0].payloadSha256='2'.repeat(64));
for(const v of vectors.vectors.filter((v:any)=>v.domain==='truss-feed-manifest/0.2.0')){if(!check(JSON.parse(v.completeWireCanonicalToken)))throw new Error(v.id+': '+JSON.stringify(check.errors));cases.push({name:v.id+' original full envelope',shapeAccepted:true,requiresSemanticAdmission:true});}
const schemaBytes=await Bun.file(root+'feed-transaction-v0.2.schema.json').arrayBuffer();
const sha=(bytes:ArrayBuffer)=>new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
await Bun.write('docs/helix/04-build/evidence/design-audit/feed-manifest-archive-shapes.json',JSON.stringify({scope:'Existing v0.2 manifest schema correspondence; no archive/profile/native custody or semantic admission',schemaSha256:sha(schemaBytes),vectorsSha256:sha(await Bun.file(root+'bindings/feed-manifest-canonical.proposal.vectors.json').arrayBuffer()),cases,nativeExecution:false,complete:false},null,2)+'\n');
console.log(JSON.stringify({cases:cases.length,nativeExecution:false,complete:false}));
