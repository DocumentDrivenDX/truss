import {test,expect} from 'bun:test';
import {decodeAcceptanceJson,AcceptanceJsonError} from '../packages/postgresql/src/acceptance-json';
const corpus=await Bun.file('docs/helix/03-test/acceptance-outer-json-expected.proposal.json').json();
for(const c of corpus.cases)test(c.name,()=>{
 const bytes=Uint8Array.from(Buffer.from(c.utf8Hex,'hex'));
 expect(new Bun.CryptoHasher('sha256').update(bytes).digest('hex')).toBe(c.sourceSha256);
 if(c.expected.status==='decoded'){const value=decodeAcceptanceJson(bytes);expect(JSON.stringify(value)).toBe(JSON.stringify(c.expected.value));if(c.name==='inert prototype name')expect(Object.getPrototypeOf(value)).toBe(null)}
 else{let failure:unknown;try{decodeAcceptanceJson(bytes)}catch(e){failure=e}expect(failure).toBeInstanceOf(AcceptanceJsonError);expect((failure as AcceptanceJsonError).reason).toBe(c.expected.reason)}
});
test('complete original input fixture preserves all native and converted custody',async()=>{
 const fixture=await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json();
 const bytes=new TextEncoder().encode(JSON.stringify(fixture.input));
 expect(JSON.stringify(decodeAcceptanceJson(bytes))).toBe(JSON.stringify(fixture.input));
 expect(bytes.length).toBe(fixture.expected.canonicalTreeBytes);
});
test('selected depth and container limits refuse before an over-limit output',()=>{
 const decode=(text:string)=>decodeAcceptanceJson(new TextEncoder().encode(text));
 expect(decode('['.repeat(129)+']'.repeat(129))).toBeDefined();
 expect(()=>decode('['.repeat(130)+']'.repeat(130))).toThrow(AcceptanceJsonError);
 expect((decode('['+Array(4096).fill('null').join(',')+']') as unknown[]).length).toBe(4096);
 expect(()=>decode('['+Array(4097).fill('null').join(',')+']')).toThrow(AcceptanceJsonError);
});
test('raw byte and cumulative duplicate-name work are conjunctive ceilings',()=>{
 const large=new Uint8Array(1048577);expect(()=>decodeAcceptanceJson(large)).toThrow(AcceptanceJsonError);
 const keys=Array.from({length:1000},(_,i)=>JSON.stringify('key-'+i.toString().padStart(5,'0'))+':null');
 let failure:unknown;try{decodeAcceptanceJson(new TextEncoder().encode('{'+keys.join(',')+'}'))}catch(e){failure=e}
 expect(failure).toBeInstanceOf(AcceptanceJsonError);expect((failure as AcceptanceJsonError).reason).toBe('resource');
});
test('exact node ceiling counts containers and every scalar occurrence',()=>{
 const make=(last:number)=>'['+Array.from({length:25},(_,i)=>'['+Array(i===24?last:3999).fill('null').join(',')+']').join(',')+']';
 expect((decodeAcceptanceJson(new TextEncoder().encode(make(3998))) as unknown[]).length).toBe(25);
 let failure:unknown;try{decodeAcceptanceJson(new TextEncoder().encode(make(3999)))}catch(e){failure=e}
 expect(failure).toBeInstanceOf(AcceptanceJsonError);expect((failure as AcceptanceJsonError).reason).toBe('resource');
});
