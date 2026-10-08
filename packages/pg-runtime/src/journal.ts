/** Host-local originals; local IDs confer no native issuer, epoch or settlement authority. */
import {openSync,writeSync,fsyncSync,closeSync,lstatSync} from 'node:fs';
import {join} from 'node:path';
import {randomUUID} from 'node:crypto';
export interface OriginalQueryJournal {
 begin(text:string,values:readonly (string|null)[]):{
  frame(bytes:Uint8Array):void;
  finish(outcome:'response_complete'|'server_error'|'uncertain'):void;
 };
}
/** Explicit opt-in. Directory must already exist, be private and host-owned. Contains sensitive SQL/data. */
export function createFileQueryJournal(directory:string):OriginalQueryJournal {
 const stat=lstatSync(directory);
 if(!stat.isDirectory()||(stat.mode&0o077)!==0||stat.uid!==process.getuid?.())throw Error('Private owned journal directory required');
 return {begin(text,values){
  const path=join(directory,randomUUID()+'.jsonl');
  const append=(record:unknown,first=false)=>{
   const fd=openSync(path,first?'wx':'a',0o600);
   try{const bytes=Buffer.from(JSON.stringify(record)+'\n');let offset=0;while(offset<bytes.length)offset+=writeSync(fd,bytes,offset,bytes.length-offset);fsyncSync(fd);}finally{closeSync(fd);}
  };
  append({kind:'request',text,values:[...values]},true);
  // Persist directory entry before native admission, including after a machine crash.
  const dir=openSync(directory,'r');try{fsyncSync(dir);}finally{closeSync(dir);}
  let ended=false;
  return {frame(bytes){if(ended)throw Error('Journal ended');append({kind:'frame',hex:Buffer.from(bytes).toString('hex')});},
   finish(outcome){if(ended)throw Error('Journal ended');append({kind:'outcome',outcome});ended=true;}};
 }};
}
