import {decodeCapturedOriginContext} from '../packages/postgresql/src/captured-origin-context';
/** Rollback-contained context0.3 byte custody, not full installed admission. */
import {SQL} from 'bun';
const url=process.env.TRUSS_OPERATION_TEST_URL;if(!url?.startsWith('postgres://postgres@127.0.0.1:15434/'))throw Error('Owned fixture URL required');
const sql=new SQL(url,{max:1});const checks:string[]=[];
try{
 await sql.begin(async tx=>{
  await tx.unsafe(await Bun.file('docs/helix/04-build/evidence/source-epoch-storage.owner-export.sql').text());
  for(const component of ['source-epoch-immutability','source-epoch-lock','source-epoch-issue','operation-epoch-context-admission'])await tx.unsafe(await Bun.file('packages/postgresql/native/'+component+'.sql').text());
  await tx`INSERT INTO truss.installation_marker VALUES (1,'truss-bootstrap-marker/0.1.0','component-installation','component-only',decode(repeat('00',32),'hex'),'component',decode(repeat('00',32),'hex'),'owned-fixture','truss',now(),'component-clock-unqualified')`;
  const issued=await tx`SELECT truss.runtime_issue_source_epoch('component-installation',NULL,'component-incarnation',decode('0102','hex'),decode('0304','hex')) AS epoch`;
  const epoch=issued[0].epoch;
  const origin=new TextEncoder().encode(' {"actor":"asserted", "note":"\\u0000", "decimal":"123.000"}\n');
  const hex=Array.from(origin,b=>b.toString(16).padStart(2,'0')).join('');
  const invoke=(sourceHex:string,profileHex:string)=>tx.unsafe("SELECT * FROM truss.runtime_admit_operation_with_epoch_context('catalog-acceptance',decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode($1,'hex'),decode($2,'hex'),'component-installation',$3,'component-incarnation')",[sourceHex,profileHex,epoch]);
  const refuse=async(label:string,code:string,fn:()=>Promise<unknown>)=>{let actual='';try{await tx.savepoint(async()=>{await fn()})}catch(e){actual=(e as any).errno??(e as any).code}if(actual!==code)throw Error(label+': '+actual);checks.push(label)};
  await refuse('Empty asserted bytes refuse before operation insertion','22023',()=>invoke('','01'));
  await refuse('Empty capture profile refuses before operation insertion','22023',()=>invoke(hex,''));
  await refuse('Asserted source bound refuses before insertion','22023',()=>invoke('20'.repeat(131073),'01'));
  const rows=await invoke(hex,'010203');const context=JSON.parse(Buffer.from(rows[0].context_hex,'hex').toString('utf8'));
  if(Object.keys(context).length!==16||context.interfaceVersion!=='truss-native-operation-context/0.4'||context.assertedOriginUtf8Hex!==hex||context.assertedOriginCaptureProfileHex!=='010203')throw Error('Original context byte correspondence');
  const actual=await tx`SELECT current_user::text AS actor,session_user::text AS login`;
  if(context.actingUser!==actual[0].actor||context.sessionUser!==actual[0].login)throw Error('Native actor substitution');
  checks.push('One original context0.4 artifact retains exact asserted whitespace/escapes and separate native actors/profile');
  if(context.installationId!=='component-installation'||context.sourceEpoch!==epoch||context.targetIncarnation!=='component-incarnation'||context.sourceEpochProfileHex!=='0102'||context.sourceEpochEvidenceHex!=='0304')throw Error('Same-operation native epoch correspondence');
  checks.push('One immutable original context binds actual native-issued epoch and registry profile/evidence bytes');
  const decoded=decodeCapturedOriginContext(new Uint8Array(Buffer.from(rows[0].context_hex,'hex')),'0.4');
  if(!decoded.epoch||decoded.epoch.sourceEpoch!==epoch||decoded.epoch.profileHex!=='0102'||decoded.epoch.evidenceHex!=='0304'||decoded.origin.databaseRole!==actual[0].actor||decoded.assertedUtf8Hex!==hex)throw Error('Original context4 host decode mismatch');
  checks.push('Strict host decoder preserves original epoch evidence and asserted/native actor correspondence');
  for(const invalid of [{...context,sourceEpoch:''},{...context,sourceEpochEvidenceHex:'zz'},{...context,extra:'unknown'}]){let rejected=false;try{decodeCapturedOriginContext(new TextEncoder().encode(JSON.stringify(invalid)),'0.4')}catch{rejected=true}if(!rejected)throw Error('Invalid context4 decoded');}
  let legacy=false;try{decodeCapturedOriginContext(new Uint8Array(Buffer.from(rows[0].context_hex,'hex')))}catch{legacy=true}if(!legacy)throw Error('Context3 decoder accepted epoch-context upgrade');
  checks.push('Invalid epoch identity/evidence/extra fields and implicit context3 upgrade refuse');

  await refuse('Epoch issuer refuses transition behind captured original writer','55000',()=>tx`SELECT truss.runtime_issue_source_epoch('component-installation',${epoch},'component-incarnation',decode('01','hex'),decode('02','hex'))`);
  await refuse('Context original bytes cannot be replaced','55000',()=>tx`UPDATE truss.row_home_operation SET original_context_bytes=decode('01','hex') WHERE original_writer_xid=pg_current_xact_id_if_assigned()`);
  await refuse('Original operation cannot be deleted','55000',()=>tx`DELETE FROM truss.row_home_operation WHERE original_writer_xid=pg_current_xact_id_if_assigned()`);
  const retained=await tx`SELECT encode(original_context_bytes,'hex') AS bytes FROM truss.row_home_operation WHERE original_writer_xid=pg_current_xact_id_if_assigned()`;
  if(retained.length!==1||retained[0].bytes!==rows[0].context_hex)throw Error('Original capture changed');
  checks.push('Failed substitutions preserve complete original context');
  throw Error('ROLLBACK_ASSERTED_CAPTURE');
 }).catch(e=>{if(e.message!=='ROLLBACK_ASSERTED_CAPTURE')throw e});
 const after=await sql`SELECT count(*)::text AS n FROM truss.row_home_operation`;if(after[0].n!=='0')throw Error('Rollback leaked capture');checks.push('Outer rollback removes captured operation');
 const sources:Record<string,string>={};for(const path of ['scripts/check-asserted-origin-admission.ts','packages/postgresql/native/operation-epoch-context-admission.sql','packages/postgresql/native/operation-admission.sql','docs/helix/04-build/evidence/source-epoch-storage.owner-export.sql','packages/postgresql/native/source-epoch-immutability.sql','packages/postgresql/native/source-epoch-lock.sql','packages/postgresql/native/source-epoch-issue.sql','packages/postgresql/src/captured-origin-context.ts','packages/postgresql/src/asserted-origin-map.ts','packages/postgresql/native/catalog-input-custody.sql'])sources[path]=new Bun.CryptoHasher('sha256').update(await Bun.file(path).arrayBuffer()).digest('hex');
 await Bun.write('docs/helix/04-build/evidence/design-audit/epoch-context-admission.json',JSON.stringify({sources,checks,scope:'Actual context0.4 same-operation native epoch/actor/asserted byte capture and immutable custody on PostgreSQL17.9; profile bytes are explicit component inputs, not installed authority or complete asserted-origin semantic admission'},null,2)+'\n');console.log(JSON.stringify({checks:checks.length}));
}finally{await sql.close();}
