/** Offline native correspondence check. Never resubmits SQL or interprets commit authority. */
import {readdir,readFile,stat,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {ResponseIngress,decodeResponseFrame} from '../packages/pg-runtime/src/wire';
const directory=process.argv[2];if(!directory)throw Error('Original journal directory required');
const files=(await readdir(directory)).filter(name=>/^[0-9a-f-]+\.jsonl$/.test(name));
if(!files.length||files.length>1000)throw Error('Journal inventory outside bounds');
const leases=new Map<string,bigint[]>();
const inventory=[];const sqlStates:string[]=[];let serverErrors=0,completed=0;
for(const name of files){
 const path=join(directory,name);const metadata=await stat(path);
 if(metadata.size>10000000||(metadata.mode&0o777)!==0o600)throw Error('Original journal bounds/permissions');
 const bytes=await readFile(path);if(bytes.at(-1)!==10)throw Error('Torn original record');
 const records=bytes.toString('utf8').trimEnd().split('\n').map(line=>JSON.parse(line));
 const request=records.shift(),outcome=records.pop();
 if(request?.kind!=='request'||typeof request.text!=='string'||!Array.isArray(request.values)||request.values.some((value:unknown)=>value!==null&&typeof value!=='string'))throw Error('Original request missing');
 if(!request.custody||typeof request.custody.lease!=='string'||! /^[0-9a-f-]{36}$/.test(request.custody.lease)||! /^(0|[1-9][0-9]*)$/.test(request.custody.ordinal))throw Error('Local custody missing');
 const ordinals=leases.get(request.custody.lease)??[];ordinals.push(BigInt(request.custody.ordinal));leases.set(request.custody.lease,ordinals);
 if(outcome?.kind!=='outcome'||!['response_complete','server_error'].includes(outcome.outcome))throw Error('Unsettled observation; no replay permitted');
 const limits={maxFrameBytes:1048576,maxFields:2048,maxTotalBytes:4194304,maxFrames:10000};
 const ingress=new ResponseIngress(limits);const frames=[];
 for(const record of records){
  if(record.kind!=='frame'||typeof record.hex!=='string'||! /^(?:[0-9a-f]{2})+$/.test(record.hex))throw Error('Original frame missing');
  ingress.feed(Buffer.from(record.hex,'hex'),frame=>frames.push(decodeResponseFrame(frame,limits)));
 }
 ingress.finish();const errors=frames.filter(frame=>frame.kind==='E');
 if(outcome.outcome==='server_error'){if(errors.length!==1)throw Error('Original error missing');sqlStates.push(errors[0].fields.find(field=>field.tag==='C')!.value!);serverErrors++;}
 else {if(errors.length)throw Error('Error misclassified');completed++;}
 inventory.push({custody:request.custody,locator:name,sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex'),frames:frames.length,outcome:outcome.outcome});
}
for(const ordinals of leases.values()){
 ordinals.sort((a,b)=>a<b?-1:a>b?1:0);
 for(let i=0;i<ordinals.length;i++)if(ordinals[i]!==BigInt(i))throw Error('Missing or duplicate query in observed checkout');
}
await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/query-journal.json',import.meta.url),JSON.stringify({loader:'bun/'+Bun.version,requests:inventory.length,localLeases:leases.size,completed,serverErrors,sqlStates,inventory,qualification:'Separate process reads original retained native query files; bounded original frame replay into decoder only, no database submission. Exact file hashes retained; sensitive SQL/result bytes remain private. Does not prove crash durability, native issuer/epoch or transaction settlement/recovery authority.'},null,2)+'\n');
console.log('Retained native journals verified offline: '+inventory.length+' requests, '+serverErrors+' server errors.');
