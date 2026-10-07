/** Candidate serialization experiment only; not production identity admission. */
const root='docs/helix/04-build/evidence/design-audit/record-identity-oracle';
const fixtureText=await Bun.file(root+'/fixtures.json').text();
const profileText=await Bun.file('docs/helix/02-design/contracts/bindings/record-field-identity-encoding-v0.1.proposal.json').text();
const profile=JSON.parse(profileText),fixture=JSON.parse(fixtureText);
const hash=(text:string)=>new Bun.CryptoHasher('sha256').update(text).digest('hex');
const keys=['documentId','element','module','revision'];
if(JSON.stringify(profile.serializedMemberOrder)!==JSON.stringify(keys))throw Error('profile order changed');
const observations=[];
for(const row of fixture.cases){
 const input=row.identity;
 if(Object.keys(input).length!==4||keys.some(key=>typeof input[key]!=='string'))throw Error('fixture identity shape');
 const serialized=JSON.stringify({documentId:input.documentId,element:input.element,module:input.module,revision:input.revision});
 const bytes=new TextEncoder().encode(serialized);
 const hex=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
 if(serialized!==row.expectedText||hex!==row.expectedUtf8Hex)throw Error('independent bytes disagree: '+row.id);
 observations.push({id:row.id,actualUtf8Hex:hex,expectedUtf8Hex:row.expectedUtf8Hex});
}
if(await Bun.file(root+'/fixtures.json').text()!==fixtureText||await Bun.file('docs/helix/02-design/contracts/bindings/record-field-identity-encoding-v0.1.proposal.json').text()!==profileText)throw Error('original fixture/profile changed');
await Bun.write('docs/helix/04-build/evidence/design-audit/record-identity-json-candidate.json',JSON.stringify({scope:'Observed fixed-order TypeScript JSON serialization against three independent byte fixtures only; not original source/identity validation, complete escaping/resource profile, Rust/compiler feature composition, native storage or adoption',bunVersion:Bun.version,profileSha256:hash(profileText),fixtureSha256:hash(fixtureText),observations,rustOracleExecuted:false,nativeExecution:false,adopted:false},null,2)+'\n');
console.log(JSON.stringify({cases:observations.length,rustOracleExecuted:false,nativeExecution:false,adopted:false}));
