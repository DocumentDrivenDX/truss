/** Component native execution against the owner object definition; not protected engine adoption. */
import {SQL} from 'bun';
import {LocalPgProbe} from '../packages/weft-pg-probe/src/index';
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
 const probe=await createQueryEngine(compiler,input);
 const cases=[
  {sql:'SELECT COUNT(*) AS total FROM Customer c',expected:[[{integerToken:'2'}]]},
  {sql:'SELECT c.name,SUM(o.total) AS total FROM Customer c JOIN Orders o ON o.customer_id=c.id GROUP BY c.name',expected:[['Ada',{decimalToken:'25.00'}]]},
  {sql:'SELECT SUM(o.total) AS total FROM Orders o',emptyOrders:true,expected:[[null]]},
  {sql:'SELECT c.id FROM Customer c WHERE c.id > :cursor ORDER BY c.id LIMIT 2',parameters:{cursor:{family:'integer',value:'9007199254740993'}},expected:[[{integerToken:'9007199254740994'}]]},
  {sql:'SELECT c.id FROM Customer c WHERE c.name = :name ORDER BY c.id LIMIT 20',parameters:{name:{family:'string',value:"Ada'; DROP TABLE truss.object; --"}},expected:[]},
  {sql:'SELECT c.name,SUM(o.total) AS total FROM Customer c JOIN Orders o ON o.customer_id=c.id GROUP BY c.name',corruptDecimal:true,expected:[],refuse:true}
 ];
 let contexts=0,integrityChecks=0,nativeBindQueries=0;const observations=[];const nativeProfiles:any[]=[];const wireObservations:any[]=[];
 for(const scenario of cases){
  const original=await probe.compile(scenario.sql,scenario.parameters);let dataCommands=0;
  const handlers=Object.fromEntries(original.artifact.obligations.map(obligation=>[obligation.id,{
   accepts:(incoming:any)=>JSON.stringify(incoming)===JSON.stringify(obligation),async check(scope:any,_o:any,artifact:any){
    if(obligation.id==='truss.candidate.scalarIntegrity'){
     const checks=(obligation.parameters as any).checks;
     if(!Array.isArray(checks))throw Error('Unsupported component integrity');
     for(const check of checks){
      if(Object.keys(check).sort().join(',')!=='requiredViolations,sql'||check.requiredViolations!=='0'||typeof check.sql!=='string')throw Error('Unsupported integrity meaning');
      const rows=await scope.query(check.sql,artifact.parameters.map((p:any)=>p.value));
      if(JSON.stringify(rows)!==JSON.stringify([['0']]))throw Error('Native integrity violation');integrityChecks++;
     }
    }
   }
  }]));
  // Entire private relation is fixture-owned. This is not production authorization evidence.
  const host:Host={handlers,async withReadContext(body){const parsedUrl=new URL(url);if(parsedUrl.hostname!=='127.0.0.1'||parsedUrl.username!=='postgres'||parsedUrl.pathname!=='/postgres')throw Error('Explicit local test profile required');
   const native=await LocalPgProbe.connect(Number(parsedUrl.port));
   const tx={async unsafe(text:string){const r=await native.query(text);return r.rows.map(row=>Object.fromEntries(r.fields.map((name,i)=>[name,row[i]])))}};
   try{await native.query('BEGIN');
   await tx.unsafe('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');
   await tx.unsafe('CREATE TEMP TABLE object (LIKE truss.object INCLUDING ALL) ON COMMIT DROP');
   await tx.unsafe(`INSERT INTO object (id,type_id,props,rev) VALUES
     (100,-1,'{"0":9007199254740993,"1":"Ada","2":true,"4":[]}'::jsonb,1),
     (101,-1,'{"0":9007199254740994,"1":"Bea","2":true,"4":[]}'::jsonb,1),
     (200,-2,'{"6":1,"7":9007199254740993,"8":12.50}'::jsonb,1),
     (201,-2,'{"6":2,"7":9007199254740993,"8":12.50}'::jsonb,1)`);
   if(scenario.emptyOrders)await tx.unsafe('DELETE FROM object WHERE type_id=-2');
   if(scenario.corruptDecimal)await tx.unsafe(`UPDATE object SET props=jsonb_set(props,'{8}','\"invalid-decimal\"'::jsonb) WHERE id=200`);
   const observe=()=>tx.unsafe(`SELECT current_setting('server_version') AS version,current_setting('server_encoding') AS encoding,(SELECT datcollate FROM pg_catalog.pg_database WHERE datname=current_database()) AS collate,(SELECT datctype FROM pg_catalog.pg_database WHERE datname=current_database()) AS ctype,current_setting('transaction_isolation') AS isolation,current_setting('standard_conforming_strings') AS strings,current_user::text AS actor,txid_current_snapshot()::text AS snapshot`);
   const before=await observe(),profile=before[0];
   if(profile.version.split(' ')[0]!=='17.9'||profile.encoding!=='UTF8'||profile.collate!=='C'||profile.ctype!=='C'||profile.isolation!=='repeatable read'||profile.strings!=='on')throw Error('Native profile mismatch');
   nativeProfiles.push({...profile});const baseline=JSON.stringify(profile);
   const result=await body({async verifyContext(){contexts++;const after=await observe();if(JSON.stringify(after[0])!==baseline)throw Error('Native context changed')},
    async query(text,values){
     if(text===original.artifact.sql)dataCommands++;
     const response=await native.query(text,values);nativeBindQueries++;wireObservations.push({sql:text,parameters:values,fields:response.fields,command:response.command,ready:response.ready,originalRequestFrames:response.originalRequestFrames,originalResponseFrames:response.originalFrames});
     if(response.ready!=='T')throw Error('Lost original native transaction');
     return response.rows;
    }});
   const committed=await native.query('COMMIT');if(committed.command!=='COMMIT'||committed.ready!=='I')throw Error('Unconfirmed component transaction');return result;
   }catch(error){await native.query('ROLLBACK');throw error}finally{native.close()}
  },async decode(artifact,rows){if(artifact.columns.some((c:any)=>c.representation?.kind!=='scalar'||c.representation.carrier!=='text'||!['text','exact-integer','exact-decimal'].includes(c.representation.decoder)))throw Error('Unsupported component descriptor');return rows.map(row=>row.map((value,index)=>{
   const column=artifact.columns[index] as any,representation=column.representation;
   if(representation.kind!=='scalar'||representation.carrier!=='text')throw Error('Unsupported component decoder');
   if(value===null){if(!column.nullable)throw Error('Unexpected native null');return null}
   if(typeof value!=='string')throw Error('Nonexact scalar transport');
   switch(representation.decoder){
    case 'text':return value;
    case 'exact-integer':if(!/^-?\d+$/.test(value))throw Error('Nonexact integer');return {integerToken:value};
    case 'exact-decimal':if(!/^-?\d+(?:\.\d+)?$/.test(value))throw Error('Nonexact decimal');return {decimalToken:value};
    default:throw Error('Unsupported component decoder');
   }
  }))}};
  const engine=await createQueryEngine(compiler,input,host);const admitted=await engine.compile(scenario.sql,scenario.parameters);
  if(scenario.refuse){
   let refused=false;try{await engine.execute(admitted)}catch(error){if((error as Error).message!=='Native integrity violation')throw error;refused=true}
   if(!refused||dataCommands!==0)throw Error('Corrupt native data reached user SQL/publication');
   observations.push({query:scenario.sql,refused:'native integrity',dataCommands,originalResponse:admitted.originalResponse});continue;
  }
  const result=await engine.execute(admitted);
  if(JSON.stringify(result)!==JSON.stringify(scenario.expected))throw Error('Independent native expected result mismatch: '+JSON.stringify(result));
  observations.push({query:scenario.sql,result,originalResponse:admitted.originalResponse});
 }
 if(contexts!==11||integrityChecks<2)throw Error('Incomplete native checks');
 const receipt={sourceRevision:'2744531735c2a771fbe7ed24a7f67e3afc851b25',ddlSha256:new Bun.CryptoHasher('sha256').update(ddl).digest('hex'),observations,nativeProfiles,wireObservations,contextChecks:contexts,integrityChecks,forgedDigestRefused,nativeBindQueries,parameterTransport:'original SQL in Parse with explicit text OID25 and exact UTF-8 parameter bytes in native Bind; local trust-auth component, not production transport qualification',
  qualification:'Component COUNT, duplicate-preserving join SUM, empty SUM, exact logical-key paging, bound injection and corrupt-value refusal execution against temp object LIKE actual owner 0.13 repair definition in isolated PostgreSQL17.9. Fixture bindings/IDs only; no accepted catalog, protected mutations/feed, production authorization, complete transport/resource or installed runtime qualification.'};
 await Bun.write('docs/helix/04-build/evidence/weft-integration-native-component.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({cases:observations.length,contextChecks:contexts,integrityChecks,forgedDigestRefused}));
}finally{await sql.close()}
