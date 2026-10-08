import {test,expect} from 'bun:test';
import {decodeResponseFrame} from '../packages/pg-runtime/src/wire';
const limits={maxFrameBytes:4096,maxFields:16};
const frame=(kind:string,body:number[])=>Uint8Array.from([kind.charCodeAt(0),0,0,0,body.length+4,...body]);
test('original command count text beyond host precision remains exact',()=>{
 const bytes=new TextEncoder().encode('SELECT 9007199254740993123456789\0');
 const value=decodeResponseFrame(frame('C',[...bytes]),limits);
 expect(value.fields[0]).toEqual({command:'SELECT 9007199254740993123456789',affectedRows:'9007199254740993123456789'});
 expect(decodeResponseFrame(frame('C',[...new TextEncoder().encode('INSERT 0 17\0')]),limits).fields[0].affectedRows).toBe('17');
});
test('raw data preserves NULL/empty/binary distinctions and frame boundaries',()=>{
 const original=frame('D',[0,3,255,255,255,255,0,0,0,0,0,0,0,2,255,0]);
 expect(decodeResponseFrame(original,limits).fields).toEqual([{hex:null},{hex:''},{hex:'ff00'}]);
 expect(()=>decodeResponseFrame(original,{...limits,maxFields:2})).toThrow();
 expect(()=>decodeResponseFrame(original.subarray(0,original.length-1),limits)).toThrow();
 expect(()=>decodeResponseFrame(original,{...limits,maxFrameBytes:5})).toThrow();
 expect(decodeResponseFrame(frame('Z',[69]),limits).fields).toEqual([{status:'E'}]);
 expect(()=>decodeResponseFrame(frame('Z',[88]),limits)).toThrow();
 expect(()=>decodeResponseFrame(frame('X',[]),limits)).toThrow();
});
