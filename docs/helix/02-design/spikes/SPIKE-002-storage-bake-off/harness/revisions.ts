// SPIKE-002 Method 3 / Question 1: apply R1-R5 while a background writer (pgbench, 2 clients, 100 tx/s total)
// inserts orders with two lines. Records per step: statements, rows changed, table rewrites (relfilenode), the
// strongest lock the revision session held on each relation (pg_locks polled every 5 ms from a second session plus a
// snapshot before COMMIT), elapsed time, writer latency during the revision window, and violation detection.
// Usage: VARIANT=a|c-engine|c-db bun harness/revisions.ts   -> out/30_revisions_<variant>_pg$PGVER.txt
import {SQL} from 'bun';
import {readFileSync,writeFileSync,mkdirSync,readdirSync,rmSync} from 'node:fs';
import {join,dirname} from 'node:path';
import {createHash} from 'node:crypto';
import {loadCatalog} from '../loader/engine';
import {planRevision,violatorsSql,checkReplaceSql,checkValidateSql,type Transform} from '../loader/revise';
const spike=join(dirname(new URL(import.meta.url).pathname),'..');
const variant=process.env.VARIANT??'a';const W=join(process.env.WORK!,'revisions',variant);rmSync(W,{recursive:true,force:true});mkdirSync(W,{recursive:true});
const opts={path:`${process.env.PGHOST??'/tmp'}/.s.PGSQL.${process.env.PGPORT}`,username:'postgres',database:process.env.PGDATABASE??'bakeoff'};
const sql=new SQL({...opts,max:1}),mon=new SQL({...opts,max:1});
const out:string[]=[];const log=(s:string)=>{out.push(s);console.log(s);};
const MODES=['AccessShareLock','RowShareLock','RowExclusiveLock','ShareUpdateExclusiveLock','ShareLock','ShareRowExclusiveLock','ExclusiveLock','AccessExclusiveLock'];
const tables=variant==='a'?['sales.customers','sales.orders','sales.order_lines','sales.products']:['c.object','c.edge','c.journal','c.prop_def','c.rel_def'];
log(`== ${(await sql`SELECT version() v`)[0].v}; variant=${variant}`);
await sql.unsafe(`CREATE SEQUENCE IF NOT EXISTS c.key_seq START 10000000`);
const pid=(await sql`SELECT pg_backend_pid() p`)[0].p;
const filenodes=async()=>Object.fromEntries((await mon.unsafe(`SELECT relname, relfilenode FROM pg_class WHERE oid = ANY(ARRAY[${tables.map(t=>`'${t}'::regclass`).join(',')}])`)).map((r:any)=>[r.relname,r.relfilenode]));
interface Step {label:string;stmts:string[];tx:boolean;expectFail?:boolean;detect?:string[]}
async function runRevision(id:string,title:string,steps:Step[]){
  log(`\n### ${id} ${title} [${variant}]`);
  const writer=Bun.spawn(['pgbench','-n','-M','prepared','-c','2','-j','2','-R','100','-T','25','-f',join(spike,variant==='a'?'bench/writer_a.sql':'bench/writer_c.sql'),'-l','--log-prefix=w'],{cwd:W,stdout:'pipe',stderr:'pipe'});
  await Bun.sleep(4000);
  const locks=new Map<string,number>();let polling=true;
  const poller=(async()=>{while(polling){for(const r of await mon.unsafe(`SELECT mode, coalesce(relation::regclass::text, locktype) AS rel FROM pg_locks WHERE pid = ${pid} AND granted AND locktype = 'relation'`))if(tables.includes(r.rel))locks.set(r.rel,Math.max(locks.get(r.rel)??-1,MODES.indexOf(r.mode)));await Bun.sleep(5);}})();
  const fn0=await filenodes();const t0=Date.now();let rejected='';const rows:string[]=[];
  for(const s of steps){
    const ts=Date.now();
    try{
      if(s.tx){await sql.begin(async(tx:any)=>{let cat=0;for(const st of s.stmts){const r=await tx.unsafe(st);if(/^\s*INSERT INTO c\.(schema_rev|type_def|prop_def|key_def|rel_def|rel_endpoint)/i.test(st))cat+=Number(r.count??0);else if(r.count!==undefined&&/^\s*(UPDATE|INSERT|DELETE|WITH)/i.test(st))rows.push(`${s.label}: ${r.count} rows (${r.command})`);}
          if(cat)rows.push(`${s.label}: ${cat} catalog rows inserted/updated`);
          for(const d of s.detect??[]){const v=await tx.unsafe(d);if(v.length){rejected=`${v.length} stored objects violate the new rule (first ids: ${v.slice(0,5).map((x:any)=>x.id).join(',')})`;throw new Error('REJECT '+rejected);}}
          for(const r of await tx.unsafe(`SELECT mode, relation::regclass::text AS rel FROM pg_locks WHERE pid = pg_backend_pid() AND relation IS NOT NULL`))if(tables.includes(r.rel))locks.set(r.rel,Math.max(locks.get(r.rel)??-1,MODES.indexOf(r.mode)));});}
      else for(const st of s.stmts){const r=await sql.unsafe(st);if(/^\s*(UPDATE|INSERT|DELETE|WITH)/i.test(st))rows.push(`${s.label}: ${r.count} rows`);if(/^\s*SELECT/i.test(st)&&r.length)rows.push(`${s.label}: ${r.length} violating rows listed (first: ${JSON.stringify(r[0])})`);}
      log(`  step ${s.label}: ok in ${Date.now()-ts} ms${s.expectFail?' (UNEXPECTED success)':''}`);
    }catch(e:any){if(s.expectFail&&!rejected)rejected=`DDL refused: ${String(e.message).replace(/\s+/g,' ')} (first error only)`;log(`  step ${s.label}: ${s.expectFail||String(e.message).startsWith('REJECT')?'REJECTED (detected before acceptance)':'FAILED'} in ${Date.now()-ts} ms: ${String(e.message).replace(/\s+/g,' ')}`);if(!s.expectFail&&!String(e.message).startsWith('REJECT'))throw e;}
  }
  const t1=Date.now();polling=false;await poller;const fn1=await filenodes();
  const exit=await writer.exited;const wout=await new Response(writer.stdout).text()+await new Response(writer.stderr).text();
  const lat:{end:number;ms:number;lag:number}[]=[];
  for(const f of readdirSync(W).filter(f=>f.startsWith('w.')))for(const l of readFileSync(join(W,f),'utf8').split('\n'))if(l){const x=l.split(' ');lat.push({end:Number(x[4])*1000+Number(x[5])/1000,ms:Number(x[2])/1000,lag:Number(x[6]??0)/1000});}
  for(const f of readdirSync(W).filter(f=>f.startsWith('w.')))rmSync(join(W,f));
  const inWin=lat.filter(x=>x.end>=t0&&x.end-x.ms-x.lag<=t1+50),before=lat.filter(x=>x.end<t0).map(x=>x.ms).sort((a,b)=>a-b);
  const maxLat=Math.max(0,...inWin.map(x=>x.ms+x.lag));
  const strongest=[...locks].map(([r,m])=>`${r}=${MODES[m]}`).join(', ');
  const rewritten=Object.keys(fn0).filter(k=>fn0[k]!==fn1[k]);
  log(`  elapsed: ${t1-t0} ms; rows changed: ${rows.length?rows.join('; '):'0'}; table rewrites (new relfilenode): ${rewritten.length?rewritten.join(', '):'none'}`);
  log(`  strongest locks held by the revision session: ${strongest||'none observed'}`);
  log(`  writer: ${lat.length} tx total, ${inWin.length} overlapping the revision; p50 before ${before[Math.floor(before.length/2)]?.toFixed(2)} ms; max latency (incl. schedule lag) while revising ${maxLat.toFixed(1)} ms; pgbench exit ${exit}${/aborted|error/i.test(wout)?'; writer errors: '+wout.split('\n').filter(l=>/abort|ERROR/i.test(l)).slice(0,3).join(' | '):''}`);
  log(`  violation detection before acceptance: ${rejected||'n/a or none found'}`);
}

