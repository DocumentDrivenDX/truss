/** Host-local originals; local IDs confer no native issuer, epoch or settlement authority. */
import {openSync,writeSync,fsyncSync,closeSync,lstatSync,fstatSync,readSync,constants} from 'node:fs';
import {join} from 'node:path';
import {randomUUID} from 'node:crypto';
import {ResponseIngress,decodeResponseFrame} from './wire';
export interface LocalQueryCustody {readonly lease:string;readonly ordinal:string;}
export interface OriginalQueryJournal {
 begin(text:string,values:readonly (string|null)[],custody:LocalQueryCustody):{
  frame(bytes:Uint8Array):void;
  finish(outcome:'response_complete'|'server_error'|'uncertain'):void;
 };
}
/** Explicit opt-in. Directory must already exist, be private and host-owned. Contains sensitive SQL/data. */
export function createFileQueryJournal(directory:string):OriginalQueryJournal {
 const stat=lstatSync(directory);
 if(!stat.isDirectory()||(stat.mode&0o077)!==0||stat.uid!==process.getuid?.())throw Error('Private owned journal directory required');
 return {begin(text,values,custody){
  if(!custody||! /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(custody.lease)||! /^(0|[1-9][0-9]*)$/.test(custody.ordinal))throw Error('Local query custody required');
  const path=join(directory,randomUUID()+'.jsonl');
  const append=(record:unknown,first=false)=>{
   const fd=openSync(path,first?'wx':'a',0o600);
   try{const bytes=Buffer.from(JSON.stringify(record)+'\n');let offset=0;while(offset<bytes.length)offset+=writeSync(fd,bytes,offset,bytes.length-offset);fsyncSync(fd);}finally{closeSync(fd);}
  };
  append({kind:'request',text,values:[...values],custody:{lease:custody.lease,ordinal:custody.ordinal}},true);
  // Persist directory entry before native admission, including after a machine crash.
  const dir=openSync(directory,'r');try{fsyncSync(dir);}finally{closeSync(dir);}
  let ended=false;
  return {frame(bytes){if(ended)throw Error('Journal ended');append({kind:'frame',hex:Buffer.from(bytes).toString('hex')});},
   finish(outcome){if(ended)throw Error('Journal ended');append({kind:'outcome',outcome});ended=true;}};
 }};
}

export interface OriginalQueryInspection {
 readonly state:'complete'|'uncertain'|'incomplete'|'invalid';
 readonly originalHex:string;
 readonly request?:{readonly text:string;readonly values:readonly (string|null)[];readonly custody:LocalQueryCustody};
 readonly frames?:readonly string[];
 readonly outcome?:'response_complete'|'server_error'|'uncertain';
}
/** Bounded offline inspection only. Never returns native settlement/replay authority. */
export function inspectOriginalQueryFile(path:string,limits:{maxBytes:number}):OriginalQueryInspection {
 if(!Number.isSafeInteger(limits.maxBytes)||limits.maxBytes<1||limits.maxBytes>16777216)throw Error('Journal byte limit required (at most 16 MiB)');
 const fd=openSync(path,constants.O_RDONLY|constants.O_NOFOLLOW);let bytes:Buffer;
 try{
  const stat=fstatSync(fd);
  if(!stat.isFile()||stat.uid!==process.getuid?.()||(stat.mode&0o077)!==0||stat.size>limits.maxBytes)throw Error('Private bounded original file required');
  const buffer=Buffer.alloc(stat.size+1);let count=0;
  while(count<buffer.length){const n=readSync(fd,buffer,count,buffer.length-count,null);if(!n)break;count+=n;}
  if(count!==stat.size)throw Error('Original journal changed during inspection');bytes=buffer.subarray(0,count);
 }finally{closeSync(fd);}
 const originalHex=bytes.toString('hex');
 const result=(state:OriginalQueryInspection['state'])=>Object.freeze({state,originalHex});
 if(!bytes.length||bytes.at(-1)!==10)return result('incomplete');
 try{
  const lines=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes).slice(0,-1).split('\n');
  if(lines.length>10002)return result('invalid');
  const records=lines.map(line=>JSON.parse(line));const request=records.shift();
  const exact=(value:any,keys:string[])=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
  if(!exact(request,['kind','text','values','custody'])||request.kind!=='request'||typeof request.text!=='string'||!Array.isArray(request.values)||request.values.some((v:unknown)=>v!==null&&typeof v!=='string')||!exact(request.custody,['lease','ordinal'])||typeof request.custody.lease!=='string'||! /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(request.custody.lease)||typeof request.custody.ordinal!=='string'||! /^(0|[1-9][0-9]*)$/.test(request.custody.ordinal))return result('invalid');
  const last=records.at(-1);const outcome=last?.kind==='outcome'?records.pop():undefined;
  if(outcome&&(!exact(outcome,['kind','outcome'])||!['response_complete','server_error','uncertain'].includes(outcome.outcome)))return result('invalid');
  const wire={maxFrameBytes:1048576,maxFields:2048,maxTotalBytes:4194304,maxFrames:10000};
  const ingress=new ResponseIngress(wire);const frames:string[]=[];let errors=0;
  for(const record of records){
   if(!exact(record,['kind','hex'])||record.kind!=='frame'||typeof record.hex!=='string'||! /^(?:[0-9a-f]{2})+$/.test(record.hex))return result('invalid');
   if(record.hex.length>wire.maxFrameBytes*2)return result('invalid');
   const bytes=Buffer.from(record.hex,'hex');decodeResponseFrame(bytes,wire);
   ingress.feed(bytes,frame=>{if(decodeResponseFrame(frame,wire).kind==='E')errors++;});frames.push(record.hex);
  }
  if(outcome&&outcome.outcome!=='uncertain'){
   ingress.finish();if(outcome.outcome==='server_error'?errors!==1:errors!==0)return result('invalid');
  }
  return Object.freeze({state:!outcome?'incomplete':outcome.outcome==='uncertain'?'uncertain':'complete',originalHex,
   request:Object.freeze({text:request.text,values:Object.freeze([...request.values]),custody:Object.freeze({...request.custody})}),
   frames:Object.freeze(frames),...(outcome?{outcome:outcome.outcome}:{})});
 }catch{return result('invalid');}
}
