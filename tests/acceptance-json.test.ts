import {test,expect} from 'bun:test';
import {decodeAcceptanceJson,AcceptanceJsonError} from '../packages/postgresql/src/acceptance-json';
const corpus=await Bun.file('docs/helix/03-test/acceptance-outer-json-expected.proposal.json').json();
for(const c of corpus.cases)test(c.name,()=>{
 const bytes=Uint8Array.from(Buffer.from(c.utf8Hex,'hex'));
 expect(new Bun.CryptoHasher('sha256').update(bytes).digest('hex')).toBe(c.sourceSha256);
 if(c.expected.status==='decoded'){const value=decodeAcceptanceJson(bytes);expect(JSON.stringify(value)).toBe(JSON.stringify(c.expected.value));if(c.name==='inert prototype name')expect(Object.getPrototypeOf(value)).toBe(null)}
 else{let failure:unknown;try{decodeAcceptanceJson(bytes)}catch(e){failure=e}expect(failure).toBeInstanceOf(AcceptanceJsonError);expect((failure as AcceptanceJsonError).reason).toBe(c.expected.reason)}
});
