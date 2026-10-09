import {test,expect} from 'bun:test';
import {prepareCanonicalWireTree} from '../packages/postgresql/src/canonical-wire-tree';
const bytes=(text:string)=>new TextEncoder().encode(text);
test('original source spelling and scalar UTF-8 remain separate from canonical codec carrier',()=>{
 const original=' \n{"z":[null,true,"\\u0000😀"],"a":"9007199254740993"}\n',result=prepareCanonicalWireTree(bytes(original));
 expect(Buffer.from(result.originalUtf8Hex,'hex').toString()).toBe(original);expect(JSON.parse(result.nativeTreeText)).toEqual({kind:'object',members:[{keyUtf8Hex:'7a',node:{kind:'array',items:[{kind:'null'},{kind:'boolean',value:true},{kind:'string',utf8Hex:'00f09f9880'}]}},{keyUtf8Hex:'61',node:{kind:'string',utf8Hex:'39303037313939323534373430393933'}}]});expect(result.nativeTaskCount).toBe('17');expect(Object.isFrozen(result)).toBe(true);
});
test('empty containers and inert prototype/member names preserve native member arrays',()=>{
 const result=JSON.parse(prepareCanonicalWireTree(bytes('{"__proto__":{},"\\u0000":[],"𐀀":"x","":"y"}')).nativeTreeText);
 expect(result.members.map((m:any)=>m.keyUtf8Hex)).toEqual(['5f5f70726f746f5f5f','00','f0908080','ee8080']);expect(result.members[0].node).toEqual({kind:'object',members:[]});expect(result.members[1].node).toEqual({kind:'array',items:[]});
});
test('outer numeric nodes duplicate decoded names and malformed Unicode never reach native codec',()=>{
 for(const text of ['{"x":1}','{"a":null,"\\u0061":true}','"\\ud800"'])expect(()=>prepareCanonicalWireTree(bytes(text))).toThrow();
});
test('native task ceiling is checked before carrier construction',()=>{
 const source=JSON.stringify(Array.from({length:4096},()=>[null,null,null]));expect(()=>prepareCanonicalWireTree(bytes(source))).toThrow('task capacity');
 expect(prepareCanonicalWireTree(bytes('[null]')).nativeTaskCount).toBe('4');
});
test('shared backing cannot impersonate original immutable source custody',()=>{
 expect(()=>prepareCanonicalWireTree(new Uint8Array(new SharedArrayBuffer(8)))).toThrow('byte custody');
});
