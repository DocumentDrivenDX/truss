import {test,expect} from 'bun:test';
import {loadUmfProducer} from '../packages/umf-bun/src/index';
import {preflightSourceJson} from '../packages/postgresql/src/acceptance-json';
const directory=process.env.TRUSS_UMF_PRODUCER;if(!directory)throw Error('Original Record producer directory required');
const owner=await loadUmfProducer(directory);
const source=(lexeme:string)=>`{"umf":"0.7.0","id":"numeric-source","vocabularies":{"unknown":{"version":"1.0.0"}},"extensions":{"unknown":{"value":${lexeme}}},"modules":[]}`;
for(const lexeme of ['9007199254740993','0.12345678901234567890123456789','1e9999','1e-9999','-0'])test('pinned owner refuses precision loss or unsupported numeric source: '+lexeme,()=>{
 const original=source(lexeme);expect(()=>preflightSourceJson(new TextEncoder().encode(original))).not.toThrow();
 let error:unknown;try{owner.inspect(original)}catch(e){error=e}
 expect(error).toBeDefined();expect((error as {code:string}).code).toBe('NUMBER');
});
for(const [lexeme,expected] of [['0.1',0.1],['9007199254740991',9007199254740991],['1e2',100]] as const)test('pinned owner admits interoperable numeric source without changing its decimal value: '+lexeme,()=>{
 const original=source(lexeme);const result=owner.inspect(original);
 expect(result.originalText).toBe(original);expect(result.sourceValidation.valid).toBe(true);
 expect(result.source.extensions.unknown.value).toBe(expected);expect(result.targetValidation?.valid).toBe(true);
});
test('unknown exact numeric carrier stays opaque and retains its string payload',()=>{
 const carrier='{"kind":"decimalToken","value":"0.12345678901234567890123456789"}';const original=source(carrier);const result=owner.inspect(original);
 expect(result.source.extensions.unknown.value).toEqual({kind:'decimalToken',value:'0.12345678901234567890123456789'});
 expect(result.originalText).toBe(original);expect(result.sourceValidation.valid).toBe(true);
 // Unknown extension preservation does not claim this arbitrary object is a core numeric value.
 expect(result.sourceValidation.complete).toBe(false);
});
