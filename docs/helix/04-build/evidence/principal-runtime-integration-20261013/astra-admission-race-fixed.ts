import {mock} from 'bun:test';
import {EventEmitter} from 'node:events';
class Stream extends EventEmitter { destroyed=false;closed=false; destroy(){this.destroyed=true;this.closed=true;this.emit('close');} }
const frame=(kind:string,body:Buffer)=>{const out=Buffer.alloc(body.length+5);out[0]=kind.charCodeAt(0);out.writeUInt32BE(body.length+4,1);body.copy(out,5);return out;};
const z=(s:string)=>frame('Z',Buffer.from(s));const c=(s:string)=>frame('C',Buffer.from(s+'\0'));
function row(names:string[],values:string[]){const fields=names.map(name=>{const tail=Buffer.alloc(18);tail.writeUInt32BE(25,6);tail.writeInt16BE(-1,10);tail.writeInt32BE(-1,12);return Buffer.concat([Buffer.from(name+'\0'),tail]);});const n=Buffer.alloc(2);n.writeUInt16BE(names.length);const data=values.map(v=>{const b=Buffer.from(v);const l=Buffer.alloc(4);l.writeInt32BE(b.length);return Buffer.concat([l,b]);});return [frame('T',Buffer.concat([n,...fields])),frame('D',Buffer.concat([n,...data])),c('SELECT 1')];}
let unblock!:()=>void;const blocked=new Promise<void>(r=>unblock=r);
class Client extends EventEmitter {
 connection={stream:new Stream()}; calls:string[]=[]; releaseCalls=0; first=true;status='I';
 constructor(readonly principal:string,readonly gated=false){super();this.connection.stream.on('data',()=>{});}
 async query(q:{text:string}) {this.calls.push(q.text);if(this.gated&&this.first){this.first=false;await blocked;}
 let fs:Buffer[];
 if(q.text.startsWith('SELECT')) fs=row(['original_actor','effective_actor','native_superuser','native_bypass','native_encoding'],[this.principal,this.principal,'false','false','UTF8']);
 else if(q.text.startsWith('BEGIN')){this.status='T';fs=[c('BEGIN')];}
 else if(q.text==='ROLLBACK'){this.status='I';fs=[c('ROLLBACK')];}else fs=[c('RESET')];
 this.connection.stream.emit('data',Buffer.concat([...fs,z(this.status)]));return {rows:[]};
 }
 release(){this.releaseCalls++;}
}
const bad=new Client('wrong');const good=new Client('alice',true);let clients=[bad,good];
mock.module('pg',()=>({Pool:class{async connect(){const c=clients.shift();if(!c)throw Error('No clients');return c;}async end(){}},DatabaseError:class extends Error{}}));
const {createPgConnectionSource}=await import('/private/tmp/truss-security-main-integration/packages/pg-runtime/src/index.ts');
const host=createPgConnectionSource({},{ordinaryPrincipal:'alice'});
const first=host.source.acquire().then(()=>({unexpected:true}),e=>({error:String(e)}));
const second=host.source.acquire();
const refusal=await first;
if(!('error' in refusal)||!refusal.error.includes('Pinned ordinary principal unavailable'))throw Error('First refusal not reproduced');
unblock();
const pending=await second.then(()=>({unexpected:true}),e=>({error:String(e)}));
if(!('error' in pending)||!pending.error.includes('Host admission closed'))throw Error('Pending lease escaped closure');
if(host.quarantinedCount()!==2||good.releaseCalls!==0||bad.releaseCalls!==0)throw Error('Pending checkout custody lost');
const future=await host.source.acquire().then(()=>({unexpected:true}),e=>({error:String(e)}));
if(!('error' in future)||!future.error.includes('Host admission closed'))throw Error('Future admission reopened');
await host.shutdownQuarantinedTransports();
if(good.releaseCalls!==1||bad.releaseCalls!==1||!good.connection.stream.closed||!bad.connection.stream.closed)throw Error('Explicit shutdown incomplete');
console.log(JSON.stringify({first:refusal,second:pending,future,quarantinedCount:host.quarantinedCount(),calls:{bad:bad.calls,good:good.calls},scope:'Synthetic deterministic driver and original framed-response source; actual unchanged runtime logic. No native database or authenticated deployment claim.'},null,2));
