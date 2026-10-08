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
 const barrier=await Bun.file('packages/postgresql/native/operation-commit-barrier.sql').text();await sql.unsafe(barrier);
 const admit="SELECT * FROM truss.runtime_admit_operation('mutation',decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'))";
 await sql.unsafe('BEGIN');await sql.unsafe(admit);
 let commitCode='';try{await sql.unsafe('COMMIT')}catch(e){commitCode=(e as any).errno??(e as any).code}
 assert(commitCode==='55000','unfinalized operation cannot commit');
 const rejected=await sql.unsafe('SELECT count(*)::text AS n FROM truss.row_home_operation');assert(rejected[0].n==='0','failed commit removes custody');
 await sql.unsafe('CREATE TEMP TABLE caller_sentinel (value text)');await sql.unsafe('BEGIN');
 await sql.unsafe("INSERT INTO caller_sentinel VALUES ('earlier caller work')");await sql.unsafe('SAVEPOINT operation');await sql.unsafe(admit);await sql.unsafe('ROLLBACK TO SAVEPOINT operation');await sql.unsafe('COMMIT');
 const sentinel=await sql.unsafe('SELECT value FROM caller_sentinel');assert(sentinel.length===1&&sentinel[0].value==='earlier caller work','rolled back operation preserves earlier caller work');
 await sql.unsafe('BEGIN');await sql.unsafe(admit);
 await sql.unsafe("UPDATE truss.row_home_operation SET phase='application_finalized',readiness_generation=0,sealed_generation=0,application_generation=0,application_result_bytes=decode('01','hex')");
 let forgedCode='';try{await sql.unsafe('COMMIT')}catch(e){forgedCode=(e as any).errno??(e as any).code}
 assert(forgedCode==='55000','phase flags cannot bypass unavailable complete finalizer');
 const catalogStage=await Bun.file('packages/postgresql/native/catalog-document-stage.sql').text();await sql.unsafe(catalogStage);
 const beforeHead=await sql.unsafe('SELECT rev::text AS rev FROM truss.schema_head');const beforeRevisions=await sql.unsafe('SELECT count(*)::text AS n FROM truss.schema_rev');
 await sql.unsafe('BEGIN');
 await sql.unsafe(admit.replace("'mutation'","'catalog-acceptance'"));
 const originalDocument='{"umf":"0.7.0","opaque":"雪\\u0000"}';
 const staged=await sql.unsafe("SELECT * FROM truss.runtime_stage_catalog_document('original-document','r1','0.7.0',$1::text,'{}'::jsonb,'{}'::jsonb)",[originalDocument]);
 assert(staged.length===1&&staged[0].provisional_revision==='1','native provisional catalog revision allocated');
 const typeStage=await Bun.file('packages/postgresql/native/catalog-type-stage.sql').text();await sql.unsafe(typeStage);
 const candidates=[{documentId:'original-document',moduleId:'m',elementId:'z',lineageProfile:'test-original-bytes',lineageHex:'00ff'},{documentId:'original-document',moduleId:'m',elementId:'a',lineageProfile:'test-original-bytes',lineageHex:'01'}];
 const allocated=await sql.unsafe('SELECT * FROM truss.runtime_stage_new_types($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify(candidates)]);
 assert(allocated.length===2&&allocated[0].element_id==='a'&&allocated[0].type_id==='1'&&allocated[1].type_id==='2','native IDs follow original qualified byte order');
 await sql.unsafe('SAVEPOINT existing_type');let existingCode='';try{await sql.unsafe('SELECT * FROM truss.runtime_stage_new_types($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify(candidates)])}catch(e){existingCode=(e as any).errno??(e as any).code}assert(existingCode==='55000','existing identities refuse new allocation');await sql.unsafe('ROLLBACK TO SAVEPOINT existing_type');
 await sql.unsafe('UPDATE truss.type_def SET retired_rev=since_rev');
 const next=await sql.unsafe('SELECT * FROM truss.runtime_stage_new_types($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify([{...candidates[0],elementId:'b'}])]);assert(next[0].type_id==='3','retired retained IDs remain high-water contributors');
 const originalLineage=await sql.unsafe("SELECT encode(lineage_bytes,'hex') AS bytes FROM truss.type_def WHERE element='z'");assert(originalLineage[0].bytes==='00ff','original lineage bytes retained');
 const retained=await sql.unsafe('SELECT document FROM truss.schema_doc');assert(retained[0].document===originalDocument,'verbatim original source retained');
 const head=await sql.unsafe('SELECT rev::text AS rev FROM truss.schema_head');assert(JSON.stringify(head)===JSON.stringify(beforeHead),'document stage cannot publish catalog head');
 await sql.unsafe('ROLLBACK');
 const remaining=await sql.unsafe('SELECT count(*)::text AS n FROM truss.schema_rev');assert(remaining[0].n===beforeRevisions[0].n,'rollback removes staged revision and source');
 const receipt={component:'native operation admission',engine:'PostgreSQL17.9',checks,bodySha256:new Bun.CryptoHasher('sha256').update(body).digest('hex'),observerSha256:new Bun.CryptoHasher('sha256').update(observer).digest('hex'),barrierSha256:new Bun.CryptoHasher('sha256').update(barrier).digest('hex'),catalogStageSha256:new Bun.CryptoHasher('sha256').update(catalogStage).digest('hex'),typeStageSha256:new Bun.CryptoHasher('sha256').update(typeStage).digest('hex'),qualification:'Actual xid/context/artifact bounds/single unfinished/rollback/private invocation component only. Protected issuer registration, canonical observers, finalization, deferred complete-cohort checks, installer security and public runtime remain unfinished.'};
 await Bun.write('docs/helix/04-build/evidence/runtime-operation-admission.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({checks:checks.length}));
}finally{await sql.close()}
