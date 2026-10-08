/** Isolated native internal component; no normal installation marker or public writer. */
import {SQL} from 'bun';
const url=process.env.TRUSS_OPERATION_TEST_URL;
if(!url||!url.startsWith('postgres://postgres@127.0.0.1:15434/'))throw Error('Dedicated local test endpoint required');
const sql=new SQL(url,{max:1});
const layout=await Bun.file('docs/helix/04-build/evidence/weft-integration-layout-0.13.owner-export.sql').text();
const body=await Bun.file('packages/postgresql/native/operation-admission.sql').text();
const checks:string[]=[];
const assert=(v:boolean,label:string)=>{if(!v)throw Error(label);checks.push(label)};
try{
 const version=await sql.unsafe('SHOW server_version');assert(version[0].server_version.startsWith('17.9'),'exact PostgreSQL17.9');
 await sql.unsafe(layout);await sql.unsafe(body);
 const observer=await Bun.file('packages/postgresql/native/operation-generation-observer.sql').text();await sql.unsafe(observer);
 const triggers=await sql.unsafe("SELECT count(*)::text AS n FROM pg_trigger WHERE tgname IN ('runtime_state_generation','runtime_node_generation','runtime_scalar_generation') AND tgenabled='A' AND NOT tgisinternal");assert(triggers[0].n==='3','three ALWAYS generation observers installed');
 await sql.unsafe('BEGIN');
 const xid=await sql.unsafe('SELECT pg_catalog.pg_current_xact_id()::text AS xid');
 const rows=await sql.unsafe("SELECT * FROM truss.runtime_admit_operation('mutation',decode('00ff','hex'),decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'))");
 assert(rows.length===1&&rows[0].writer_xid===xid[0].xid&&rows[0].ordinal==='0','actual native xid and ordinal');
 const context=JSON.parse(Buffer.from(rows[0].context_hex,'hex').toString('utf8'));
 assert(context.xid===xid[0].xid&&context.sessionUser==='postgres'&&context.actingUser==='postgres','original actor and native context captured');
 await sql.unsafe('SAVEPOINT duplicate');
 let code='';try{await sql.unsafe("SELECT * FROM truss.runtime_admit_operation('mutation',decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'))")}catch(e){code=(e as any).errno??(e as any).code}
 assert(code==='55000','second unfinished operation refused');await sql.unsafe('ROLLBACK TO SAVEPOINT duplicate');
 const stored=await sql.unsafe("SELECT encode(original_definition_bytes,'hex') AS bytes FROM truss.row_home_operation");
 assert(stored.length===1&&stored[0].bytes==='00ff','original binary artifact retained');
 await sql.unsafe('ROLLBACK');
 const after=await sql.unsafe('SELECT count(*)::text AS n FROM truss.row_home_operation');assert(after[0].n==='0','rollback removes operation custody');
 const grants=await sql.unsafe("SELECT count(*)::text AS n FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE n.nspname='truss' AND p.proname='runtime_admit_operation' AND a.grantee=0 AND a.privilege_type='EXECUTE'");assert(grants[0].n==='0','no public execute');
 const receipt={component:'native operation admission',engine:'PostgreSQL17.9',checks,bodySha256:new Bun.CryptoHasher('sha256').update(body).digest('hex'),observerSha256:new Bun.CryptoHasher('sha256').update(observer).digest('hex'),qualification:'Actual xid/context/artifact bounds/single unfinished/rollback/private invocation component only. Protected issuer registration, canonical observers, finalization, deferred complete-cohort checks, installer security and public runtime remain unfinished.'};
 await Bun.write('docs/helix/04-build/evidence/runtime-operation-admission.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({checks:checks.length}));
}finally{await sql.close()}
