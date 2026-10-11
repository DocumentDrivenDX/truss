import {test,expect} from 'bun:test';
import {indexSourceJsonOccurrences as index,originalSourceOccurrenceBytes as bytes,preflightSourceJson,decodeAcceptanceJson} from '../packages/postgresql/src/acceptance-json';
const utf8=(s:string)=>new TextEncoder().encode(s),text=(b:Uint8Array)=>new TextDecoder().decode(b);
test('every original value has an ordered pointer and exact lexical span',()=>{
 const source=' \n{"a/b":[9007199254740993,-0,1.2300e+9,true,null,"é"],"~":{"":[]}} \t';
 const result=index(utf8(source));
 expect(result.occurrences.map(o=>[o.pointer,o.kind,text(bytes(result,result.occurrences.indexOf(o)))])).toEqual([
  ['','object',source.trim()],['/a~1b','array','[9007199254740993,-0,1.2300e+9,true,null,"é"]'],
  ['/a~1b/0','number','9007199254740993'],['/a~1b/1','number','-0'],['/a~1b/2','number','1.2300e+9'],['/a~1b/3','boolean','true'],['/a~1b/4','null','null'],['/a~1b/5','string','"é"'],['/~0','object','{"":[]}'],['/~0/','array','[]'],
 ]);
 expect(result.originalByteLength).toBe(utf8(source).length);expect(Object.isFrozen(result.occurrences[0])).toBe(true);
});
test('escaped member identity and unicode retain exact source bytes',()=>{
 const result=index(utf8('{"\\u0061":"\\uD83D\\uDE00","😀":1e999999}'));
 expect(result.occurrences.map(o=>o.pointer)).toEqual(['','/a','/😀']);expect(text(bytes(result,1))).toBe('"\\uD83D\\uDE00"');expect(text(bytes(result,2))).toBe('1e999999');
});
test('captured bytes and returned slices are independent of caller mutation',()=>{
 const input=utf8('[123]'),result=index(input);input.fill(0);const first=bytes(result,1);first.fill(0);expect(text(bytes(result,1))).toBe('123');
 expect(()=>bytes({...result},0)).toThrow('custody');for(const position of [-1,0.5,NaN,Infinity,2])expect(()=>bytes(result,position)).toThrow('position');
});
test('root primitives and empty containers remain complete occurrences',()=>{
 for(const source of ['null','false','""','123','{}','[]']){const result=index(utf8(source));expect(result.occurrences.length).toBe(1);expect(text(bytes(result,0))).toBe(source)}
});
test('source admission still refuses duplicates invalid unicode and malformed grammar',()=>{
 for(const source of ['{"a":1,"\\u0061":2}','{"a":01}','[1,]','{"x":"\\uD800"}','true false']){expect(()=>index(utf8(source))).toThrow();expect(()=>preflightSourceJson(utf8(source))).toThrow()}
 expect(()=>decodeAcceptanceJson(utf8('123'))).toThrow('numeric_node');
});
test('discarded preflight tree does not replace original number lexemes',()=>{
 const source='{"n":-1.00E-100000,"opaque":{"tag":"number","value":"literal"}}';preflightSourceJson(utf8(source));const result=index(utf8(source));expect(text(bytes(result,1))).toBe('-1.00E-100000');expect(result.occurrences.map(o=>o.pointer)).toEqual(['','/n','/opaque','/opaque/tag','/opaque/value']);
});

test('occurrence indexing applies conjunctive source and pointer work bounds',()=>{
 expect(index(utf8('['+Array(4096).fill('0').join(',')+']')).occurrences.length).toBe(4097);
 expect(()=>index(utf8('['+Array(4097).fill('0').join(',')+']'))).toThrow('resource');
 expect(()=>index(new Uint8Array(1048577))).toThrow('resource');
 expect(()=>index(utf8('['.repeat(130)+'0'+']'.repeat(130)))).toThrow('resource');
 // Long ancestry charges every materialized pointer, even when preflight alone fits.
 const source=('{"'+ 'a'.repeat(500)+'":').repeat(80)+'0'+'}'.repeat(80);
 preflightSourceJson(utf8(source));expect(()=>index(utf8(source))).toThrow('resource');
});

test('source copying never invokes caller species or own length callbacks',()=>{
 for(const throwing of [false,true]){
  const input=utf8('[123]');let calls=0;
  Object.defineProperty(input,'constructor',{value:{[Symbol.species]:function(){calls++;if(throwing)throw Error('species');return input}}});
  Object.defineProperty(input,'length',{get(){calls++;throw Error('length')}});
  const result=index(input);input.fill(0);expect(text(bytes(result,1))).toBe('123');
  const returned=bytes(result,1);returned.fill(0);expect(text(bytes(result,1))).toBe('123');expect(calls).toBe(0);
 }
});

test('non-byte typed arrays cannot be silently narrowed into source bytes',()=>{
 for(const input of [new Uint16Array([347,305,349]),new Float64Array([91,49,93])]){
  Object.defineProperty(input,Symbol.toStringTag,{get(){throw Error('tag callback')}});
  expect(()=>index(input as unknown as Uint8Array)).toThrow('grammar');
  expect(()=>preflightSourceJson(input as unknown as Uint8Array)).toThrow('grammar');
 }
});
