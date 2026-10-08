/** Private existing-sandbox driver qualification; credentials remain memory-only. */
import {SQL} from 'bun';
import {writeFile} from 'node:fs/promises';
const inspected=Bun.spawnSync(['/usr/local/bin/docker','inspect','ashlar-e2e-truss-pg17']);
if(inspected.exitCode!==0)throw Error('Existing development sandbox unavailable');
const container=JSON.parse(new TextDecoder().decode(inspected.stdout))[0];
if(container.Config.Labels['ashlar.purpose']!=='end-to-end-development')throw Error('Wrong sandbox');
const password=container.Config.Env.find((s:string)=>s.startsWith('POSTGRES_PASSWORD=')).slice('POSTGRES_PASSWORD='.length);
const sql=new SQL({adapter:'postgres',hostname:'127.0.0.1',port:15432,username:'postgres',password,database:'truss_e2e',max:1,prepare:false,connectionTimeout:5});
const evidence:{[key:string]:unknown}={driver:'bun/'+Bun.version,profile:'private-direct-postgresql-probe/0.1',prepare:false};
try{
  const exactJson='{"large":9007199254740993123456789,"unknown":{"present":null}}';
  const committed=await sql.begin('isolation level serializable read only',async tx=>{
    await tx.unsafe("SET LOCAL statement_timeout='5s'");
    await tx.unsafe("SET LOCAL lock_timeout='1s'");
    const rows=await tx.unsafe(`SELECT current_setting('server_version')::text,current_setting('transaction_isolation')::text,current_setting('transaction_read_only')::text,
      9007199254740993123::bigint::text,12345678901234567890.123456789::numeric::text,
      TIMESTAMP '2026-10-08 12:34:56.123456'::text,NULL::text,$1::text,pg_backend_pid()::text`,[exactJson]).values();
    if(rows.length!==1||rows[0].some((v:unknown)=>v!==null&&typeof v!=='string'))throw Error('Non-text raw cell');
    if(rows[0][3]!=='9007199254740993123'||rows[0][4]!=='12345678901234567890.123456789'||rows[0][6]!==null||rows[0][7]!==exactJson)throw Error('Exact carrier mismatch');
    if(rows[0][1]!=='serializable'||rows[0][2]!=='on')throw Error('Native transaction option mismatch');
    const again=await tx.unsafe('SELECT pg_backend_pid()::text').values();
    if(again[0][0]!==rows[0][8])throw Error('Connection affinity mismatch');
    return rows[0];
  });
  evidence.committedTextResult=committed;
  const sentinel=new Error('controlled callback failure');
  try{
    await sql.begin(async tx=>{
      await tx.unsafe("SET LOCAL statement_timeout='5s'");
      await tx.unsafe('CREATE TEMP TABLE truss_bun_rollback_probe(id integer)');
      await tx.unsafe('INSERT INTO truss_bun_rollback_probe VALUES(1)');
      throw sentinel;
    });
    throw Error('Callback failure unexpectedly committed');
  }catch(error){if(error!==sentinel)throw Error('Original callback exception not preserved');}
  const after=await sql.unsafe("SELECT to_regclass('pg_temp.truss_bun_rollback_probe')::text").values();
  if(after[0][0]!==null)throw Error('Rollback not independently observed');
  evidence.callbackRollbackConfirmed=true;
  const savepoint=await sql.begin(async tx=>{
    await tx.unsafe("SET LOCAL statement_timeout='5s'");
    await tx.unsafe('CREATE TEMP TABLE truss_bun_savepoint_probe(id integer)');
    await tx.unsafe('INSERT INTO truss_bun_savepoint_probe VALUES(1)');
    await tx.unsafe('SAVEPOINT truss_probe');
    await tx.unsafe('INSERT INTO truss_bun_savepoint_probe VALUES(2)');
    await tx.unsafe('ROLLBACK TO SAVEPOINT truss_probe');
    await tx.unsafe('RELEASE SAVEPOINT truss_probe');
    const rows=await tx.unsafe('SELECT id::text FROM truss_bun_savepoint_probe ORDER BY id').values();
    await tx.unsafe('DROP TABLE truss_bun_savepoint_probe');
    return rows;
  });
  if(JSON.stringify(savepoint)!==JSON.stringify([['1']]))throw Error('Savepoint correspondence mismatch');
  evidence.savepointRollbackPreservesPriorWork=true;
  evidence.qualification='Existing local PostgreSQL 17.9, Bun 1.4.2 direct single-connection unprepared subset. Exact explicit text casts, native transaction modes/affinity, controlled callback rollback and savepoint rollback. No Truss installation, caller adoption, cancellation, lost COMMIT, quarantine, prepared/pooler/Node support or complete adapter conformance.';
  await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/bun-execution.json',import.meta.url),JSON.stringify(evidence,null,2)+'\n');
  console.log('Native Bun transaction/text/savepoint probe passed; no persistent tables.');
}catch{throw Error('Native Bun execution qualification failed; no support claim.');}
finally{await sql.close();}
