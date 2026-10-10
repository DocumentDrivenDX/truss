import {decodeCapturedOriginContext} from '../packages/postgresql/src/captured-origin-context';
/** Rollback-contained context0.3 byte custody, not full installed admission. */
import {SQL} from 'bun';
const url=process.env.TRUSS_OPERATION_TEST_URL;if(!url?.startsWith('postgres://postgres@127.0.0.1:15434/'))throw Error('Owned fixture URL required');
const sql=new SQL(url,{max:1});const checks:string[]=[];
try{
 await sql.begin(async tx=>{
  await tx.unsafe(await Bun.file('packages/postgresql/native/operation-asserted-origin-admission.sql').text().then(text=>text.replace('CREATE FUNCTION','CREATE OR REPLACE FUNCTION')));
  await tx.unsafe(await Bun.file('packages/postgresql/native/catalog-captured-context.sql').text().then(text=>text.replace('CREATE FUNCTION','CREATE OR REPLACE FUNCTION')));
  const origin=new TextEncoder().encode(' {"actor":"asserted", "note":"\\u0000", "decimal":"123.000"}\n');
  const hex=Array.from(origin,b=>b.toString(16).padStart(2,'0')).join('');
  const invoke=(sourceHex:string,profileHex:string)=>tx.unsafe("SELECT * FROM truss.runtime_admit_operation_with_asserted_origin('catalog-acceptance',decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode($1,'hex'),decode($2,'hex'))",[sourceHex,profileHex]);
  const refuse=async(label:string,code:string,fn:()=>Promise<unknown>)=>{let actual='';try{await tx.savepoint(async()=>{await fn()})}catch(e){actual=(e as any).errno??(e as any).code}if(actual!==code)throw Error(label+': '+actual);checks.push(label)};
  await refuse('Empty asserted bytes refuse before operation insertion','22023',()=>invoke('','01'));
  await refuse('Empty capture profile refuses before operation insertion','22023',()=>invoke(hex,''));
  await refuse('Asserted source bound refuses before insertion','22023',()=>invoke('20'.repeat(131073),'01'));
  const rows=await invoke(hex,'010203');const context=JSON.parse(Buffer.from(rows[0].context_hex,'hex').toString('utf8'));
  if(Object.keys(context).length!==11||context.interfaceVersion!=='truss-native-operation-context/0.3'||context.assertedOriginUtf8Hex!==hex||context.assertedOriginCaptureProfileHex!=='010203')throw Error('Original context byte correspondence');
  const actual=await tx`SELECT current_user::text AS actor,session_user::text AS login`;
  if(context.actingUser!==actual[0].actor||context.sessionUser!==actual[0].login)throw Error('Native actor substitution');
  checks.push('One original context0.3 artifact retains exact asserted whitespace/escapes and separate native actors/profile');
  const collected=await tx.unsafe('SELECT * FROM truss.runtime_collect_catalog_captured_context($1,$2,$3)',[rows[0].writer_xid,rows[0].ordinal,'0']);
  if(collected.length!==1||collected[0].context_hex!==rows[0].context_hex||collected[0].database_role!==actual[0].actor)throw Error('Original native collector correspondence');
  checks.push('Versioned native collector preserves exact context0.3 original bytes and actual actor');
  await refuse('Legacy context0.2 collector refuses context0.3','55000',()=>tx.unsafe('SELECT * FROM truss.runtime_collect_catalog_original_context($1,$2,$3)',[rows[0].writer_xid,rows[0].ordinal,'0']));
  for(const [writer,ordinal,generation] of [['1',rows[0].ordinal,'0'],[rows[0].writer_xid,'1','0'],[rows[0].writer_xid,rows[0].ordinal,'1']])await refuse('Unrelated captured-context cut refuses','55000',()=>tx.unsafe('SELECT * FROM truss.runtime_collect_catalog_captured_context($1,$2,$3)',[writer,ordinal,generation]));
  const decoded=decodeCapturedOriginContext(new Uint8Array(Buffer.from(rows[0].context_hex,'hex')));
  if(decoded.assertedUtf8Hex!==hex||decoded.captureProfileHex!=='010203'||decoded.origin.databaseRole!==actual[0].actor||decoded.journalOrigin.databaseRole!==actual[0].actor)throw Error('Original host decode correspondence');
  checks.push('Host maps exact retained native asserted capture with original acting role');
  for(const invalid of [{...context,interfaceVersion:'truss-native-operation-context/0.2'},{...context,assertedOriginUtf8Hex:'313233'},{...context,assertedOriginUtf8Hex:Buffer.from('{"a":null,"a":true}').toString('hex')},{...context,extra:'unknown'}]){
   let rejected=false;try{decodeCapturedOriginContext(new TextEncoder().encode(JSON.stringify(invalid)))}catch{rejected=true}if(!rejected)throw Error('Incomplete/invalid origin context decoded');
  }
  checks.push('Old context, numeric/duplicate asserted nodes and extra context fields refuse host mapping');

  await refuse('Context original bytes cannot be replaced','55000',()=>tx`UPDATE truss.row_home_operation SET original_context_bytes=decode('01','hex') WHERE original_writer_xid=pg_current_xact_id_if_assigned()`);
  await refuse('Original operation cannot be deleted','55000',()=>tx`DELETE FROM truss.row_home_operation WHERE original_writer_xid=pg_current_xact_id_if_assigned()`);
  const retained=await tx`SELECT encode(original_context_bytes,'hex') AS bytes FROM truss.row_home_operation WHERE original_writer_xid=pg_current_xact_id_if_assigned()`;
  if(retained.length!==1||retained[0].bytes!==rows[0].context_hex)throw Error('Original capture changed');
  checks.push('Failed substitutions preserve complete original context');
  throw Error('ROLLBACK_ASSERTED_CAPTURE');
 }).catch(e=>{if(e.message!=='ROLLBACK_ASSERTED_CAPTURE')throw e});
 const after=await sql`SELECT count(*)::text AS n FROM truss.row_home_operation`;if(after[0].n!=='0')throw Error('Rollback leaked capture');checks.push('Outer rollback removes captured operation');
 const sources:Record<string,string>={};for(const path of ['scripts/check-asserted-origin-admission.ts','packages/postgresql/native/operation-asserted-origin-admission.sql','packages/postgresql/native/operation-admission.sql','packages/postgresql/native/catalog-captured-context.sql','packages/postgresql/native/catalog-observation-recheck.sql','packages/postgresql/src/captured-origin-context.ts','packages/postgresql/src/asserted-origin-map.ts','packages/postgresql/native/catalog-input-custody.sql'])sources[path]=new Bun.CryptoHasher('sha256').update(await Bun.file(path).arrayBuffer()).digest('hex');
 await Bun.write('docs/helix/04-build/evidence/design-audit/asserted-origin-admission.json',JSON.stringify({sources,checks,scope:'Actual context0.3 original byte-capture and immutable custody on PostgreSQL17.9; profile bytes are explicit component inputs, not installed authority or complete asserted-origin semantic admission'},null,2)+'\n');console.log(JSON.stringify({checks:checks.length}));
}finally{await sql.close();}
