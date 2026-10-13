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
class NativeError extends Error { code='23505'; }
let clients:Client[]=[];
mock.module('pg',()=>({Pool:class{async connect(){const c=clients.shift();if(!c)throw Error('No client');return c;}async end(){}},DatabaseError:NativeError}));
const {createPgConnectionSource}=await import('/private/tmp/truss-security-main-integration/packages/pg-runtime/src/index.ts');
const results:{name:string;passed:boolean;detail?:unknown}[]=[];
const options={ordinaryPrincipal:'alice',ordinarySubject:{schema:'diag',routine:'subject',keyColumns:['staff_id','ordinal','unicode']}};
const transaction={isolation:'repeatable_read' as const,accessMode:'read_only' as const};
function refusal(name:string,fn:()=>unknown,expected?:string){let message='';try{fn();}catch(e){message=String(e);}assert(message&&(!expected||message.includes(expected)),name+': '+message);results.push({name,passed:true});}
function subjectHook(q:string,n:number,fs:Buffer[]){return q.startsWith('SELECT *')?table(options.ordinarySubject.keyColumns,[['alice','9007199254740993','\ufeffΔ🚀']]):fs;}
function hostWith(hook:Hook=subjectHook,opts:any=options){const client=new Client(hook);clients=[client];return {client,host:createPgConnectionSource({},opts)};}
{
 const {host}=hostWith();const c=await host.source.acquire();
 refusal('before begin',()=>host.observeOrdinarySubject(c),'Active original');
 for(const x of [{},null,undefined,{...c},new Proxy(c,{})])refusal('foreign receiver '+String(x===null?'null':typeof x),()=>host.observeOrdinarySubject(x as any),'Foreign');
 await c.begin(transaction);const first=host.observeOrdinarySubject(c);
 assert(first.version==='truss.native.subject-observation/0.1'&&first.principal==='alice','metadata');
 assert(JSON.stringify(first.keyValues)===JSON.stringify(['alice','9007199254740993','\ufeffΔ🚀']),'original carriers');
 assert(JSON.stringify(first.keyHex)===JSON.stringify(first.keyValues.map(v=>Buffer.from(v).toString('hex'))),'hex correspondence');
 assert(first.keyColumns.join(',')==='staff_id,ordinal,unicode','ordered columns');
 assert(Object.isFrozen(first)&&[first.keyColumns,first.keyValues,first.keyHex].every(Object.isFrozen),'deep immutable');
 const prior=JSON.stringify(first);
 for(const fn of [()=>{(first as any).principal='bob';},()=>{(first.keyValues as string[])[0]='bob';},()=>{(first.keyHex as string[]).push('00');},()=>{(first.keyColumns as string[]).reverse();}]){try{fn();}catch{}}
 assert(JSON.stringify(first)===prior&&host.observeOrdinarySubject(c)===first,'mutated observation');results.push({name:'exact composite numeric/BOM/Unicode carriers, bytes/order, immutable nested arrays',passed:true});
 const other=hostWith();refusal('cross-host identity',()=>other.host.observeOrdinarySubject(c),'Foreign');await other.host.close();
 await c.commit();refusal('after confirmed commit',()=>host.observeOrdinarySubject(c),'Active original');assert(JSON.stringify(first)===prior,'prior snapshot changed');
 await c.begin(transaction);const second=host.observeOrdinarySubject(c);assert(second!==first&&JSON.stringify(second)===prior,'new transaction reused snapshot');results.push({name:'new transaction recaptures snapshot; retained old snapshot unchanged',passed:true});
 await c.rollback();refusal('after confirmed rollback',()=>host.observeOrdinarySubject(c),'Active original');await c.release();refusal('after release',()=>host.observeOrdinarySubject(c),'unavailable');await host.close();
}
{
 const {host}=hostWith();const c=await host.source.acquire();await c.begin(transaction);const before=JSON.stringify(host.observeOrdinarySubject(c));await c.quarantine();refusal('after explicit quarantine',()=>host.observeOrdinarySubject(c),'unavailable');await host.shutdownQuarantinedTransports();refusal('after quarantined transport shutdown',()=>host.observeOrdinarySubject(c),'unavailable');results.push({name:'quarantine retains old observation only as immutable prior data',passed:true,detail:{before}});
}
for(const phase of ['begin','execute','commit','rollback'] as const){
 let release!:()=>void;const held=new Promise<void>(r=>release=r);let entered!:()=>void;const reached=new Promise<void>(r=>entered=r);
 const {host,client}=hostWith(async(q,n,fs)=>{if(phase==='begin'&&q.startsWith('SELECT *')||phase==='execute'&&q==='SELECT 1'||phase==='commit'&&q==='COMMIT'||phase==='rollback'&&q==='ROLLBACK'){entered();await held;}return subjectHook(q,n,fs);});
 const c=await host.source.acquire();if(phase!=='begin')await c.begin(transaction);
 const op=phase==='begin'?c.begin(transaction):phase==='execute'?c.execute({sql:'SELECT 1',parameters:[]}):phase==='commit'?c.commit():c.rollback();await reached;const count=client.calls.length;
 refusal('while '+phase+' pending',()=>host.observeOrdinarySubject(c));assert(client.calls.length===count,'observer dispatched query');release();await op;
 if(phase==='begin'||phase==='execute'){assert(host.observeOrdinarySubject(c).principal==='alice','settled availability');await c.rollback();}else refusal('after '+phase+' settles',()=>host.observeOrdinarySubject(c),'Active original');
 await c.release();await host.close();
}
{
 const {host}=hostWith(subjectHook,{ordinaryPrincipal:'alice'});const c=await host.source.acquire();await c.begin(transaction);refusal('principal-only host has no invented subject',()=>host.observeOrdinarySubject(c),'Active original');await c.rollback();await c.release();await host.close();
}
{
 const errorFrames=()=>[frame('E',Buffer.from('SERROR\0C23505\0Msynthetic native violation\0\0')),ready('I')];
 const {host}=hostWith((q,n,fs,c)=>{if(q==='COMMIT'){c.status='I';c.connection.stream.emit('data',Buffer.concat(errorFrames()));throw new NativeError('commit rejected');}return subjectHook(q,n,fs);});
 const c=await host.source.acquire();await c.begin(transaction);const prior=host.observeOrdinarySubject(c);const outcome=await c.commit();assert(typeof outcome==='object'&&outcome.status==='rejected'&&outcome.sqlState==='23505','classified rejection');refusal('classified rejected commit followed by confirmed rollback clears observation',()=>host.observeOrdinarySubject(c),'Active original');assert(prior.keyValues[0]==='alice','old snapshot mutation');await c.release();await host.close();
}
{
 const {host}=hostWith((q,n,fs,c)=>{if(q==='SELECT 1'){c.status='E';c.connection.stream.emit('data',Buffer.concat([frame('E',Buffer.from('SERROR\0C23505\0Msynthetic violation\0\0')),ready('E')]));throw new NativeError('execute rejected');}return subjectHook(q,n,fs);});
 const c=await host.source.acquire();await c.begin(transaction);const before=host.observeOrdinarySubject(c);let rejected=false;try{await c.execute({sql:'SELECT 1',parameters:[]});}catch{rejected=true;}assert(rejected,'missing native error');
 let after:unknown;try{after=host.observeOrdinarySubject(c);}catch(e){after=String(e);}
 assert(typeof after==='string'&&after.includes('Active original subject observation unavailable'),'failed transaction snapshot remained available');
 results.push({name:'native failed-transaction response invalidates accessor',passed:true});
 await c.rollback();await c.begin(transaction);assert(host.observeOrdinarySubject(c)!==before,'failed observation reused');await c.rollback();await c.release();await host.close();
}
{
 let reads=0;const {host}=hostWith((q,n,fs)=>q.startsWith('SELECT *')?table(options.ordinarySubject.keyColumns,[[++reads===1?'alice':'new-subject','9007199254740993','\ufeffΔ🚀']]):fs);
 const c=await host.source.acquire();await c.begin(transaction);const prior=host.observeOrdinarySubject(c);await c.rollback();await c.begin(transaction);const current=host.observeOrdinarySubject(c);assert(prior.keyValues[0]==='alice'&&current.keyValues[0]==='new-subject'&&prior!==current&&reads===2,'recaptured bytes');await c.rollback();await c.release();await host.close();results.push({name:'new transaction recaptures changed original helper bytes without mutating retained prior observation',passed:true});
}
console.log(JSON.stringify({scope:'Actual current runtime and original framed-response parser under deterministic synthetic pg driver. No native server/authenticated deployment or live source authority claim.',count:results.length,results},null,2));
