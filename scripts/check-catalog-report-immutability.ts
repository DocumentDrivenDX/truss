import {SQL} from 'bun';
const url=process.env.TRUSS_OPERATION_TEST_URL;if(!url)throw Error('Explicit isolated native test URL required');
const sourcePath='packages/postgresql/native/catalog-report-immutability.sql',source=await Bun.file(sourcePath).text();
const sql=new SQL(url,{max:1,connectionTimeout:5});
try{
 const observed=await sql.begin(async tx=>{
  // Exact trigger body in a temporary byte-home fixture, not an accepted report.
  await tx.unsafe('CREATE TEMP TABLE catalog_acceptance_report(rev int PRIMARY KEY,report_bytes bytea NOT NULL) ON COMMIT DROP');
  await tx.unsafe(source.replaceAll('truss.','pg_temp.'));
  await tx.unsafe("INSERT INTO pg_temp.catalog_acceptance_report VALUES (1,decode('000102ff','hex'))");
  const checks:string[]=[];
  for(const mode of ['origin','replica']){
   await tx.unsafe('SET LOCAL session_replication_role='+mode);
   for(const mutation of ["UPDATE pg_temp.catalog_acceptance_report SET report_bytes=decode('ab','hex') WHERE rev=1","DELETE FROM pg_temp.catalog_acceptance_report WHERE rev=1","TRUNCATE pg_temp.catalog_acceptance_report"]){
    await tx.unsafe('SAVEPOINT report_negative');let refused=false;
    try{await tx.unsafe(mutation)}catch(error){const e=error as {code?:string;errno?:string};if((e.errno??e.code)!=='55000')throw error;refused=true}
    await tx.unsafe('ROLLBACK TO SAVEPOINT report_negative');await tx.unsafe('RELEASE SAVEPOINT report_negative');
    if(!refused)throw Error('Immutable report mutation admitted');checks.push(mode+': '+mutation.split(' ')[0]+' refused');
   }
  }
  const rows=await tx.unsafe("SELECT rev::text,encode(report_bytes,'hex') AS bytes FROM pg_temp.catalog_acceptance_report");
  if(rows.length!==1||rows[0].rev!=='1'||rows[0].bytes!=='000102ff')throw Error('Original bytes changed');checks.push('original byte inventory preserved after all refusals');
  const triggers=await tx.unsafe("SELECT tgenabled::text AS mode FROM pg_trigger WHERE tgrelid='pg_temp.catalog_acceptance_report'::regclass AND NOT tgisinternal");
  if(triggers.length!==2||triggers.some((r:{mode:string})=>r.mode!=='A'))throw Error('Unavoidable replica dispatch missing');checks.push('both triggers ENABLE ALWAYS');
  const version=await tx.unsafe('SHOW server_version');return {engine:version[0].server_version,checks};
 });
 const receipt={...observed,sourceSha256:new Bun.CryptoHasher('sha256').update(source).digest('hex'),scope:'Actual native immutable report byte-home trigger in temporary fixture. No insert admission, accepted report, full privilege/dependency installation, retention or head publication qualification.'};
 await Bun.write('docs/helix/04-build/evidence/catalog-report-immutability.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
}finally{await sql.close()}
