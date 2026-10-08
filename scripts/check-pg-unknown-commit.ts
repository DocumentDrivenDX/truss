/** Isolated child probe: deliberate lost driver completion after original server commit frame. */
import {createPgConnectionSource,createFileQueryJournal,decodeResponseFrame,type OriginalQueryJournal} from '@documentdrivendx/truss-pg-runtime';
import {createEngineExecutor} from '@documentdrivendx/truss-postgresql';
import {createRequire} from 'node:module';
import {mkdtemp,readFile,readdir,writeFile} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import {join} from 'node:path';
const require=createRequire(new URL('../packages/pg-runtime/package.json',import.meta.url));
const {Client}=require('pg');
const probe=Bun.spawnSync(['/usr/local/bin/docker','inspect','ashlar-e2e-truss-pg17']);
if(probe.exitCode)throw Error('Existing sandbox unavailable');
const container=JSON.parse(new TextDecoder().decode(probe.stdout))[0];
if(container.Config.Labels['ashlar.purpose']!=='end-to-end-development')throw Error('Wrong sandbox');
const password=container.Config.Env.find((s:string)=>s.startsWith('POSTGRES_PASSWORD=')).slice(18);
const config={host:'127.0.0.1',port:15432,user:'postgres',password,database:'truss_e2e',connectionTimeoutMillis:5000};
const admin=new Client({...config,types:{getTypeParser(){return (text:string)=>text;}}});
const table='truss_uncertain_'+randomUUID().replaceAll('-','');
const directory=await mkdtemp('/private/tmp/truss-unknown-commit-');
const original=createFileQueryJournal(directory);let injected=false;
const journal:OriginalQueryJournal={begin(text,values,custody){
 const retained=original.begin(text,values,custody);
 return {frame(bytes){
  retained.frame(bytes);
  if(text==='COMMIT'&&decodeResponseFrame(bytes,{maxFrameBytes:1048576,maxFields:2048}).kind==='C'){
   injected=true;throw Error('Deliberate driver completion loss after original commit frame');
  }
 },finish:outcome=>retained.finish(outcome)};
}};
const host=createPgConnectionSource({...config,max:1,options:'-c statement_timeout=5000'},{journal});
const executor=createEngineExecutor(host.source);let created=false;
try{
 await admin.connect();await admin.query('CREATE TABLE '+table+'(id integer PRIMARY KEY)');created=true;
 const result=await executor.withTransaction({isolation:'read_committed',accessMode:'read_write'},async tx=>{
  const write=await executor.execute(tx,{sql:'INSERT INTO '+table+' VALUES(1)',parameters:[]});
  if(write.status!=='ok')throw Error('Native write failed before fault');return 'withheld_application_result';
 });
 if(!injected||result.status!=='error'||result.error.code!=='commit_unknown'||result.error.retryScope!=='none')throw Error('Unknown commit classification missing');
 const independent=await admin.query('SELECT count(*)::text AS count FROM '+table);
 if(independent.rows[0].count!=='1')throw Error('Independent committed effect missing');
 if(host.quarantinedCount()!==1)throw Error('Original custody not quarantined');
 let closeRefused=false;try{await host.close();}catch{closeRefused=true;}if(!closeRefused)throw Error('Unsettled source cleanup admitted');
 const files=await readdir(directory);const requests=[];const retained=[];
 for(const file of files){
  const bytes=await readFile(join(directory,file));const records=bytes.toString('utf8').trimEnd().split('\n').map(line=>JSON.parse(line));
  if(records[0].text==='COMMIT'){
   const frames=records.filter(record=>record.kind==='frame').map(record=>decodeResponseFrame(Buffer.from(record.hex,'hex'),{maxFrameBytes:1048576,maxFields:2048}));
   if(frames.length!==1||frames[0].kind!=='C'||frames[0].fields[0].command!=='COMMIT')throw Error('Original COMMIT frame not retained before loss');
  }
  requests.push(records[0]);retained.push({sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex'),outcome:records.at(-1)});
 }
 requests.sort((a,b)=>BigInt(a.custody.ordinal)<BigInt(b.custody.ordinal)?-1:1);
 if(requests.some((request,index)=>request.custody.ordinal!==String(index)||request.custody.lease!==requests[0].custody.lease))throw Error('Original local custody sequence missing');
 const sql=requests.map(request=>request.text);
 if(sql.length!==3||sql.filter(text=>text==='COMMIT').length!==1||sql.some(text=>text==='ROLLBACK'))throw Error('Replay or guessed rollback after uncertainty');
 const unknown=retained.filter(record=>record.outcome.kind==='outcome'&&record.outcome.outcome==='uncertain');
 if(unknown.length!==1)throw Error('Original uncertainty not retained');
 await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/pg-unknown-commit.json',import.meta.url),JSON.stringify({driver:'pg/8.16.3',loader:'bun/'+Bun.version,originalJournalDirectory:directory,result,quarantined:1,closeRefused,independentCommittedRows:'1',requests:3,commitSubmissions:1,rollbackSubmissions:0,retained,qualification:'Actual local PostgreSQL 17.9 commit effect independently observed after deliberate driver completion loss at retained original CommandComplete before parser forwarding. Adapter reports commit_unknown/no retry and keeps quarantine. Private originals retained; isolated child exits after fixture removal. This is not natural packet-loss/crash testing, general uncertainty settlement, protected Truss installation or source ACK authority.'},null,2)+'\n');
 console.log('Native lost commit completion: committed effect observed, unknown outcome retained, no replay/rollback.');
}finally{
 if(created)await admin.query('DROP TABLE '+table);await admin.end();
}
// Quarantine deliberately remains unresolved in the host object. End this isolated
// probe process; do not expose process termination as a library recovery operation.
process.exit(0);
