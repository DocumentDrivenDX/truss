import {createPgConnectionSource} from '../packages/pg-runtime/src/index';
import {createEngineExecutor} from '../packages/postgresql/src/index';
import {writeFile} from 'node:fs/promises';
const probe=Bun.spawnSync(['/usr/local/bin/docker','inspect','ashlar-e2e-truss-pg17']);
if(probe.exitCode)throw Error('Existing sandbox unavailable');
const container=JSON.parse(new TextDecoder().decode(probe.stdout))[0];
if(container.Config.Labels['ashlar.purpose']!=='end-to-end-development')throw Error('Wrong sandbox');
const password=container.Config.Env.find((s:string)=>s.startsWith('POSTGRES_PASSWORD=')).slice(18);
const host=createPgConnectionSource({host:'127.0.0.1',port:15432,user:'postgres',password,database:'truss_e2e',max:1,
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
 await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/pg-executor.json',import.meta.url),JSON.stringify({driver:'pg/8.16.3',loader:'bun/'+Bun.version,result,
 qualification:'Actual engine executor + direct pg driver on existing local PostgreSQL 17.9. Exact native numeric text cells, duplicate/empty column descriptions, savepoints and confirmed read-only commit. No caller adoption/cancellation, lost-commit native containment, pooler/Node or full Truss bootstrap qualification.'},null,2)+'\n');
 console.log('Native pg executor exact transport/columns/savepoints/commit passed.');
}finally{await host.close();}
