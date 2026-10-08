/** Local trust-auth-only protocol probe. Not a production connection/pool/transport profile. */
import {createConnection,type Socket} from 'node:net';
const utf8=new TextDecoder('utf-8',{fatal:true});
const i16=(v:number)=>{const b=Buffer.alloc(2);b.writeInt16BE(v);return b};
const i32=(v:number)=>{const b=Buffer.alloc(4);b.writeInt32BE(v);return b};
function string(value:string):Buffer {
 if(value.includes('\0'))throw Error('PostgreSQL text cannot carry NUL');
 for(let i=0;i<value.length;i++){const c=value.charCodeAt(i);if(c>=0xd800&&c<=0xdbff){const n=value.charCodeAt(++i);if(!(n>=0xdc00&&n<=0xdfff))throw Error('Invalid Unicode')}else if(c>=0xdc00&&c<=0xdfff)throw Error('Invalid Unicode')}
 if(Buffer.byteLength(value)>1_048_576)throw Error('Text budget exceeded');return Buffer.from(value,'utf8');
}
const z=(s:string)=>Buffer.concat([string(s),Buffer.from([0])]);
const frame=(tag:string,body:Buffer)=>Buffer.concat([Buffer.from(tag),i32(body.length+4),body]);
export interface Response {
 readonly fields:readonly string[];readonly rows:readonly (readonly (string|null)[])[];
 readonly originalRequestFrames:readonly string[];readonly command:string;readonly ready:'I'|'T'|'E';readonly originalFrames:readonly string[];
}
export class LocalPgProbe {
 private buffer=Buffer.alloc(0);private queued:Buffer[]=[];private queuedBytes=0;
 private waiter?:{resolve:(v:Buffer)=>void;reject:(e:Error)=>void};private failure?:Error;
 private busy=false;private closed=false;
 private constructor(private readonly socket:Socket){
  socket.on('data',chunk=>{try{
   if(!Buffer.isBuffer(chunk))throw Error('Unexpected decoded socket input');
   if(this.buffer.length+this.queuedBytes+chunk.length>8_388_608)throw Error('Response ingress budget exceeded');
   this.buffer=Buffer.concat([this.buffer,chunk]);
   while(this.buffer.length>=5){const size=this.buffer.readInt32BE(1);
    if(size<4||size>1_048_576)throw Error('Invalid response frame length');if(this.buffer.length<size+1)break;
    const original=this.buffer.subarray(0,size+1);this.buffer=this.buffer.subarray(size+1);
    if(this.waiter){const waiter=this.waiter;this.waiter=undefined;waiter.resolve(original)}
    else{this.queued.push(original);this.queuedBytes+=original.length}
   }
  }catch(error){this.stop(error as Error)}});
  socket.on('error',e=>this.stop(e));socket.on('close',()=>this.stop(Error('Native connection closed')));
 }
 private stop(error:Error){this.failure??=error;this.closed=true;this.socket.destroy();this.waiter?.reject(this.failure);this.waiter=undefined}
 private next():Promise<Buffer>{
  if(this.failure)return Promise.reject(this.failure);const result=this.queued.shift();
  if(result){this.queuedBytes-=result.length;return Promise.resolve(result)}
  return new Promise((resolve,reject)=>{if(this.waiter)throw Error('Concurrent native response waiter');this.waiter={resolve,reject}});
 }
 static async connect(port:number,user='postgres',database='postgres'):Promise<LocalPgProbe>{
  if(!Number.isInteger(port)||port<1||port>65535)throw Error('Invalid local port');
  const socket=createConnection({host:'127.0.0.1',port});const probe=new LocalPgProbe(socket);
  const timeout=setTimeout(()=>probe.stop(Error('Startup deadline')),5000);
  try{
   await new Promise<void>((resolve,reject)=>{socket.once('connect',resolve);socket.once('error',reject)});
   const body=Buffer.concat([i32(196608),z('user'),z(user),z('database'),z(database),z('client_encoding'),z('UTF8'),Buffer.from([0])]);socket.write(Buffer.concat([i32(body.length+4),body]));
   let authenticated=false;for(;;){const message=await probe.next(),tag=String.fromCharCode(message[0]),payload=message.subarray(5);
    if(tag==='R'){if(authenticated||payload.length!==4||payload.readInt32BE()!==0)throw Error('Only local trust-auth profile supported');authenticated=true}
    else if(tag==='Z'){if(!authenticated||payload.length!==1||payload[0]!==73)throw Error('Invalid startup readiness');break}
    else if(!['S','K','N'].includes(tag))throw Error('Unsupported startup response');
   }
   return probe;
  }catch(error){probe.stop(error as Error);throw error}finally{clearTimeout(timeout)}
 }
 async query(sql:string,parameters:readonly string[]=[]):Promise<Response>{
  if(this.closed||this.busy)throw Error('Closed or busy original connection');
  if(parameters.length>1024)throw Error('Parameter budget exceeded');
  const source=z(sql),values=parameters.map(string);
  if(source.length+values.reduce((n,v)=>n+v.length,0)>4_194_304)throw Error('Request budget exceeded');
  const parse=frame('P',Buffer.concat([z(''),source,i16(values.length),...values.map(()=>i32(25))]));
  const bind=frame('B',Buffer.concat([z(''),z(''),i16(0),i16(values.length),...values.flatMap(v=>[i32(v.length),v]),i16(0)]));
  const describe=frame('D',Buffer.concat([Buffer.from('P'),z('')]));
  const execute=frame('E',Buffer.concat([z(''),i32(0)]));
  this.busy=true;const timeout=setTimeout(()=>this.stop(Error('Native query deadline')),5000);
  const originalFrames:string[]=[],fields:string[]=[],rows:(string|null)[][]=[];let command='',error:Error|undefined,total=0,described=false;
  try{
   this.socket.write(Buffer.concat([parse,bind,describe,execute,frame('S',Buffer.alloc(0))]));
   for(;;){const message=await this.next();total+=message.length;
    if(total>8_388_608||originalFrames.length>=20000)throw Error('Response budget exceeded');originalFrames.push(message.toString('base64'));
    const tag=String.fromCharCode(message[0]),body=message.subarray(5);let offset=0;
    const read16=()=>{if(offset+2>body.length)throw Error('Truncated response');const n=body.readInt16BE(offset);offset+=2;return n};
    const read32=()=>{if(offset+4>body.length)throw Error('Truncated response');const n=body.readInt32BE(offset);offset+=4;return n};
    const cstring=()=>{const end=body.indexOf(0,offset);if(end<0)throw Error('Unterminated response string');const result=utf8.decode(body.subarray(offset,end));offset=end+1;return result};
    if(tag==='T'){
     if(described)throw Error('Duplicate row description');described=true;const count=read16();if(count<0||count>1024)throw Error('Field budget');
     for(let i=0;i<count;i++){fields.push(cstring());if(offset+18>body.length)throw Error('Truncated field description');if(body.readInt16BE(offset+16)!==0)throw Error('Unexpected binary format');offset+=18}
     if(offset!==body.length)throw Error('Trailing row description');
    }else if(tag==='D'){
     const count=read16();if(!described||count!==fields.length||rows.length>=10000)throw Error('Row shape/budget');const row:(string|null)[]=[];
     for(let i=0;i<count;i++){const length=read32();if(length===-1)row.push(null);else{if(length<0||offset+length>body.length)throw Error('Invalid cell length');row.push(utf8.decode(body.subarray(offset,offset+length)));offset+=length}}
     if(offset!==body.length)throw Error('Trailing row bytes');rows.push(row);
    }else if(tag==='C'){if(command)throw Error('Multiple command completion');command=cstring();if(offset!==body.length)throw Error('Trailing command bytes')}
    else if(tag==='E'){const parts:Record<string,string>={};while(offset<body.length&&body[offset]!==0){const key=String.fromCharCode(body[offset++]);parts[key]=cstring()};error=Object.assign(Error(parts.M??'Native error'),{code:parts.C})}
    else if(tag==='Z'){
     if(body.length!==1||!['I','T','E'].includes(String.fromCharCode(body[0])))throw Error('Invalid settlement status');
     const ready=String.fromCharCode(body[0]) as Response['ready'];if(error){Object.assign(error,{ready,originalFrames:Object.freeze(originalFrames)});throw error}if(!command)throw Error('Missing original command completion');
     if(command.startsWith('SELECT ')&&(!/^SELECT (0|[1-9][0-9]*)$/.test(command)||BigInt(command.slice(7))!==BigInt(rows.length)))throw Error('Original SELECT count mismatch');
     return Object.freeze({fields:Object.freeze(fields),rows:Object.freeze(rows.map(r=>Object.freeze(r))),command,ready,originalRequestFrames:Object.freeze([parse,bind,describe,execute,frame('S',Buffer.alloc(0))].map(v=>v.toString('base64'))),originalFrames:Object.freeze(originalFrames)});
    }else if(!['1','2','n','N','S'].includes(tag))throw Error('Unsupported query response');
   }
  }catch(e){if(!(e as any).code)this.stop(e as Error);throw e}finally{clearTimeout(timeout);this.busy=false}
 }
 close(){if(!this.closed){this.socket.write(frame('X',Buffer.alloc(0)));this.socket.end();this.closed=true}}
}
