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

import {ResponseIngress} from '../packages/pg-runtime/src/wire';
test('fragmented original frame forwards once only after full admission',()=>{
 const original=frame('C',[...new TextEncoder().encode('SELECT 0\0')]);
 const ingress=new ResponseIngress({...limits,maxTotalBytes:100,maxFrames:2});const forwarded:Uint8Array[]=[];
 for(const byte of original.subarray(0,original.length-1))ingress.feed(Uint8Array.of(byte),x=>forwarded.push(x));
 expect(forwarded.length).toBe(0);ingress.feed(original.subarray(original.length-1),x=>forwarded.push(x));
 ingress.feed(frame('Z',[73]),()=>{});ingress.finish();
 expect(forwarded).toEqual([original]);expect(ingress.accounting.frames).toBe(2);
});
test('oversized header refuses before body allocation or forwarding and remains closed',()=>{
 const ingress=new ResponseIngress({...limits,maxTotalBytes:100,maxFrames:2});let calls=0;
 expect(()=>ingress.feed(Uint8Array.of(68,127,255,255,255),()=>calls++)).toThrow('frame-limit');
 expect(calls).toBe(0);expect(ingress.accounting.refused).toBe(true);
 expect(()=>ingress.feed(frame('Z',[73]),()=>calls++)).toThrow('refused');
 const partial=new ResponseIngress({...limits,maxTotalBytes:100,maxFrames:2});partial.feed(Uint8Array.of(84),()=>calls++);
 expect(()=>partial.finish()).toThrow('incomplete');
});

import nativeWire from '../docs/helix/04-build/evidence/inert-assembly/native-wire.json';
test('invalid text row refuses before forwarding to original parser',()=>{
 const originalDescription=Uint8Array.from(Buffer.from(nativeWire.frames[0].originalHex,'hex'));
 const ingress=new ResponseIngress({...limits,maxTotalBytes:4096,maxFrames:4});let calls=0;
 ingress.feed(originalDescription,()=>calls++);
 const invalid=frame('D',[0,2,0,0,0,1,255,255,255,255,255]);
 expect(()=>ingress.feed(invalid,()=>calls++)).toThrow();
 expect(calls).toBe(1);expect(ingress.accounting.refused).toBe(true);
});

test('query completion requires original command then ready and matching SELECT rows',()=>{
 const limits_={...limits,maxTotalBytes:4096,maxFrames:8};
 const command=frame('C',[...new TextEncoder().encode('SELECT 0\0')]);
 const incomplete=new ResponseIngress(limits_);incomplete.feed(command,()=>{});
 expect(()=>incomplete.finish()).toThrow('incomplete');
 const outOfOrder=new ResponseIngress(limits_);expect(()=>outOfOrder.feed(frame('Z',[73]),()=>{})).toThrow('response-order');
 const complete=new ResponseIngress(limits_);complete.feed(command,()=>{});complete.feed(frame('Z',[73]),()=>{});complete.finish();
 expect(()=>complete.feed(command,()=>{})).toThrow('ended');
 const wrongCount=new ResponseIngress(limits_);expect(()=>wrongCount.feed(frame('C',[...new TextEncoder().encode('SELECT 1\0')]),()=>{})).toThrow('row-count');
});

test('error response retains ordered fields and ends only on original ready',()=>{
 const error=frame('E',[...new TextEncoder().encode('SERROR\0C22012\0Mdivision by zero\0'),0]);
 const value=decodeResponseFrame(error,limits);expect(value.fields).toEqual([{tag:'S',value:'ERROR'},{tag:'C',value:'22012'},{tag:'M',value:'division by zero'}]);
 const ingress=new ResponseIngress({...limits,maxTotalBytes:4096,maxFrames:4});let calls=0;
 ingress.feed(error,()=>calls++);ingress.feed(frame('Z',[69]),()=>calls++);ingress.finish();expect(calls).toBe(2);
 const duplicate=frame('E',[...new TextEncoder().encode('C22012\0C22012\0'),0]);
 expect(()=>decodeResponseFrame(duplicate,limits)).toThrow();
 const noCode=frame('E',[...new TextEncoder().encode('Merror\0'),0]);expect(()=>decodeResponseFrame(noCode,limits)).toThrow();
 const noTerminator=frame('E',[...new TextEncoder().encode('C22012\0')]);expect(()=>decodeResponseFrame(noTerminator,limits)).toThrow();
});

test('notice is retained without replacing original command completion',()=>{
 const ingress=new ResponseIngress({...limits,maxTotalBytes:4096,maxFrames:4});const kinds:string[]=[];
 const notice=frame('N',[...new TextEncoder().encode('SNOTICE\0C00000\0Mnotice\0'),0]);
 ingress.feed(notice,frame=>kinds.push(String.fromCharCode(frame[0])));
 ingress.feed(frame('C',[...new TextEncoder().encode('SELECT 0\0')]),frame=>kinds.push(String.fromCharCode(frame[0])));
 ingress.feed(frame('Z',[73]),frame=>kinds.push(String.fromCharCode(frame[0])));ingress.finish();
 expect(kinds).toEqual(['N','C','Z']);
});

test('unnamed extended response requires parse/bind before no-data completion',()=>{
 const limits_={...limits,maxTotalBytes:4096,maxFrames:8};const ingress=new ResponseIngress(limits_);let calls=0;
 for(const packet of [frame('1',[]),frame('2',[]),frame('n',[]),frame('C',[...new TextEncoder().encode('INSERT 0 1\0')]),frame('Z',[73])])ingress.feed(packet,()=>calls++);
 ingress.finish();expect(calls).toBe(5);
 const foreign=new ResponseIngress(limits_);expect(()=>foreign.feed(frame('2',[]),()=>{})).toThrow('response-order');
 expect(()=>decodeResponseFrame(frame('1',[0]),limits)).toThrow();
});
