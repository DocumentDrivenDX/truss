/** Owned fixture only; storage constraints do not qualify epoch issuance. */
import {SQL} from 'bun';
const url=process.env.TRUSS_OPERATION_TEST_URL;
if(!url?.startsWith('postgres://postgres@127.0.0.1:15434/'))throw Error('Owned fixture URL required');
const sql=new SQL(url,{max:1});const checks:string[]=[];
try {
 await sql.begin(async tx=>{
  const count=await tx`SELECT count(*)::text AS n FROM truss.installation_marker`;
  if(count[0].n!=='0')throw Error('Marker fixture must be empty');
  await tx.unsafe(await Bun.file('docs/helix/04-build/evidence/source-epoch-storage.owner-export.sql').text());
  await tx`INSERT INTO truss.installation_marker VALUES (1,'truss-bootstrap-marker/0.1.0','component-test-installation','component-only',decode(repeat('00',32),'hex'),'component',decode(repeat('00',32),'hex'),'owned-fixture','truss',now(),'component-clock-unqualified')`;
  await tx.unsafe(await Bun.file('packages/postgresql/native/source-epoch-issue.sql').text());
  try {await tx.savepoint(async sp=>{
   const initial=await sp`SELECT truss.runtime_issue_source_epoch('component-test-installation',NULL,'component-test-incarnation',decode('01','hex'),decode('02','hex')) AS epoch`;
   const first=initial[0].epoch;
   if(!/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(first))throw Error('Native issuer token grammar');
   const successor=await sp`SELECT truss.runtime_issue_source_epoch('component-test-installation',${first},'component-restored-incarnation',decode('01','hex'),decode('03','hex')) AS epoch`;
   if(successor[0].epoch===first)throw Error('Issuer reused epoch');
   const issued=await sp`SELECT source_epoch,predecessor_epoch FROM truss.source_epoch_registry ORDER BY transition_reason`;
   if(issued.length!==2||issued[0].source_epoch!==first||issued[1].predecessor_epoch!==first)throw Error('Issuer lineage mismatch');
   checks.push('Native issuance generates UUID4 initial and distinct successor with original predecessor');
   throw Error('ROLLBACK_ISSUER_COMPONENT');
  });}catch(e){if((e as Error).message!=='ROLLBACK_ISSUER_COMPONENT')throw e;}
  const issuedAfter=await tx`SELECT count(*)::text AS n FROM truss.source_epoch_registry`;
  if(issuedAfter[0].n!=='0')throw Error('Issuer rollback leaked');
  checks.push('Issuer savepoint rollback removes initial and successor registry/pointer');
  const insert=(epoch:string,prior:string|null,reason:string)=>tx`INSERT INTO truss.source_epoch_registry (installation_id,source_epoch,target_incarnation,predecessor_epoch,transition_reason,profile_bytes,evidence_bytes) VALUES ('component-test-installation',${epoch},'component-test-incarnation',${prior},${reason},decode('01','hex'),decode('0203','hex'))`;
  const refuse=async(label:string,code:string,fn:()=>Promise<unknown>)=>{
   let observed='';try{await tx.savepoint(async()=>{await fn();});}catch(e){observed=(e as any).errno??(e as any).code;}
   if(observed!==code)throw Error(`${label}: expected ${code}, got ${observed}`);checks.push(label);
  };
  await insert('component-initial',null,'initial');
  await tx`INSERT INTO truss.source_epoch_current VALUES (1,'component-test-installation','component-initial')`;
  checks.push('Initial registry/pointer component insertion');
  await refuse('Missing predecessor refuses','23503',()=>insert('component-next','absent','restore'));
  await refuse('Self predecessor refuses','23514',()=>insert('component-self','component-self','restore'));
  await refuse('Initial with predecessor refuses','23514',()=>insert('component-wrong','component-initial','initial'));
  await refuse('Duplicate epoch refuses','23505',()=>insert('component-initial',null,'initial'));
  await refuse('Missing current registry refuses','23503',()=>tx`UPDATE truss.source_epoch_current SET source_epoch='absent'`);
  await insert('component-successor','component-initial','restore');
  await tx`UPDATE truss.source_epoch_current SET source_epoch='component-successor'`;
  const rows=await tx`SELECT source_epoch,encode(evidence_sha256,'hex') AS digest FROM truss.source_epoch_registry ORDER BY source_epoch`;
  const digest=new Bun.CryptoHasher('sha256').update(new Uint8Array([2,3])).digest('hex');
  if(rows.length!==2||rows.some((r:{digest:string})=>r.digest!==digest))throw Error('History/digest mismatch');
  checks.push('Successor preserves original registry and exact artifact digest');
  await tx.unsafe(await Bun.file('packages/postgresql/native/source-epoch-immutability.sql').text());
  for(const mode of ['origin','replica']) {
   await tx.unsafe(`SET LOCAL session_replication_role=${mode}`);
   await refuse(`${mode}: registry UPDATE blocked`,'55000',()=>tx`UPDATE truss.source_epoch_registry SET evidence_bytes=decode('04','hex')`);
   await refuse(`${mode}: registry DELETE blocked`,'55000',()=>tx`DELETE FROM truss.source_epoch_registry`);
   await refuse(`${mode}: registry TRUNCATE blocked`,'55000',()=>tx`TRUNCATE truss.source_epoch_registry CASCADE`);
  }
  await tx`SET LOCAL session_replication_role=origin`;
  const guards=await tx`SELECT tgenabled::text AS enabled FROM pg_catalog.pg_trigger WHERE tgrelid='truss.source_epoch_registry'::regclass AND tgname IN ('runtime_source_epoch_immutable','runtime_source_epoch_no_truncate')`;
  if(guards.length!==2||guards.some((r:{enabled:string})=>r.enabled!=='A'))throw Error('Epoch guards not ALWAYS');
  const retained=await tx`SELECT source_epoch,encode(evidence_sha256,'hex') AS digest FROM truss.source_epoch_registry ORDER BY source_epoch`;
  if(JSON.stringify(retained)!==JSON.stringify(rows))throw Error('Guard changed original registry');
  checks.push('Both guards ALWAYS and original epoch evidence unchanged');
  await tx.unsafe(await Bun.file('packages/postgresql/native/source-epoch-lock.sql').text());
  const locked=await tx`SELECT * FROM truss.runtime_lock_source_epoch('component-test-installation','component-successor','component-test-incarnation')`;
  if(locked.length!==1||locked[0].source_epoch!=='component-successor'||locked[0].profile_hex!=='01'||locked[0].evidence_hex!=='0203'||locked[0].evidence_sha256!==digest)throw Error('Epoch readback mismatch');
  checks.push('Current pointer lock returns exact original registry bytes');
  await refuse('Stale epoch comparison refuses','55000',()=>tx`SELECT * FROM truss.runtime_lock_source_epoch('component-test-installation','component-initial','component-test-incarnation')`);
  await refuse('Wrong incarnation comparison refuses','55000',()=>tx`SELECT * FROM truss.runtime_lock_source_epoch('component-test-installation','component-successor','different')`);
  await refuse('Missing expected identity refuses','55000',()=>tx`SELECT * FROM truss.runtime_lock_source_epoch(NULL,'component-successor','component-test-incarnation')`);
  await refuse('Issuer stale predecessor refuses','55000',()=>tx`SELECT truss.runtime_issue_source_epoch('component-test-installation','component-initial','component-test-incarnation',decode('01','hex'),decode('02','hex'))`);
  await refuse('Issuer null profile refuses','55000',()=>tx`SELECT truss.runtime_issue_source_epoch('component-test-installation','component-successor','component-test-incarnation',NULL,decode('02','hex'))`);
  try {await tx.savepoint(async sp=>{
   await sp`SELECT * FROM truss.runtime_admit_operation('mutation',decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'))`;
   await refuse('Actual native admitted writer fences epoch issuance','55000',()=>tx`SELECT truss.runtime_issue_source_epoch('component-test-installation','component-successor','component-test-incarnation',decode('01','hex'),decode('02','hex'))`);
   await refuse('Actual original operation cannot be deleted to evade epoch fence','55000',()=>tx`DELETE FROM truss.row_home_operation WHERE original_writer_xid=pg_current_xact_id_if_assigned()`);
   const retainedWriter=await sp`SELECT count(*)::text AS n FROM truss.row_home_operation WHERE original_writer_xid=pg_current_xact_id_if_assigned()`;
   if(retainedWriter[0].n!=='1')throw Error('Original writer custody lost');
   checks.push('Actual admitted operation survives attempted epoch transition and removal');
   throw Error('ROLLBACK_ORIGINAL_WRITER_TEST');
  });}catch(e){if((e as Error).message!=='ROLLBACK_ORIGINAL_WRITER_TEST')throw e;}
  const rolledWriter=await tx`SELECT count(*)::text AS n FROM truss.row_home_operation WHERE original_writer_xid=pg_current_xact_id_if_assigned()`;
  if(rolledWriter[0].n!=='0')throw Error('Original operation rollback failed');
  checks.push('Original operation savepoint rollback restores no-writer state');
  await tx`SET LOCAL ROLE pg_read_all_data`;
  await refuse('Ordinary role issuer execution denied','42501',()=>tx`SELECT truss.runtime_issue_source_epoch('component-test-installation','component-successor','component-test-incarnation',decode('01','hex'),decode('02','hex'))`);
  await refuse('Ordinary role epoch primitive execution denied','42501',()=>tx`SELECT * FROM truss.runtime_lock_source_epoch('component-test-installation','component-successor','component-test-incarnation')`);
  await refuse('Ordinary role registry insert denied','42501',()=>insert('component-forged',null,'initial'));
  await refuse('Ordinary role pointer update denied','42501',()=>tx`UPDATE truss.source_epoch_current SET source_epoch='component-initial'`);
  await tx`RESET ROLE`;
  throw new Error('ROLLBACK_COMPONENT_TEST');
 }).catch(e=>{if(e.message!=='ROLLBACK_COMPONENT_TEST')throw e;});
 const after=await sql`SELECT to_regclass('truss.source_epoch_registry')::text AS registry,(SELECT count(*)::text FROM truss.installation_marker) AS markers,version() AS version`;
 if(after[0].registry!==null||after[0].markers!=='0')throw Error('Rollback leaked component state');
 checks.push('Outer rollback removes registry/pointer and marker');
 const sources:Record<string,string>={};
 for(const path of ['scripts/check-source-epoch-storage.ts','packages/postgresql/native/source-epoch-immutability.sql','packages/postgresql/native/source-epoch-lock.sql','packages/postgresql/native/source-epoch-issue.sql','packages/postgresql/native/operation-admission.sql','docs/helix/04-build/evidence/source-epoch-storage.owner-export.sql'])sources[path]=new Bun.CryptoHasher('sha256').update(await Bun.file(path).arrayBuffer()).digest('hex');
 await Bun.write('docs/helix/04-build/evidence/design-audit/source-epoch-storage-native.json',JSON.stringify({database:after[0].version,sources,checks,scope:'Rollback-contained storage candidate constraints and ordinary-role DML denial only; synthetic component tokens are not issued epochs, installed admission or lifecycle qualification',qualified:false},null,2)+'\n');console.log(JSON.stringify({checks:checks.length,qualified:false}));
}finally{await sql.close();}
