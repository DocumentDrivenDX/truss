import {test,expect} from 'bun:test';
import {createAcceptanceInputInspector,AcceptanceInputInspectionError} from '../packages/umf-bun/src/acceptance-input';
const inspector=await createAcceptanceInputInspector('/Users/erik/Projects/umf/package.json');
const fixture=await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json();
const inspect=(input:unknown)=>inspector.inspect(new TextEncoder().encode(JSON.stringify(input)));
test('complete original wire and all converted artifact bytes survive inspection',()=>{
 const bytes=new TextEncoder().encode(JSON.stringify(fixture.input));const result=inspector.inspect(bytes);
 expect(JSON.stringify(result.input)).toBe(JSON.stringify(fixture.input));expect(result.documents.map(d=>d.originalText)).toEqual(['{}','{}']);
 expect(result.originalUtf8Hex).toBe(Buffer.from(bytes).toString('hex'));expect(Object.isFrozen(result.input.documents[1].ingress)).toBe(true);expect(result.scope).toBe('wire_and_artifact_inspection_only');
});
for(const [name,modify,reason] of [
 ['missing conversion source',(v:any)=>delete v.documents[1].ingress.source,'schema'],
 ['damaged source digest',(v:any)=>v.documents[1].ingress.source.sha256='0'.repeat(64),'artifact_integrity'],
 ['noncanonical identical artifact',(v:any)=>v.documents[0].artifact.bytesBase64='e31=','artifact_integrity'],
 ['duplicate original document',(v:any)=>v.documents[1].documentId=v.documents[0].documentId,'document_identity'],
 ['host number',(v:any)=>v.transforms[0].parameters.value=1.25,'numeric_node'],
] as const)test(name,()=>{const changed=structuredClone(fixture.input);modify(changed);let failure:any;try{inspect(changed)}catch(e){failure=e}expect(failure).toBeDefined();expect(failure.reason).toBe(reason)});
test('documents-only input cannot become complete original admission',()=>expect(()=>inspect({documents:fixture.input.documents})).toThrow(AcceptanceInputInspectionError));

test('concurrently shared raw custody cannot enter inspection',()=>expect(()=>inspector.inspect(new Uint8Array(new SharedArrayBuffer(2)))).toThrow(AcceptanceInputInspectionError));
