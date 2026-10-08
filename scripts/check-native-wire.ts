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
 await client.connect();const stream=client.connection.stream;
 const handlers=stream.listeners('data');if(handlers.length!==1)throw Error('Unqualified original parser listener composition');
 const originalParser=handlers[0];const ingress=new ResponseIngress({maxFrameBytes:65536,maxFields:16,maxTotalBytes:65536,maxFrames:8});
 const guarded=(chunk:Uint8Array)=>{capture(chunk);try{ingress.feed(chunk,frame=>originalParser.call(stream,Buffer.from(frame.buffer,frame.byteOffset,frame.byteLength)));}catch{stream.destroy(Error('Probe ingress refusal'));}};
 client.on('error',()=>{});stream.removeListener('data',originalParser);stream.on('data',guarded);
 const sql="SELECT 9007199254740993123::bigint AS duplicate,NULL::text AS duplicate";
 const result=await client.query({text:sql,rowMode:'array'});stream.off('data',guarded);stream.on('data',originalParser);ingress.finish();
 if(overflow)throw Error('Probe byte cap exceeded');
 const wire=new Uint8Array(bytes);let at=0;for(const chunk of chunks){wire.set(chunk,at);at+=chunk.length;}
 const frames=[];at=0;while(at<wire.length){
  if(at+5>wire.length)throw Error('Incomplete original frame');
  let length=0n;for(let i=1;i<=4;i++)length=length*256n+BigInt(wire[at+i]);
  if(length<4n||length>65535n||length+1n>BigInt(wire.length-at))throw Error('Original framing refusal');
  const end=at+Number(length)+1;frames.push(decodeResponseFrame(wire.subarray(at,end),{maxFrameBytes:65536,maxFields:16}));at=end;
 }
 if(frames.map(frame=>frame.kind).join('')!=='TDCZ')throw Error('Unexpected complete response inventory');
 if(frames[0].fields.map(field=>field.name).join(',')!=='duplicate,duplicate'||frames[2].fields[0].command!=='SELECT 1'||frames[2].fields[0].affectedRows!=='1'||frames[3].fields[0].status!=='I')throw Error('Original descriptor/command/status mismatch');
 if(frames[1].fields[0].hex!==Buffer.from('9007199254740993123').toString('hex')||frames[1].fields[1].hex!==null)throw Error('Original raw row mismatch');
 await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/native-wire.json',import.meta.url),JSON.stringify({driver:'pg/8.16.3',sql,bytes,frames,beforeParser:true,ingressAccounting:ingress.accounting,driverResult:{fields:result.fields.map((field:any)=>field.name),rows:result.rows,command:result.command,rowCount:String(result.rowCount)},qualification:'One original T/D/C/Z response captured on local PostgreSQL 17.9 under Bun. Private probe replaces one existing data listener and forwards admitted complete frames to the original pg parser. Decoder/frame copy limits apply before parser forwarding; original socket chunk/transport allocation, full response/error/notice kinds, native uncertainty containment and original-query issuer/epoch authority remain unqualified. No Truss installation or complete producer/profile adoption.'},null,2)+'\n');
 console.log('Original native RowDescription/DataRow/CommandComplete/ReadyForQuery subset matches.');
}finally{await client.end();}