if(variant==='a'){
  const R=readFileSync(join(spike,'sql/a_revisions.sql'),'utf8').split('\n').filter(l=>l&&!l.startsWith('--'));
  const [r1,r2try,r2list,r2fix,r2apply,r3a,r3b,r4,r5a,r5b]=R as string[];
  await runRevision('R1','add optional Customer.phone',[{label:'ALTER ADD COLUMN',stmts:[r1!],tx:true}]);
  await runRevision('R2','tighten Customer.name 100 -> 60',[{label:'attempt ALTER TYPE varchar(60)',stmts:[r2try!],tx:true,expectFail:true},{label:'list violators',stmts:[r2list!],tx:false},{label:'remediate (truncate) + ALTER TYPE',stmts:[r2fix!,r2apply!],tx:true}]);
  await runRevision('R3','add Customer -> Customer referredBy',[{label:'ADD COLUMN + FK + index',stmts:[r3a!,r3b!],tx:true}]);
  await runRevision('R4','Customer.email one -> array',[{label:'ALTER TYPE varchar(200)[] USING',stmts:[r4!],tx:true}]);
  await runRevision('R5','Order.channel -> required, backfill',[{label:'backfill UPDATE',stmts:[r5a!],tx:true},{label:'SET NOT NULL',stmts:[r5b!],tx:true}]);
}else{
  const db=variant==='c-db';const binding=JSON.parse(readFileSync(join(spike,'model/sales.binding.json'),'utf8'));
  const doc=(n:number)=>readFileSync(join(spike,`model/sales.rev${n}.umf.json`),'utf8');
  async function cRev(n:number,title:string,transforms:Transform[]=[],remediate:Transform[]=[]){
    const prior=await loadCatalog(sql);const text=doc(n);const plan=planRevision(prior,JSON.parse(text),n,transforms,binding);
    const sha=createHash('sha256').update(text).digest('hex');
    const covered=new Set(transforms.map(t=>plan.catalog.props.find(p=>p.element===t.element)!.prop_id));
    const detect=plan.changedRules.filter(r=>![...covered].some(pid=>r.name.includes(`_p${pid}_`))).map(r=>violatorsSql(r)+' LIMIT 1000');
    const accept=(label:string):Step=>({label,tx:true,detect,stmts:[`INSERT INTO c.schema_rev VALUES (${n},'0.7.0','${sha}',$umf$${text}$umf$) ON CONFLICT (rev) DO NOTHING`,...plan.catalogSql.trim().split('\n'),...(db?checkReplaceSql(plan):[])]});
    const steps:Step[]=[];
    if(remediate.length){steps.push(accept('attempt: catalog + detection'+(db?' + CHECK swap':'')));
      const fix=planRevision(prior,JSON.parse(doc(n-1)),n-1,remediate,binding);steps.push({label:'remediate (generic truncate transform)',tx:true,stmts:fix.transforms});}
    steps.push(accept('accept: catalog rows + detection'+(db?' + CHECK swap (NOT VALID)':'')));
    if(plan.transforms.length)steps.push({label:'generic data transform + journal',tx:true,stmts:plan.transforms});
    if(plan.changedRules.length)steps.push(db?{label:'VALIDATE CONSTRAINT',tx:false,stmts:checkValidateSql(plan)}:{label:'verify: count violators of changed rules',tx:false,stmts:plan.changedRules.map(r=>violatorsSql(r)+' LIMIT 5')});
    if(db&&plan.newIndexes.length)steps.push({label:'CREATE UNIQUE INDEX CONCURRENTLY',tx:false,stmts:plan.newIndexes.map(s=>s.replace('CREATE UNIQUE INDEX IF NOT EXISTS','CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS'))});
    log(`  [plan rev${n}] catalog statements=${plan.catalogSql.trim().split('\n').length}; changed rules=${plan.changedRules.map(r=>r.name).join(',')||'none'}; dropped=${plan.droppedRules.join(',')||'none'}; new indexes=${plan.newIndexes.length}; transforms=${plan.transforms.length}`);
    await runRevision(`R${n}`,title,steps);
  }
  await cRev(1,'add optional Customer.phone');
  await cRev(2,'tighten Customer.name 100 -> 60',[],[{kind:'truncate-string',element:'Customer.name',max:60}]);
  await cRev(3,'add Customer -> Customer referredBy');
  await cRev(4,'Customer.email one -> array',[{kind:'wrap-in-array',element:'Customer.email'}]);
  await cRev(5,'Order.channel -> required, backfill',[{kind:'fill-absent',element:'Order.channel',valueJson:'"web"'}]);
}
writeFileSync(join(spike,`out/30_revisions_${variant}_pg${process.env.PGVER??"17"}${process.env.OUTSUF??""}.txt`),out.join('\n')+'\n');
await sql.close();await mon.close();
