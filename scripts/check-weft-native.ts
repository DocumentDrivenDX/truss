/** Component native execution against the owner object definition; not protected engine adoption. */
import {SQL} from 'bun';
import {createQueryEngine,type Host,type BindingInput} from '../packages/weft/src/index';
import {loadCompiler} from '../packages/weft-bun/src/index';
const directory=process.env.TRUSS_WEFT_BUILD;if(!directory)throw Error('TRUSS_WEFT_BUILD required');
const url=process.env.TRUSS_WEFT_TEST_URL;if(!url)throw Error('Explicit isolated test database required');
const sql=new SQL(url,{max:1});
const source='docs/helix/04-build/evidence/weft-integration-layout-0.13.owner-export.sql';
const ddl=await Bun.file(source).text();
const request=await Bun.file('tests/weft/fixtures/qualified-count.request.json').json();
const compiler=await loadCompiler(directory);
const input:BindingInput={...request.target,modules:request.modules};
try {
 await sql.unsafe(ddl).simple();
 let forgedDigestRefused=false;
 await sql.begin(async tx=>{
  await tx.unsafe('CREATE TEMP TABLE archive_probe (LIKE truss.installation_archive INCLUDING ALL) ON COMMIT DROP');
  const identity='雪\\identity';
  const expected=new Bun.CryptoHasher('sha256').update(identity).digest('hex');
  await tx.unsafe("INSERT INTO archive_probe (installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES ('component','input',$1,decode('01','hex'),decode($2,'hex'))",[identity,expected]);
  try {await tx.savepoint(async sp=>{await sp.unsafe("INSERT INTO archive_probe (installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES ('component','input',$1,decode('01','hex'),decode(repeat('00',32),'hex'))",[identity])})}
  catch(error){if((error as any).errno!=='23514')throw error;forgedDigestRefused=true}
 });
 if(!forgedDigestRefused)throw Error('Forged UTF-8 identity digest admitted');
 const probe=await createQueryEngine(compiler,input);const plan=await probe.compile('SELECT COUNT(*) AS total FROM Customer c');
 let contexts=0;const handlers=Object.fromEntries(plan.artifact.obligations.map(obligation=>[obligation.id,{
  accepts:(incoming:any)=>JSON.stringify(incoming)===JSON.stringify(obligation),async check(){
   if(obligation.id==='truss.candidate.scalarIntegrity'&&JSON.stringify(obligation.parameters)!==JSON.stringify({checks:[],context:'same snapshot before casts/user filters',domainQualification:'separate exact facets/codec obligation'}))throw Error('Unsupported component integrity');
  }
 }]));
 // Trusted fixture host controls the entire private temp relation. No production authorization claim.
 const host:Host={handlers,async withReadContext(body){return sql.begin(async tx=>{
  await tx.unsafe('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');
  await tx.unsafe('CREATE TEMP TABLE object (LIKE truss.object INCLUDING ALL)');
  await tx.unsafe(`INSERT INTO object (id,type_id,props,rev) VALUES (100,-1,'{}'::jsonb,1),(101,-1,'{}'::jsonb,1)`);
  const before=await tx.unsafe(`SELECT current_setting('server_version') AS version,current_setting('server_encoding') AS encoding,(SELECT datcollate FROM pg_catalog.pg_database WHERE datname=current_database()) AS collate,(SELECT datctype FROM pg_catalog.pg_database WHERE datname=current_database()) AS ctype,current_setting('transaction_isolation') AS isolation,current_setting('standard_conforming_strings') AS strings,current_user::text AS actor,txid_current_snapshot()::text AS snapshot`);
  const profile=before[0];if(!profile.version.startsWith('17.9')||profile.encoding!=='UTF8'||profile.collate!=='C'||profile.ctype!=='C'||profile.isolation!=='repeatable read'||profile.strings!=='on')throw Error('Native profile mismatch');
  const baseline=JSON.stringify(profile);
  return body({async verifyContext(){contexts++;const after=await tx.unsafe(`SELECT current_setting('server_version') AS version,current_setting('server_encoding') AS encoding,(SELECT datcollate FROM pg_catalog.pg_database WHERE datname=current_database()) AS collate,(SELECT datctype FROM pg_catalog.pg_database WHERE datname=current_database()) AS ctype,current_setting('transaction_isolation') AS isolation,current_setting('standard_conforming_strings') AS strings,current_user::text AS actor,txid_current_snapshot()::text AS snapshot`);if(JSON.stringify(after[0])!==baseline)throw Error('Native context changed')},
   async query(text,values){return tx.unsafe(text,[...values]).values() as any}});
 })},async decode(artifact,rows){if(artifact.columns.length!==1||(artifact.columns[0] as any).representation.decoder!=='exact-integer')throw Error('Unsupported component decoder');return rows.map(row=>{if(typeof row[0]!=='string'||!/^\d+$/.test(row[0]))throw Error('Nonexact COUNT');return {integerToken:row[0]}})}};
 const engine=await createQueryEngine(compiler,input,host);const admitted=await engine.compile('SELECT COUNT(*) AS total FROM Customer c');const result=await engine.execute(admitted);
 if(JSON.stringify(result)!==JSON.stringify([{integerToken:'2'}])||contexts!==2)throw Error('Native result/context mismatch');
 const receipt={sourceRevision:'2744531735c2a771fbe7ed24a7f67e3afc851b25',ddlSha256:new Bun.CryptoHasher('sha256').update(ddl).digest('hex'),result,contextChecks:contexts,forgedDigestRefused,
  qualification:'Component COUNT execution against temp object LIKE actual owner 0.13 repair definition in isolated PostgreSQL17.9. Fixture bindings/IDs only; no accepted catalog, protected mutations/feed, production authorization, complete transport/resource or installed runtime qualification.'};
 await Bun.write('docs/helix/04-build/evidence/weft-integration-native-component.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
}finally{await sql.close()}
