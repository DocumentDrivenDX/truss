import {describe,test,expect} from 'bun:test';
import {mapAssertedOrigin} from '../packages/postgresql/src/asserted-origin-map';
const bytes=(s:string)=>new TextEncoder().encode(s);
describe('asserted origin candidate mapping',()=>{
 test('preserves exact numeric-looking strings, tagged authored objects, null and sequence',()=>{
  const original=bytes('{"actor":"claimed","decimal":"9007199254740993.000","tag":{"kind":"integer","text":"123"},"values":[null,false,""],"databaseRole":"asserted-only"}');
  const result=mapAssertedOrigin(original,'actual role');
  expect(result.origin.asserted).toEqual(JSON.parse(new TextDecoder().decode(original)));
  expect(result.journalOrigin.databaseRole).toBe('actual role');
  expect(result.journalOrigin.asserted).toMatchObject({kind:'map'});
  const entries=(result.journalOrigin.asserted as any).entries;
  expect(entries.find((e:any)=>e.key==='decimal').value).toEqual({kind:'string',text:'9007199254740993.000'});
  expect(entries.find((e:any)=>e.key==='tag').value.kind).toBe('map');
  expect(entries.find((e:any)=>e.key==='databaseRole').value.text).toBe('asserted-only');
  original.fill(0);expect(result.origin.asserted).toHaveProperty('actor','claimed');
  expect(Object.isFrozen(entries)).toBe(true);
 });
 test('orders unsigned UTF8 keys and preserves NUL/prototype names',()=>{
  const result=mapAssertedOrigin(bytes('{"😀":"a","\uE000":"b","__proto__":"c","\\u0000":"d"}'),'role');
  expect((result.journalOrigin.asserted as any).entries.map((e:any)=>e.key)).toEqual(['\0','__proto__','\uE000','😀']);
  expect(Object.hasOwn(result.origin.asserted as object,'__proto__')).toBe(true);
 });
 test('refuses numbers, duplicates and invalid role text',()=>{
  for(const input of ['123','{"a":null,"a":true}','"\\ud800"'])expect(()=>mapAssertedOrigin(bytes(input),'role')).toThrow();
  for(const role of ['', '\0','\ud800'])expect(()=>mapAssertedOrigin(bytes('null'),role)).toThrow();
 });
});
