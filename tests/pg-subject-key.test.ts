import {test,expect} from 'bun:test';
import {createOrdinarySubjectKeyBinding} from '../packages/pg-runtime/src/subject-key';
import * as owner from '../packages/python/src/truss/_umf_keys08/producer.js';
const sourceText=JSON.parse(await Bun.file(import.meta.dir+'/../packages/python/tests/fixtures/security-mapping-request.json').text()).modules[0].documentJson;
const identity={module:'m',element:'Staff',key:'pk'};
const connection={} as any;
function observation(values:string[],columns=values.map((_,i)=>'k'+i)){
 return Object.freeze({version:'truss.native.subject-observation/0.1' as const,principal:'alice',keyColumns:Object.freeze(columns),keyValues:Object.freeze(values),keyHex:Object.freeze(values.map(v=>Buffer.from(v).toString('hex')))});
}
function binding(source:string,values:string[],encodings:('string'|'core-literal-json')[],selected=identity){
 const observed=observation(values);return createOrdinarySubjectKeyBinding({host:{observeOrdinarySubject(c){if(c!==connection)throw Error('foreign');return observed;}},owner,inspectSubjectKey:()=>{},sourceText:source,identity:selected,keyColumns:[...observed.keyColumns],encodings});
}
test('native string subject uses exact original UMF key receipt and bytes',()=>{
 const result=binding(sourceText,['alice'],['string']).encode(connection);
 const source=owner.readJsonValue(sourceText,'json');const expected=owner.encodeCoreKeyTuple(source,identity,[{string:'alice'}]);
 expect(result.bytesHex).toBe(expected.bytesHex);expect(JSON.parse(result.originalReceiptText)).toEqual(expected);expect(Object.isFrozen(result)).toBe(true);
 expect(()=>binding(sourceText,['alice'],['string']).encode({} as any)).toThrow();
});
test('all scalar key families and ordered exact numeric/binary literals stay with owner',()=>{
 const source=JSON.parse(sourceText);const m=source.modules[0];
 const kinds=['string','boolean','integer','decimal','binary'];
 m.elements=[{id:'Staff',kind:'record',name:'Staff',members:kinds.map((_,i)=>({module:'m',element:'k'+i})),keys:[{id:'pk',name:'Key',fields:kinds.map((_,i)=>({module:'m',element:'k'+i}))}],extensions:{}},...kinds.map((kind,i)=>({id:'k'+i,name:'k'+i,kind:'field',scalarType:kind,cardinality:'one',nullability:'required',extensions:{},...(kind==='decimal'?{facets:{precision:30,scale:4}}:{})}))];
 const values=[{string:'Δ\uFEFF'},{boolean:true},{integerToken:'9007199254740993'},{decimalToken:'9007199254740993.0000'},{binaryHex:'0001'}];
 const text=JSON.stringify(source);const native=values.map(v=>JSON.stringify(v));
 const result=binding(text,native,kinds.map(()=> 'core-literal-json')).encode(connection);
 const expected=owner.encodeCoreKeyTuple(source,identity,values);expect(result.bytesHex).toBe(expected.bytesHex);
 const changed=[...native];changed[2]=JSON.stringify({integerToken:'9007199254740992'});
 expect(binding(text,changed,kinds.map(()=> 'core-literal-json')).encode(connection).bytesHex).not.toBe(result.bytesHex);
 const reversed=[...native].reverse();expect(()=>binding(text,reversed,kinds.map(()=> 'core-literal-json')).encode(connection)).toThrow();
});
test('owner rejects arity/domain/null/unknown key and literal JSON errors',()=>{
 for(const [values,encodings,selected] of [
  [['1'],['core-literal-json'],identity],
  [['null'],['core-literal-json'],identity],
  [['{"integerToken":"1"}'],['core-literal-json'],identity],
  [['{'],['core-literal-json'],identity],
  [['alice','bob'],['string','string'],identity],
  [['alice'],['string'],{...identity,key:'missing'}],
 ] as const)expect(()=>binding(sourceText,[...values],[...encodings] as any,selected).encode(connection)).toThrow();
});
test('binding selection is captured; column mismatch and byte limits refuse',()=>{
 const selected={...identity},columns=['staff_id'],encodings=['string' as const];
 const host={observeOrdinarySubject:()=>observation(['alice'],['staff_id'])};
 const captured=createOrdinarySubjectKeyBinding({host,owner,inspectSubjectKey:()=>{},sourceText,identity:selected,keyColumns:columns,encodings});
 selected.key='missing';columns[0]='changed';encodings[0]='core-literal-json' as any;host.observeOrdinarySubject=()=>{throw Error('changed');};
 expect(captured.encode(connection).bytesHex.length).toBeGreaterThan(0);
 expect(()=>createOrdinarySubjectKeyBinding({host:{observeOrdinarySubject:()=>observation(['alice'],['other'])},owner,inspectSubjectKey:()=>{},sourceText,identity,keyColumns:['staff_id'],encodings:['string']}).encode(connection)).toThrow();
 expect(()=>binding(sourceText,['x'.repeat(1048577)],['string']).encode(connection)).toThrow();
 expect(()=>binding('x'.repeat(1048577),['alice'],['string'])).toThrow();
});

test('source byte identity rejects lossy raw Unicode but preserves escaped JSON',()=>{
 for(const name of ['\uD800','\uDFFF']){
  const doc=JSON.parse(sourceText);doc.modules[0].elements[0].name=name;
  const escaped=JSON.stringify(doc);
  const raw=escaped.replace(/\\u[dD][89a-fA-F][0-9a-fA-F]{2}/,name);
  expect(()=>binding(raw,['alice'],['string'])).toThrow();
  expect(binding(escaped,['alice'],['string']).encode(connection).sourceSha256.length).toBe(64);
 }
});

test('declared deferred inspectors refuse without invocation; ordinary rejected promises are observed',async()=>{
 let calls=0;const observed=observation(['alice'],['staff_id']);
 const options={host:{observeOrdinarySubject:()=>observed},owner,sourceText,identity,keyColumns:['staff_id'],encodings:['string' as const]};
 for(const inspectSubjectKey of [async()=>{calls++;throw Error('async');},function*(){calls++;},async function*(){calls++;}])expect(()=>createOrdinarySubjectKeyBinding({...options,inspectSubjectKey:inspectSubjectKey as any})).toThrow();
 expect(calls).toBe(0);
 expect(()=>createOrdinarySubjectKeyBinding({...options,inspectSubjectKey:(()=>Promise.reject(Error('contained'))) as any})).toThrow();
 await new Promise(resolve=>setTimeout(resolve,0));
});
