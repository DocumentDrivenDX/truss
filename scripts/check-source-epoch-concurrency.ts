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
  await tx.unsafe(`INSERT INTO ${namespace}.installation_marker VALUES ('component-installation')`);
  await tx.unsafe(`INSERT INTO ${namespace}.source_epoch_registry (installation_id,source_epoch,target_incarnation,predecessor_epoch,transition_reason,profile_bytes,evidence_bytes) VALUES ('component-installation','component-initial','component-incarnation',NULL,'initial',decode('01','hex'),decode('02','hex')),('component-installation','component-next','component-incarnation','component-initial','restore',decode('01','hex'),decode('03','hex'))`);
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
   await tx.unsafe(`UPDATE ${namespace}.source_epoch_current SET source_epoch='component-next' WHERE singleton_id=1`);
  });}catch(e){observed=(e as any).errno??(e as any).code;}
  if(observed!=='55P03')throw Error('Concurrent pointer update did not wait on admitted writer: '+observed);
  checks.push('Concurrent transition hits native lock timeout while writer holds shared pointer lock');
 }finally{release();await writer;}
 checks.push('Writer retains original epoch until transaction completion');
 await b.unsafe(`UPDATE ${namespace}.source_epoch_current SET source_epoch='component-next' WHERE singleton_id=1`);
 const next=await a.begin(tx=>tx.unsafe(`SELECT * FROM ${namespace}.runtime_lock_source_epoch('component-installation','component-next','component-incarnation')`));
 if(next.length!==1||next[0].source_epoch!=='component-next'||next[0].evidence_hex!=='03')throw Error('Successor admission failed');
 checks.push('Transition succeeds after writer completes and next admission returns successor evidence');
 const version=await a`SELECT version() AS version`;
 const sources:Record<string,string>={};for(const path of ['scripts/check-source-epoch-concurrency.ts','packages/postgresql/native/source-epoch-lock.sql','packages/postgresql/native/source-epoch-immutability.sql','docs/helix/04-build/evidence/source-epoch-storage.owner-export.sql'])sources[path]=new Bun.CryptoHasher('sha256').update(await Bun.file(path).arrayBuffer()).digest('hex');
 await Bun.write('docs/helix/04-build/evidence/design-audit/source-epoch-concurrency.json',JSON.stringify({database:version[0].version,sources,checks,scope:'Two original native connections, synthetic component namespace/marker and tokens; lock behavior only, not issuer/transition authority or complete installed admission',qualified:false},null,2)+'\n');
 console.log(JSON.stringify({checks:checks.length,qualified:false}));
}finally{
 if(created)await a.unsafe(`DROP SCHEMA ${namespace} CASCADE`);
 await Promise.all([a.close(),b.close()]);
}
