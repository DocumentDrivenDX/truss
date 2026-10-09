import {test,expect} from 'bun:test';
import {preflightSourceJson,decodeAcceptanceJson,AcceptanceJsonError} from '../packages/postgresql/src/acceptance-json';
const bytes=(s:string)=>new TextEncoder().encode(s);
test('source numerical lexemes remain opaque even beyond JavaScript precision and range',()=>{
 const original=bytes('{"integer":9007199254740993,"decimal":0.12345678901234567890123456789,"exponent":1e9999,"negative":-0}');
 const retained=original.slice();expect(preflightSourceJson(original)).toBeUndefined();expect(original).toEqual(retained);
 expect(()=>decodeAcceptanceJson(original)).toThrow('numeric_node');
});
test('strict numeric grammar rejects incomplete and non-JSON spellings',()=>{
 for(const value of ['01','-01','+1','1.','.1','1e','1e+','--1','NaN','Infinity','0x1','1 2'])expect(()=>preflightSourceJson(bytes(value))).toThrow(AcceptanceJsonError);
 for(const value of ['0','-0','12','-12.5','1E+2','1e-2'])expect(()=>preflightSourceJson(bytes(value))).not.toThrow();
});
test('duplicate decoded names and malformed Unicode cannot reach the owner parser',()=>{
 expect(()=>preflightSourceJson(bytes('{"id":"a","\\u0069d":"b"}'))).toThrow('duplicate_member');
 expect(()=>preflightSourceJson(bytes('{"x":"\\ud800"}'))).toThrow('unicode');
 expect(()=>preflightSourceJson(Uint8Array.from([34,0xed,0xa0,0x80,34]))).toThrow('unicode');
});
test('source preflight retains structural bounds for numeric-heavy documents',()=>{
 expect(()=>preflightSourceJson(bytes('['.repeat(129)+'0'+']'.repeat(129)))).toThrow('resource');
 expect(()=>preflightSourceJson(bytes('['+Array(4097).fill('0').join(',')+']'))).toThrow('resource');
});
