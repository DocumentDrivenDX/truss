import {mock} from 'bun:test';
import {EventEmitter} from 'node:events';
const assert=(b:unknown,m:string)=>{if(!b)throw Error(m);};
const frame=(k:string,b:Buffer)=>{const o=Buffer.alloc(b.length+5);o[0]=k.charCodeAt(0);o.writeUInt32BE(b.length+4,1);b.copy(o,5);return o;};
const command=(s:string)=>frame('C',Buffer.from(s+'\0'));const ready=(s:string)=>frame('Z',Buffer.from(s));
const names=['original_actor','effective_actor','native_superuser','native_bypass','native_encoding'];
function table(ns:string[],vals:(string|Buffer|null)[][],oids=ns.map(()=>25)) {const n=Buffer.alloc(2);n.writeUInt16BE(ns.length);const desc=ns.map((name,i)=>{const t=Buffer.alloc(18);t.writeUInt32BE(oids[i],6);t.writeInt16BE(-1,10);t.writeInt32BE(-1,12);return Buffer.concat([Buffer.from(name+'\0'),t]);});return [frame('T',Buffer.concat([n,...desc])),...vals.map(vs=>frame('D',Buffer.concat([n,...vs.map(v=>{const b=v===null?null:Buffer.isBuffer(v)?v:Buffer.from(v);const l=Buffer.alloc(4);l.writeInt32BE(b===null?-1:b.length);return b===null?l:Buffer.concat([l,b]);})]))),command('SELECT '+vals.length)];}
class Stream extends EventEmitter {destroyed=false;closed=false; constructor(readonly owner:Client){super();}destroy(error?:Error){if(this.closed)return;this.destroyed=true;this.closed=true;if(error)this.owner.emit('error',error);this.emit('close');}}
type Hook=(q:string,n:number,frames:Buffer[],c:Client)=>Buffer[]|Promise<Buffer[]>;
class Client extends EventEmitter {connection:{stream:Stream};calls:string[]=[];status='I';released=0;constructor(readonly hook?:Hook){super();this.connection={stream:new Stream(this)};this.connection.stream.on('data',()=>{});}async query(q:{text:string}){this.calls.push(q.text);let fs:Buffer[];
 if(q.text.startsWith('SELECT SESSION_USER AS'))fs=table(names,[['alice','alice','false','false','UTF8']],[19,19,25,25,25]);
 else if(q.text.startsWith('SELECT session_user'))fs=table(names,[['alice','alice','false','false','UTF8']]);
 else if(q.text.startsWith('SELECT *'))fs=table(['staff_id'],[['alice']]);
 else if(q.text.startsWith('BEGIN')){this.status='T';fs=[command('BEGIN')];}
 else if(q.text==='COMMIT'||q.text==='ROLLBACK'){this.status='I';fs=[command(q.text)];}
 else if(q.text==='SELECT 1')fs=table(['one'],[['1']]);
 else fs=[command('RESET')];
 fs=this.hook?await this.hook(q.text,this.calls.length,fs,this):fs;
 this.connection.stream.emit('data',Buffer.concat([...fs,ready(this.status)]));return {rows:[]};}
 release(){this.released++;}}
