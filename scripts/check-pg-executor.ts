import {createPgConnectionSource} from '@documentdrivendx/truss-pg-runtime';
import {createEngineExecutor} from '@documentdrivendx/truss-postgresql';
import {writeFile} from 'node:fs/promises';
const probe=Bun.spawnSync(['/usr/local/bin/docker','inspect','ashlar-e2e-truss-pg17']);
if(probe.exitCode)throw Error('Existing sandbox unavailable');
const container=JSON.parse(new TextDecoder().decode(probe.stdout))[0];
if(container.Config.Labels['ashlar.purpose']!=='end-to-end-development')throw Error('Wrong sandbox');
const password=container.Config.Env.find((s:string)=>s.startsWith('POSTGRES_PASSWORD=')).slice(18);
const host=createPgConnectionSource({host:'127.0.0.1',port:15432,user:'postgres',password,database:'truss_e2e',max:2,
connectionTimeoutMillis:5000,options:'-c statement_timeout=5000 -c lock_timeout=1000'});
const executor=createEngineExecutor(host.source);
try{
 const result=await executor.withTransaction({isolation:'serializable',accessMode:'read_only'},async tx=>{
   const value=await executor.execute(tx,{sql:"SELECT 9007199254740993123::bigint AS duplicate,12345678901234567890.123456789::numeric AS duplicate,NULL::text AS absent",parameters:[]});
   if(value.status!=='ok')throw Error('Native executor read failed');
   if(JSON.stringify(value.value.columns)!==JSON.stringify(['duplicate','duplicate','absent'])||
      JSON.stringify(value.value.rows)!==JSON.stringify([[{state:'text',text:'9007199254740993123'},{state:'text',text:'12345678901234567890.123456789'},{state:'null'}]]))throw Error('Native exact transport mismatch');
   const empty=await executor.execute(tx,{sql:'SELECT 1::text AS retained_name WHERE false',parameters:[]});
   if(empty.status!=='ok'||empty.value.columns[0]!=='retained_name'||empty.value.rows.length!==0)throw Error('Empty description lost');
   const point=await executor.savepoint(tx);if(point.status!=='ok')throw Error('Savepoint failure');
   if((await executor.rollbackToSavepoint(tx,point.value)).status!=='ok'||(await executor.releaseSavepoint(tx,point.value)).status!=='ok')throw Error('Savepoint control failure');
   return {value:value.value,empty:empty.value};
 });
 if(result.status!=='ok'||result.value.durability!=='committed')throw Error('Native settlement failed');
 const run = async (tx:any,sql:string,parameters:any[]=[])=>{const r=await executor.execute(tx,{sql,parameters});if(r.status!=='ok')throw Error('Native statement refused');return r.value;};
 const writes=await executor.withTransaction({isolation:'read_committed',accessMode:'read_write'},async tx=>{
   await run(tx,'CREATE TEMP TABLE truss_pg_write_probe(id bigint PRIMARY KEY,value jsonb)');
   const original='{"large":9007199254740993123456789,"unknown":null}';
   const insert=await run(tx,'INSERT INTO truss_pg_write_probe VALUES($1::bigint,$2::jsonb)',[{position:1,carrier:'integer',text:'9007199254740993123'},{position:2,carrier:'json',text:original}]);
   if(insert.affectedRows!=='1'||insert.command!=='INSERT')throw Error('Write command correspondence');
   const point=await executor.savepoint(tx);if(point.status!=='ok')throw Error('Write savepoint refused');
   const duplicate=await executor.execute(tx,{sql:'INSERT INTO truss_pg_write_probe VALUES(9007199254740993123,NULL)',parameters:[]});
   if(duplicate.status!=='error')throw Error('Native duplicate did not fail');
   if((await executor.rollbackToSavepoint(tx,point.value)).status!=='ok'||(await executor.releaseSavepoint(tx,point.value)).status!=='ok')throw Error('Native error containment failed');
   const retained=await run(tx,'SELECT id,value FROM truss_pg_write_probe');
   if(retained.rows.length!==1||retained.rows[0][0].text!=='9007199254740993123'||!retained.rows[0][1].text.includes('9007199254740993123456789'))throw Error('Prior write not preserved exactly');
   await run(tx,'DROP TABLE truss_pg_write_probe');return {insert,retained};
 });
 if(writes.status!=='ok')throw Error('Write settlement failed');
 const sentinel=Error('controlled native rollback');
 try{await executor.withTransaction({isolation:'read_committed',accessMode:'read_write'},async tx=>{
   await run(tx,'CREATE TEMP TABLE truss_pg_rollback_probe(id integer)');
   await run(tx,'INSERT INTO truss_pg_rollback_probe VALUES(1)');throw sentinel;
 });throw Error('Unexpected callback completion');}catch(error){if(error!==sentinel)throw Error('Original callback exception not preserved');}
 const rollback=await executor.withTransaction({isolation:'read_committed',accessMode:'read_only'},async tx=>run(tx,"SELECT to_regclass('pg_temp.truss_pg_rollback_probe')::text AS absent"));
 if(rollback.status!=='ok'||rollback.value.value.rows[0][0].state!=='null')throw Error('Original rollback not observed');
 let arrived=0;let releaseBarrier:()=>void=()=>{};
 const barrier=new Promise<void>(resolve=>{releaseBarrier=resolve;});
 const lockPair=async(first:string,second:string)=>executor.withTransaction({isolation:'read_committed',accessMode:'read_write'},async tx=>{
   await run(tx,"SET LOCAL lock_timeout='3s'");
   const lock=(key:string)=>executor.execute(tx,{sql:'SELECT pg_advisory_xact_lock($1::bigint)::text AS locked',parameters:[{position:1,carrier:'integer',text:key}]});
   if((await lock(first)).status!=='ok')throw Error('First private probe lock failed');
   if(++arrived===2)releaseBarrier();await barrier;
   return lock(second);
 });
 const deadlock=await Promise.all([lockPair('1890033411','1890033412'),lockPair('1890033412','1890033411')]);
 if(deadlock.filter(r=>r.status==='error'&&r.error.code==='retry'&&r.error.sqlState==='40P01'&&r.error.retryScope==='whole_transaction').length!==1||
    deadlock.filter(r=>r.status==='ok'&&r.value.durability==='committed').length!==1)throw Error('Native deadlock settlement correspondence');
 const commitRejection=await executor.withTransaction({isolation:'read_committed',accessMode:'read_write'},async tx=>{
   await run(tx,'CREATE TEMP TABLE truss_pg_deferred_parent(id integer PRIMARY KEY)');
   await run(tx,'CREATE TEMP TABLE truss_pg_deferred_child(id integer REFERENCES truss_pg_deferred_parent(id) DEFERRABLE INITIALLY DEFERRED)');
   await run(tx,'INSERT INTO truss_pg_deferred_child VALUES(1)');return 'pending-only';
 });
 if(commitRejection.status!=='error'||commitRejection.error.sqlState!=='23503'||commitRejection.error.retryScope!=='none'||host.quarantinedCount()!==0)throw Error('Commit rejection not settled');
 const rejectionRollback=await executor.withTransaction({isolation:'read_committed',accessMode:'read_only'},async tx=>run(tx,"SELECT to_regclass('pg_temp.truss_pg_deferred_parent')::text AS parent,to_regclass('pg_temp.truss_pg_deferred_child')::text AS child"));
 if(rejectionRollback.status!=='ok'||rejectionRollback.value.value.rows[0].some(c=>c.state!=='null'))throw Error('Rejected commit effects survived');
 await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/pg-executor.json',import.meta.url),JSON.stringify({driver:'pg/8.16.3',loader:'bun/'+Bun.version,result,writes,rollback,deadlock,commitRejection,rejectionRollback,
 qualification:'Actual engine executor + direct pg driver on existing local PostgreSQL 17.9. Exact native numeric text cells, duplicate/empty column descriptions, savepoints, confirmed read-only/write commit, exact parameterized write, uniqueness-error savepoint containment preserving prior work and independently observed callback rollback and one actual advisory-lock deadlock with whole-transaction retry outcome; actual deferred-FK commit rejection with confirmed rollback and independent absent-table observation. No caller adoption/cancellation, lost-commit native containment, pooler/Node or full Truss bootstrap qualification.'},null,2)+'\n');
 console.log('Native pg executor exact transport/columns/savepoints/commit passed.');
}finally{await host.close();}
