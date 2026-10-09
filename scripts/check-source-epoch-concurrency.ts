/** Two-connection lock schedule; isolated component namespace, no issued epochs. */
import {SQL} from 'bun';
const url=process.env.TRUSS_OPERATION_TEST_URL;
if(!url?.startsWith('postgres://postgres@127.0.0.1:15434/'))throw Error('Owned fixture URL required');
const a=new SQL(url,{max:1}),b=new SQL(url,{max:1});
const namespace='truss_epoch_lock_component';let created=false;
const checks:string[]=[];
try {
 const existing=await a`SELECT to_regnamespace(${namespace})::text AS n`;
 if(existing[0].n!==null)throw Error('Component namespace already exists; refuse overwrite');
 await a.begin(async tx=>{
  await tx.unsafe(`CREATE SCHEMA ${namespace}`);
  await tx.unsafe(`CREATE TABLE ${namespace}.installation_marker (installation_id text COLLATE pg_catalog."C" PRIMARY KEY)`);
  await tx.unsafe((await Bun.file('docs/helix/04-build/evidence/source-epoch-storage.owner-export.sql').text()).replaceAll('truss.',namespace+'.'));
  await tx.unsafe((await Bun.file('packages/postgresql/native/source-epoch-immutability.sql').text()).replaceAll('truss.',namespace+'.'));
  await tx.unsafe((await Bun.file('packages/postgresql/native/source-epoch-lock.sql').text()).replaceAll('truss.',namespace+'.'));
  await tx.unsafe((await Bun.file('packages/postgresql/native/source-epoch-issue.sql').text()).replaceAll('truss.',namespace+'.'));
  await tx.unsafe(`INSERT INTO ${namespace}.installation_marker VALUES ('component-installation')`);
  await tx.unsafe(`INSERT INTO ${namespace}.source_epoch_registry (installation_id,source_epoch,target_incarnation,predecessor_epoch,transition_reason,profile_bytes,evidence_bytes) VALUES ('component-installation','component-initial','component-incarnation',NULL,'initial',decode('01','hex'),decode('02','hex'))`);
  await tx.unsafe(`INSERT INTO ${namespace}.source_epoch_current VALUES (1,'component-installation','component-initial')`);
 });created=true;
 let release!:()=>void,admitted!:()=>void;
 const gate=new Promise<void>(resolve=>release=resolve),ready=new Promise<void>(resolve=>admitted=resolve);
 const writer=a.begin(async tx=>{
  const rows=await tx.unsafe(`SELECT * FROM ${namespace}.runtime_lock_source_epoch('component-installation','component-initial','component-incarnation')`);
  if(rows.length!==1||rows[0].source_epoch!=='component-initial')throw Error('Initial admission failed');
  admitted();await gate;
  const original=await tx.unsafe(`SELECT source_epoch FROM ${namespace}.source_epoch_current`);
  if(original[0].source_epoch!=='component-initial')throw Error('Transition straddled held writer');
 });
 try {
  await Promise.race([ready,writer.then(()=>{throw Error('Writer ended before readiness');})]);
  let observed='';try{await b.begin(async tx=>{
   await tx`SET LOCAL lock_timeout='250ms'`;
   await tx.unsafe(`SELECT ${namespace}.runtime_issue_source_epoch('component-installation','component-initial','component-restored-incarnation',decode('01','hex'),decode('04','hex'))`);
  });}catch(e){observed=(e as any).errno??(e as any).code;}
  if(observed!=='55P03')throw Error('Concurrent issuer did not wait on admitted writer: '+observed);
  checks.push('Concurrent native issuer hits native lock timeout while writer holds shared pointer lock');
  const pending=await b.unsafe(`SELECT count(*)::text AS n FROM ${namespace}.source_epoch_registry`);
  if(pending[0].n!=='1')throw Error('Timed-out issuer leaked epoch');
  checks.push('Timed-out issuer leaves no speculative successor');
 }finally{release();await writer;}
 checks.push('Writer retains original epoch until transaction completion');
 const issued=await b.unsafe(`SELECT ${namespace}.runtime_issue_source_epoch('component-installation','component-initial','component-restored-incarnation',decode('01','hex'),decode('04','hex')) AS epoch`);
 const successor=issued[0].epoch;
 if(!/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(successor))throw Error('Issued successor grammar');
 const next=await a.begin(tx=>tx.unsafe(`SELECT * FROM ${namespace}.runtime_lock_source_epoch('component-installation','${successor}','component-restored-incarnation')`));
 if(next.length!==1||next[0].source_epoch!==successor||next[0].evidence_hex!=='04')throw Error('Successor admission failed');
 checks.push('Transition succeeds after writer completes and next admission returns successor evidence');
 const lineage=await a.unsafe(`SELECT source_epoch,predecessor_epoch FROM ${namespace}.source_epoch_registry WHERE predecessor_epoch IS NOT NULL`);
 if(lineage.length!==1||lineage[0].source_epoch!==successor||lineage[0].predecessor_epoch!=='component-initial')throw Error('Native issuer lineage mismatch');
 checks.push('Only successful native issuer retains the original predecessor lineage');
 const version=await a`SELECT version() AS version`;
 const sources:Record<string,string>={};for(const path of ['scripts/check-source-epoch-concurrency.ts','packages/postgresql/native/source-epoch-issue.sql','packages/postgresql/native/source-epoch-lock.sql','packages/postgresql/native/source-epoch-immutability.sql','docs/helix/04-build/evidence/source-epoch-storage.owner-export.sql'])sources[path]=new Bun.CryptoHasher('sha256').update(await Bun.file(path).arrayBuffer()).digest('hex');
 await Bun.write('docs/helix/04-build/evidence/design-audit/source-epoch-concurrency.json',JSON.stringify({database:version[0].version,sources,checks,scope:'Two original native connections and native issuer-generated successor, synthetic component namespace/marker and initial tokens; issuer locking behavior only, not issuer/transition authority or complete installed admission',qualified:false},null,2)+'\n');
 console.log(JSON.stringify({checks:checks.length,qualified:false}));
}finally{
 if(created)await a.unsafe(`DROP SCHEMA ${namespace} CASCADE`);
 await Promise.all([a.close(),b.close()]);
}