let clients:Client[]=[];
mock.module('pg',()=>({Pool:class{async connect(){const c=clients.shift();if(!c)throw Error('No client');return c;}async end(){}},DatabaseError:class extends Error{}}));
const {createPgConnectionSource}=await import('/private/tmp/truss-security-main-integration/packages/pg-runtime/src/index.ts');
const results:{name:string;passed:boolean;detail?:unknown}[]=[];
const opts={ordinaryPrincipal:'alice',ordinarySubject:{schema:'diag',routine:'subject',keyColumns:['staff_id']}};
async function run(name:string,options:any,hook:Hook|undefined,expected?:string){const client=new Client(hook);clients=[client];const host=createPgConnectionSource({},options);let conn:any;let caught='';try{conn=await host.source.acquire();await conn.begin({isolation:'repeatable_read',accessMode:'read_only'});await conn.rollback();await conn.release();await host.close();}catch(e){caught=String(e);assert(expected&&caught.includes(expected),name+': '+caught);assert(host.quarantinedCount()===1,name+' missing quarantine');await host.shutdownQuarantinedTransports();}assert(expected?!!caught:!caught,name+' outcome');results.push({name,passed:true});return client;}
await run('direct principal and text subject',opts,undefined);
const nameClient=await run('observer NAME input and TEXT output',{...opts,ordinaryPrincipalObserver:{schema:'diag',routine:'observe'},ordinarySubject:{...opts.ordinarySubject,actorCarrier:'name'}},undefined);
assert(nameClient.calls.some(s=>s==='SELECT * FROM "diag"."subject"(SESSION_USER)'),'name carrier');
for(const [name,vs] of [ ['wrong session',['other','alice','false','false','UTF8']], ['superuser',['alice','alice','true','false','UTF8']], ['bypass',['alice','alice','false','true','UTF8']], ['encoding',['alice','alice','false','false','LATIN1']], ['boolean spelling',['alice','alice','f','false','UTF8']] ] as const)await run(name,opts,(q,n,fs)=>n===1?table(names,[[...vs]]):fs,'Pinned ordinary principal unavailable');
await run('wrong principal OID',opts,(q,n,fs)=>n===1?table(names,[['alice','alice','false','false','UTF8']],[19,25,25,25,25]):fs,'Original principal response unavailable');
await run('multiple principal rows',opts,(q,n,fs)=>n===1?table(names,[['alice','alice','false','false','UTF8'],['alice','alice','false','false','UTF8']]):fs,'Original principal response unavailable');
await run('effective identity after reset',opts,(q,n,fs)=>n===5?table(names,[['alice','other','false','false','UTF8']]):fs,'Pinned ordinary principal unavailable');
for(const [name,ns,vs,oids] of [ ['subject absent',['staff_id'],[],[25]], ['subject duplicate',['staff_id'],[['alice'],['alice']],[25]], ['subject wrong ordered name',['different'],[['alice']],[25]], ['subject wrong OID',['staff_id'],[['alice']],[19]], ['subject null',['staff_id'],[[null]],[25]], ['subject oversized',['staff_id'],[['x'.repeat(65537)]],[25]] ] as any[]) await run(name,opts,(q,n,fs)=>q.startsWith('SELECT *')?table(ns,vs,oids):fs,'Original subject binding unavailable');
await run('subject invalid UTF8',opts,(q,n,fs)=>q.startsWith('SELECT *')?table(['staff_id'],[[Buffer.from([255])]]):fs,'Original response refused');
await run('subject exact 64KiB',opts,(q,n,fs)=>q.startsWith('SELECT *')?table(['staff_id'],[['x'.repeat(65536)]]):fs);
await run('release reset failure',{ordinaryPrincipal:'alice'},(q,n,fs)=>n===9?table(names,[['wrong','alice','false','false','UTF8']]):fs,'Pinned ordinary principal unavailable');
{
 let resume!:()=>void;const hold=new Promise<void>(r=>resume=r);let entered!:()=>void;const pending=new Promise<void>(r=>entered=r);
 const client=new Client(async(q,n,fs)=>{if(q.startsWith('SELECT *')){entered();await hold;}return fs;});clients=[client];const host=createPgConnectionSource({},opts);const c=await host.source.acquire();const begin=c.begin({isolation:'repeatable_read',accessMode:'read_only'});await pending;const before=client.calls.length;
 for(const [label,call] of [['execute',()=>c.execute({sql:'SELECT 1',parameters:[]})],['rollback',()=>c.rollback()],['commit',()=>c.commit()],['release',()=>c.release()]] as const){let message='';try{await call();}catch(e){message=String(e);}assert(message.includes('Subject preflight still pending'),'pending '+label);}
 assert(client.calls.length===before,'overlap dispatched');resume();await begin;await c.rollback();await c.release();await host.close();results.push({name:'subject pending refuses four overlapping operations without dispatch',passed:true});
}
{
 let resume!:()=>void;const hold=new Promise<void>(r=>resume=r);let entered!:()=>void;const pending=new Promise<void>(r=>entered=r);
 const client=new Client(async(q,n,fs)=>{if(q==='SELECT 1'){entered();await hold;}return fs;});clients=[client];const host=createPgConnectionSource({},{ordinaryPrincipal:'alice'});const c=await host.source.acquire();await c.begin({isolation:'read_committed',accessMode:'read_only'});const first=c.execute({sql:'SELECT 1',parameters:[]});await pending;const count=client.calls.length;let error='';try{await c.rollback();}catch(e){error=String(e);}assert(error.includes('operation still pending')&&client.calls.length===count,'busy exclusion');resume();await first;await c.rollback();await c.release();await host.close();results.push({name:'execute pending refuses rollback without dispatch',passed:true});
}
{
 const client=new Client((q,n,fs,c)=>n===1?new Promise((_,reject)=>c.connection.stream.once('close',()=>reject(Error('closed')))):fs);clients=[client];const host=createPgConnectionSource({},{ordinaryPrincipal:'alice',originalResponseTimeoutMs:10});const start=performance.now();let error='';try{await host.source.acquire();}catch(e){error=String(e);}assert(error.includes('Original response deadline'),'deadline refusal');assert(client.connection.stream.destroyed&&host.quarantinedCount()===1,'deadline custody');await host.shutdownQuarantinedTransports();results.push({name:'10ms selected deadline destroys transport and retains quarantine',passed:true,detail:{elapsedMs:performance.now()-start}});
}
{
 const selected:any={ordinaryPrincipal:'alice',ordinarySubject:{schema:'diag',routine:'subject',keyColumns:['staff_id']}};const client=new Client();clients=[client];const host=createPgConnectionSource({},selected);selected.ordinaryPrincipal='other';selected.ordinarySubject.schema='evil';selected.ordinarySubject.routine='wrong';selected.ordinarySubject.keyColumns[0]='wrong';const c=await host.source.acquire();await c.begin({isolation:'repeatable_read',accessMode:'read_only'});assert(client.calls.includes('SELECT * FROM "diag"."subject"(SESSION_USER::pg_catalog.text)'),'selection mutation');await c.rollback();await c.release();await host.close();results.push({name:'construction copies caller and selected routine/keys',passed:true});
}
console.log(JSON.stringify({scope:'Actual runtime plus original native frame decoder/query wrapper with deterministic synthetic pg driver; no native/authenticated deployment or real socket scheduling claim.',count:results.length,results},null,2));
