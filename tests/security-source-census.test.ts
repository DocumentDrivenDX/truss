// SPDX-License-Identifier: MIT OR Apache-2.0
import {test,expect} from 'bun:test';
import {CensusChunkAssembly} from '../packages/pg-runtime/src/security-source-census';
import {decodeResponseFrame,ResponseIngress} from '../packages/pg-runtime/src/wire';
const n16=(n:number)=>{const b=Buffer.alloc(2);b.writeUInt16BE(n);return b;};
const n32=(n:number)=>{const b=Buffer.alloc(4);b.writeInt32BE(n);return b;};
const cstring=(s:string)=>Buffer.from(s+'\0');
function frame(kind:string,body:Buffer){return Buffer.concat([Buffer.from(kind),n32(body.length+4),body]);}
function response(batch:(string|null)[][],options:{names?:string[];oid?:number;format?:number;count?:number;status?:string}={}){
 const names=options.names??['ordinal','total_bytes','chunk_hex'];
 const desc=Buffer.concat([n16(3),...names.map(name=>Buffer.concat([cstring(name),n32(0),n16(0),n32(options.oid??25),n16(65535),n32(-1),n16(options.format??0)]))]);
 const bytes=[frame('T',desc),...batch.map(row=>frame('D',Buffer.concat([n16(row.length),...row.map(cell=>cell===null?n32(-1):Buffer.concat([n32(Buffer.byteLength(cell)),Buffer.from(cell)]))]))),frame('C',cstring('FETCH '+(options.count??batch.length))),frame('Z',Buffer.from(options.status??'T'))];
 // Original binary fixture, independently checked by the existing ingress/decoder.
 const decoded:ReturnType<typeof decodeResponseFrame>[]=[];
 const ingress=new ResponseIngress({maxFrameBytes:1048576,maxFields:2048,maxTotalBytes:4194304,maxFrames:10000});
 for(const b of bytes)ingress.feed(b,f=>decoded.push(decodeResponseFrame(f,{maxFrameBytes:1048576,maxFields:2048})));
 ingress.finish();return decoded;
}
function chunks(bytes:Buffer){return Array.from({length:Math.ceil(bytes.length/32768)},(_,i)=>[String(i),String(bytes.length),bytes.subarray(i*32768,(i+1)*32768).toString('hex')]);}
function capture(bytes:Buffer){const a=new CensusChunkAssembly(),rows=chunks(bytes);for(let i=0;i<rows.length;i+=16)a.accept(response(rows.slice(i,i+16)));a.accept(response([]));return a.finish();}
for(const size of [1,32767,32768,32769,524288,524289,16777216])test('complete exact byte boundary '+size,()=>{
 const source=Buffer.alloc(size,65);expect(Buffer.from(capture(source))).toEqual(source);
});
test('native UTF8 bytes survive a split inside a multibyte scalar',()=>{
 const source=Buffer.from('A'.repeat(32767)+'🙂é'+ 'B'.repeat(32767));expect(capture(source)).toBe(source.toString());
});
test('one over image ceiling refuses without accepted prefix',()=>{
 const a=new CensusChunkAssembly();expect(()=>a.accept(response([['0','16777217','41'.repeat(32768)]]))).toThrow();expect(()=>a.finish()).toThrow();
});
const base=chunks(Buffer.alloc(32769,65));
const invalid:Record<string,(string|null)[][]>={
 missingFirst:[base[1]],duplicate:[base[0],base[0]],reversed:[base[1],base[0]],gap:[base[0],['2',...base[1].slice(1)]],
 shortened:[['0','32769','41']],long:[['0','32769','41'.repeat(32769)]],
 inconsistentTotal:[base[0],['1','32768','41']],nullChunk:[['0','32769',null]],
 uppercase:[['0','32769','AA'.repeat(32768)]],invalidHex:[['0','32769','gg'.repeat(32768)]],
 noncanonicalOrdinal:[['00','32769',base[0][2]]],negativeOrdinal:[['-1','32769',base[0][2]]],
 noncanonicalTotal:[['0','032769',base[0][2]]],zeroTotal:[['0','0','41']],nullCensus:[[null,null,null]],extraRow:[...base,['2','32769','41']]
};
for(const [name,batch] of Object.entries(invalid))test('refuse '+name,()=>{const a=new CensusChunkAssembly();expect(()=>a.accept(response(batch))).toThrow();expect(()=>a.finish()).toThrow();});
test('truncated stream and premature terminal response refuse',()=>{
 const a=new CensusChunkAssembly();a.accept(response([base[0]]));expect(()=>a.finish()).toThrow();expect(()=>a.accept(response([]))).toThrow();expect(()=>a.finish()).toThrow();
});
test('full bytes are not released before native end of cursor',()=>{const a=new CensusChunkAssembly();a.accept(response(base));expect(()=>a.finish()).toThrow();a.accept(response([]));expect(a.finish()).toBe('A'.repeat(32769));expect(()=>a.accept(response([]))).toThrow();expect(()=>a.finish()).toThrow();});
for(const opts of [{names:['wrong','total_bytes','chunk_hex']},{oid:23},{format:1},{status:'I'}])test('native descriptor or status refusal '+JSON.stringify(opts),()=>{
 const a=new CensusChunkAssembly();expect(()=>a.accept(response(base,opts))).toThrow();expect(()=>a.finish()).toThrow();
});
test('over fetch ceiling',()=>{const a=new CensusChunkAssembly();const b=chunks(Buffer.alloc(17*32768));expect(()=>a.accept(response(b))).toThrow();});
test('assembler rejects lying FETCH count accepted by generic ingress',()=>{const a=new CensusChunkAssembly();expect(()=>a.accept(response(base,{count:1}))).toThrow();expect(()=>a.finish()).toThrow();});
test('final UTF8 refusal retains no accepted image',()=>{const a=new CensusChunkAssembly();a.accept(response(chunks(Buffer.from([0xff]))));a.accept(response([]));expect(()=>a.finish()).toThrow();expect(()=>a.finish()).toThrow();});
test('countercontrol: fabricated well-shaped frames can replace bytes without custody',()=>{
 expect(capture(Buffer.from('forged complete source'))).toBe('forged complete source');
 // Sequence/size checks are not original source authentication or injectivity.
});
