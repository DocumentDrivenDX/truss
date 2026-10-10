/** One-query private pre-parser probe; no full driver producer qualification. */
import {createRequire} from 'node:module';
import {writeFile} from 'node:fs/promises';
import {decodeResponseFrame,ResponseIngress} from '@documentdrivendx/truss-pg-runtime';
const require=createRequire(new URL('../packages/pg-runtime/package.json',import.meta.url));const {Client}=require('pg');
const inspected=Bun.spawnSync(['/usr/local/bin/docker','inspect','ashlar-e2e-truss-pg17']);if(inspected.exitCode)throw Error('Sandbox unavailable');
const container=JSON.parse(new TextDecoder().decode(inspected.stdout))[0];if(container.Config.Labels['ashlar.purpose']!=='end-to-end-development')throw Error('Wrong sandbox');
const password=container.Config.Env.find((s:string)=>s.startsWith('POSTGRES_PASSWORD=')).slice(18);
const client=new Client({host:'127.0.0.1',port:15432,user:'postgres',password,database:'truss_e2e',connectionTimeoutMillis:5000,types:{getTypeParser:()=> (text:string)=>text}});
const chunks:Uint8Array[]=[];let bytes=0;let overflow=false;
const capture=(chunk:Uint8Array)=>{bytes+=chunk.length;if(bytes>65536){overflow=true;return;}chunks.push(Uint8Array.from(chunk));};
try{
 await client.connect();await client.query('BEGIN');const stream=client.connection.stream;
 const handlers=stream.listeners('data');if(handlers.length!==1)throw Error('Unqualified original parser listener composition');
 const originalParser=handlers[0];const ingress=new ResponseIngress({maxFrameBytes:65536,maxFields:16,maxTotalBytes:65536,maxFrames:8});
 const guarded=(chunk:Uint8Array)=>{capture(chunk);try{ingress.feed(chunk,frame=>originalParser.call(stream,Buffer.from(frame.buffer,frame.byteOffset,frame.byteLength)));}catch{stream.destroy(Error('Probe ingress refusal'));}};
 client.on('error',()=>{});stream.removeListener('data',originalParser);stream.on('data',guarded);
 const sql="SELECT 1/0";
 const ready=new Promise<void>((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Original ready unavailable')),3000);client.connection.once('readyForQuery',()=>{clearTimeout(timer);resolve();});});
 let errorCode:string|undefined;
 try{await client.query({text:sql,rowMode:'array'});}catch(error:any){errorCode=error.code;}
 await ready;if(errorCode!=='22012')throw Error('Expected native error unavailable');stream.off('data',guarded);stream.on('data',originalParser);ingress.finish();
 if(overflow)throw Error('Probe byte cap exceeded');
 const wire=new Uint8Array(bytes);let at=0;for(const chunk of chunks){wire.set(chunk,at);at+=chunk.length;}
 const frames=[];at=0;while(at<wire.length){
  if(at+5>wire.length)throw Error('Incomplete original frame');
  let length=0n;for(let i=1;i<=4;i++)length=length*256n+BigInt(wire[at+i]);
  if(length<4n||length>65535n||length+1n>BigInt(wire.length-at))throw Error('Original framing refusal');
  const end=at+Number(length)+1;frames.push(decodeResponseFrame(wire.subarray(at,end),{maxFrameBytes:65536,maxFields:16}));at=end;
 }
 if(frames.map(frame=>frame.kind).join('')!=='EZ'||frames[0].fields.find(field=>field.tag==='C')?.value!=='22012'||frames[1].fields[0].status!=='E')throw Error('Original error/status inventory mismatch');
 const rollback=await client.query('ROLLBACK');if(rollback.command!=='ROLLBACK')throw Error('Native rollback unavailable');
 await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/native-wire-error.json',import.meta.url),JSON.stringify({driver:'pg/8.16.3',sql,bytes,frames,beforeParser:true,ingressAccounting:ingress.accounting,driverErrorCode:errorCode,rollbackCommand:rollback.command,qualification:'One original E/Z response for division-by-zero inside BEGIN, followed by confirmed ROLLBACK captured on local PostgreSQL 17.9 under Bun. Private probe replaces one existing data listener and forwards admitted complete frames to the original pg parser. Decoder/frame copy limits apply before parser forwarding; original socket chunk/transport allocation, full response/error/notice kinds, native uncertainty containment and original-query issuer/epoch authority remain unqualified. No Truss installation or complete producer/profile adoption.'},null,2)+'\n');
 console.log('Original native ErrorResponse/failed ReadyForQuery match; rollback confirmed.');
}finally{await client.end();}
