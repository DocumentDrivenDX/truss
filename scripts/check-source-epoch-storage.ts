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
  if(rows.length!==2||rows.some(r=>r.digest!==digest))throw Error('History/digest mismatch');
  checks.push('Successor preserves original registry and exact artifact digest');
  await tx`SET LOCAL ROLE pg_read_all_data`;
  await refuse('Ordinary role registry insert denied','42501',()=>insert('component-forged',null,'initial'));
  await refuse('Ordinary role pointer update denied','42501',()=>tx`UPDATE truss.source_epoch_current SET source_epoch='component-initial'`);
  await tx`RESET ROLE`;
  throw new Error('ROLLBACK_COMPONENT_TEST');
 }).catch(e=>{if(e.message!=='ROLLBACK_COMPONENT_TEST')throw e;});
 const after=await sql`SELECT to_regclass('truss.source_epoch_registry')::text AS registry,(SELECT count(*)::text FROM truss.installation_marker) AS markers,version() AS version`;
 if(after[0].registry!==null||after[0].markers!=='0')throw Error('Rollback leaked component state');
 checks.push('Outer rollback removes registry/pointer and marker');
 await Bun.write('docs/helix/04-build/evidence/design-audit/source-epoch-storage-native.json',JSON.stringify({database:after[0].version,checks,scope:'Rollback-contained storage candidate constraints and ordinary-role DML denial only; synthetic component tokens are not issued epochs, installed admission or lifecycle qualification',qualified:false},null,2)+'\n');console.log(JSON.stringify({checks:checks.length,qualified:false}));
}finally{await sql.close();}
