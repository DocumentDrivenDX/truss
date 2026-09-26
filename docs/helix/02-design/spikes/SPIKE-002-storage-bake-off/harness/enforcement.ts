// SPIKE-002 Method 4 / Question 2: enforcement matrix. For every assertion: one violating and one control write per
// option and layer. A = UMF-generated tables + hand-written DDL; C-engine = loader/engine validation before any
// SQL; C-db = raw SQL straight into the shared tables (bypassing the engine) with the generated conditional CHECKs,
// edge FKs/indexes and generic deferred trigger installed. Every write runs in a transaction that is rolled back
// after `SET CONSTRAINTS ALL IMMEDIATE`, so deferred checks fire and the dataset is unchanged.
// Usage: bun harness/enforcement.ts   (env from env.sh; writes out/20_enforcement_pg$PGVER.txt)
import {SQL} from 'bun';
import {writeFileSync,readFileSync} from 'node:fs';
import {join,dirname} from 'node:path';
import {parseExact,type NJ} from '../loader/exact-json';
import {checkDdl,INVARIANTS,type Catalog} from '../loader/catalog';
import {encodeRecord,validateEncoded,insertEncoded,loadCatalog,propsText,EngineViolation,type Encoded} from '../loader/engine';
const spike=join(dirname(new URL(import.meta.url).pathname),'..');
const sql=new SQL({path:`${process.env.PGHOST??'/tmp'}/.s.PGSQL.${process.env.PGPORT}`,username:'postgres',database:process.env.PGDATABASE??'bakeoff',max:4});
const out:string[]=[];const log=(s:string)=>{out.push(s);console.log(s);};
class Rollback extends Error{}
const errText=(e:any)=>`${e.code??e.errno??''} ${e.message}`.replace(/\s+/g,' ').trim();
/** Run statements in a transaction, fire deferred constraints, roll back. Returns 'accepted' or the error. */
async function db(fn:(tx:any)=>Promise<void>):Promise<{ok:boolean;msg:string}>{
  try{await sql.begin(async(tx:any)=>{await fn(tx);await tx.unsafe('SET CONSTRAINTS ALL IMMEDIATE');throw new Rollback();});return {ok:true,msg:'accepted'};}
  catch(e:any){if(e instanceof Rollback)return {ok:true,msg:'accepted'};return {ok:false,msg:errText(e)};}
}
const ver=(await sql`SELECT version() v`)[0].v as string;log(`== ${ver}`);

// ---- install option C database-side checks (generated from the catalog) and time it ----
const cat:Catalog=await loadCatalog(sql);
const checks=checkDdl(cat,INVARIANTS.sql);
const have=(await sql`SELECT count(*)::int n FROM pg_constraint WHERE conrelid='c.object'::regclass AND conname LIKE 'ck_t%'`)[0].n;
if(have!==checks.length){
  const t0=performance.now();
  for(const c of checks)await sql.unsafe(`ALTER TABLE c.object DROP CONSTRAINT IF EXISTS ${c.name}; ALTER TABLE c.object ADD CONSTRAINT ${c.name} CHECK (${c.sql})`);
  log(`C-db: added ${checks.length} conditional CHECK constraints to c.object (validating ${(await sql`SELECT count(*)::int n FROM c.object`)[0].n} existing rows) in ${((performance.now()-t0)/1000).toFixed(1)} s`);
}else log(`C-db: ${checks.length} conditional CHECK constraints already installed`);

// ---- helpers ----
const J=(s:string)=>parseExact(s);
const enc=(type:string,json:string)=>encodeRecord(cat,type,J(json));
const cInsertRaw=async(tx:any,type:string,props:string,retained:string|null=null)=>(await tx.unsafe(`INSERT INTO c.object (type_id,props,retained,rev) VALUES ((SELECT type_id FROM c.type_def WHERE element=$1),$2::text::jsonb,$3::text::jsonb,0) RETURNING id`,[type,props,retained]))[0].id;
const objId=async(tx:any,type:string,key:string)=>{const t=cat.types.find(t=>t.element===type)!;const k=cat.keys.find(k=>k.type_id===t.type_id&&k.is_primary)!;return (await tx.unsafe(`SELECT id FROM c.object WHERE type_id=${t.type_id} AND (props->>'${k.prop_ids[0]}')::bigint = ${key}`))[0]?.id;};
const rel=(id:string)=>cat.rels.find(r=>r.rel_id===id)!.rel_type_id;
const T=(e:string)=>cat.types.find(t=>t.element===e)!.type_id;
const edge=async(tx:any,r:string,s:any,st:string,t:any,tt:string)=>tx.unsafe(`INSERT INTO c.edge (rel_type_id,source_id,source_type,target_id,target_type) VALUES (${rel(r)},${s},${T(st)},${t},${T(tt)})`);
/** Engine unit-of-work multiplicity check: every min>0 end of every relationship touching a new object in the unit. */
function unitViolations(unit:{type:string;e:Encoded;key:string}[]):{rule:string;message:string}[]{
  const v:{rule:string;message:string}[]=[];
  for(const u of unit)for(const r of cat.rels.filter(r=>!r.composition)){
    const t=u.e.typeId;
    if(r.endpoints.some(([s])=>s===t)&&r.target_min>0){ // outgoing: own refs (dir out) + unit members pointing at us via inverse
      const n=u.e.refs.filter(x=>x.relId===r.rel_type_id&&x.dir==='out').length+unit.filter(o=>o.e.refs.some(x=>x.relId===r.rel_type_id&&x.dir==='in'&&x.key.kind==='number'&&x.key.value===u.key&&x.targetType===t)).length;
      if(n<r.target_min)v.push({rule:`rel:${r.rel_id}:target-min`,message:`${u.type} ${u.key} has ${n} (min ${r.target_min})`});}
    if(r.endpoints.some(([s])=>s===t)&&r.target_max!==null){const n=u.e.refs.filter(x=>x.relId===r.rel_type_id&&x.dir==='out').length;if(n>r.target_max)v.push({rule:`rel:${r.rel_id}:target-max`,message:`${u.type} ${u.key} has ${n} (max ${r.target_max})`});}
    if(r.endpoints.some(([,tt])=>tt===t)&&r.source_max!==null){const n=u.e.refs.filter(x=>x.relId===r.rel_type_id&&x.dir==='in').length;if(n>r.source_max)v.push({rule:`rel:${r.rel_id}:source-max`,message:`${u.type} ${u.key} has ${n} (max ${r.source_max})`});}
    if(r.endpoints.some(([,tt])=>tt===t)&&r.source_min>0){
      const n=u.e.refs.filter(x=>x.relId===r.rel_type_id&&x.dir==='in').length;
      if(n<r.source_min)v.push({rule:`rel:${r.rel_id}:source-min`,message:`${u.type} ${u.key} has ${n} (min ${r.source_min})`});}
  }
  return v;
}
async function engine(unit:{type:string;json:string}[]):Promise<{ok:boolean;msg:string}>{
  const encs=unit.map(u=>({type:u.type,e:enc(u.type,u.json),key:(J(u.json) as any).members.id?.value}));
  const v=[...encs.flatMap(u=>validateEncoded(cat,u.e).map(x=>({rule:x.rule,message:`${x.path}: ${x.message}`}))),...unitViolations(encs)];
  if(v.length)return {ok:false,msg:'ENGINE '+v.map(x=>`${x.rule} (${x.message})`).join('; ')};
  const r=await db(async tx=>{for(const u of encs)await insertEncoded(tx,cat,u.e,{validate:false,journal:true});});
  if(!r.ok&&r.msg.includes('engine rejected write'))return {ok:false,msg:'ENGINE '+r.msg.replace(/^.*engine rejected write: /,'')};
  return r.ok?{ok:true,msg:'accepted by engine and database'+(encs.some(u=>u.e.retained)?`; retained=${encs.map(u=>u.e.retained?propsText(u.e.retained):'').join('')}`:'')}:{ok:false,msg:'DB (after engine accepted) '+r.msg};
}

// ---- base records ----
const cust=(o:string='')=>`{"id":900001,"code":"T900001","name":"Test customer","createdAt":"2026-09-25T10:00:00+02:00"${o}}`;
const ord=(o:string='',cust='1')=>`{"id":900001,"placedAt":"2026-09-25T10:00:00Z","status":"paid","total":10.00,"customer":${cust}${o}}`;
const line=(o:string='',id='900001')=>`{"id":${id},"lineNo":1,"quantity":2,"unitPrice":5.00,"lineTotal":10.00,"order":900001,"product":1${o}}`;
const custSql=(cols:string,vals:string)=>`INSERT INTO sales.customers (id,code,name,"createdAt"${cols}) VALUES (900001,'T900001','Test customer','2026-09-25T10:00:00+02:00'${vals})`;
const ordSql=(total='10.00',cust='1',status=`'paid'`)=>`INSERT INTO sales.orders (id,"placedAt",status,total,"customerId") VALUES (900001,'2026-09-25T10:00:00Z',${status},${total},${cust})`;
const lineSql=(o:{id?:string;lineNo?:string;q?:string;up?:string;lt?:string}={})=>`INSERT INTO sales.order_lines (id,"lineNo",quantity,"unitPrice","lineTotal","orderId","productId") VALUES (${o.id??'900001'},${o.lineNo??'1'},${o.q??'2'},${o.up??'5.00'},${o.lt??'10.00'},900001,1)`;
// C-db raw writes: encode (no validation) then insert straight into the shared tables
const cCust=async(tx:any,json:string)=>{const e=enc('Customer',json);return cInsertRaw(tx,'Customer',propsText(e.props),e.retained?propsText(e.retained):null);};
const cOrder=async(tx:any,json:string,withCustomer=true,withLine=true)=>{const e=enc('Order',json);const o=await cInsertRaw(tx,'Order',propsText(e.props));
  if(withCustomer)await edge(tx,'order-customer',o,'Order',await objId(tx,'Customer','1'),'Customer');
  if(withLine){const l=await cInsertRaw(tx,'OrderLine',propsText(enc('OrderLine',line()).props));await edge(tx,'order-lines',o,'Order',l,'OrderLine');await edge(tx,'line-product',l,'OrderLine',await objId(tx,'Product','1'),'Product');}
  return o;};

type Case={id:string;assertion:string;a:[()=>Promise<any>,()=>Promise<any>];ce:[()=>Promise<any>,()=>Promise<any>];cd:[()=>Promise<any>,()=>Promise<any>]};
const cases:Case[]=[
 {id:'N1',assertion:'nullability required: Customer.name absent',
  a:[()=>db(tx=>tx.unsafe(`INSERT INTO sales.customers (id,code,"createdAt") VALUES (900001,'T900001',now())`)),()=>db(tx=>tx.unsafe(custSql('','')))],
  ce:[()=>engine([{type:'Customer',json:`{"id":900001,"code":"T900001","createdAt":"2026-09-25T10:00:00Z"}`}]),()=>engine([{type:'Customer',json:cust()}])],
  cd:[()=>db(async tx=>{await cCust(tx,`{"id":900001,"code":"T900001","createdAt":"2026-09-25T10:00:00Z"}`);}),()=>db(async tx=>{await cCust(tx,cust());})]},
 {id:'N2',assertion:'nullability required: Customer.name explicit null',
  a:[()=>db(tx=>tx.unsafe(`INSERT INTO sales.customers (id,code,name,"createdAt") VALUES (900001,'T900001',NULL,now())`)),()=>db(tx=>tx.unsafe(custSql(',email',',NULL')))],
  ce:[()=>engine([{type:'Customer',json:`{"id":900001,"code":"T900001","name":null,"createdAt":"2026-09-25T10:00:00Z"}`}]),()=>engine([{type:'Customer',json:cust(',"email":null')}])],
  cd:[()=>db(async tx=>{await cCust(tx,`{"id":900001,"code":"T900001","name":null,"createdAt":"2026-09-25T10:00:00Z"}`);}),()=>db(async tx=>{await cCust(tx,cust(',"email":null'));})]},
 {id:'L1',assertion:'length max 100 Unicode scalars: Customer.name 101 (control: 100 incl. combining marks)',
  a:[()=>db(tx=>tx.unsafe(`INSERT INTO sales.customers (id,code,name,"createdAt") VALUES (900001,'T900001',repeat('x',101),now())`)),()=>db(tx=>tx.unsafe(`INSERT INTO sales.customers (id,code,name,"createdAt") VALUES (900001,'T900001',repeat('e'||chr(769),50),now())`))],
  ce:[()=>engine([{type:'Customer',json:cust().replace('Test customer','x'.repeat(101))}]),()=>engine([{type:'Customer',json:cust().replace('Test customer','é'.repeat(50))}])],
  cd:[()=>db(async tx=>{await cCust(tx,cust().replace('Test customer','x'.repeat(101)));}),()=>db(async tx=>{await cCust(tx,cust().replace('Test customer','é'.repeat(50)));})]},
 {id:'L2',assertion:'length on array items: Customer.tags item max 30 (31 chars)',
  a:[()=>db(tx=>tx.unsafe(custSql(',payload',`,'{"tags":["${'t'.repeat(31)}"]}'`))),()=>db(tx=>tx.unsafe(custSql(',payload',`,'{"tags":["ok","ok"]}'`)))],
  ce:[()=>engine([{type:'Customer',json:cust(`,"tags":["${'t'.repeat(31)}"]`)}]),()=>engine([{type:'Customer',json:cust(',"tags":["ok","ok"]')}])],
  cd:[()=>db(async tx=>{await cCust(tx,cust(`,"tags":["${'t'.repeat(31)}"]`));}),()=>db(async tx=>{await cCust(tx,cust(',"tags":["ok","ok"]'));})]},
 {id:'P1',assertion:'decimal precision 14: Order.total 1000000000000.00 (13 integer digits)',
  a:[()=>db(tx=>tx.unsafe(ordSql('1000000000000.00'))),()=>db(async tx=>{await tx.unsafe(ordSql('999999999999.99'));await tx.unsafe(lineSql({lt:'10.00'}));})],
  ce:[()=>engine([{type:'Order',json:ord().replace('10.00','1000000000000.00')},{type:'OrderLine',json:line()}]),()=>engine([{type:'Order',json:ord().replace('10.00','999999999999.99')},{type:'OrderLine',json:line()}])],
  cd:[()=>db(async tx=>{await cOrder(tx,ord().replace('10.00','1000000000000.00'));}),()=>db(async tx=>{await cOrder(tx,ord().replace('10.00','999999999999.99'));})]},
 {id:'P2',assertion:'decimal scale 2, no implicit rounding: Order.total 10.005',
  a:[()=>db(async tx=>{await tx.unsafe(ordSql('10.005'));await tx.unsafe(lineSql());const r=await tx`SELECT total::text t FROM sales.orders WHERE id=900001`;throw Object.assign(new Error(`(accepted; stored as ${r[0].t})`),{code:'SILENT'});}),()=>db(async tx=>{await tx.unsafe(ordSql('10.00'));await tx.unsafe(lineSql());})],
  ce:[()=>engine([{type:'Order',json:ord().replace('10.00','10.005')},{type:'OrderLine',json:line()}]),()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line()}])],
  cd:[()=>db(async tx=>{await cOrder(tx,ord().replace('10.00','10.005'));}),()=>db(async tx=>{await cOrder(tx,ord());})]},
 {id:'W1',assertion:'integer width 16-bit signed: OrderLine.lineNo 32768',
  a:[()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(lineSql({lineNo:'32768'}));}),()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(lineSql({lineNo:'32767'}));})],
  ce:[()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line().replace('"lineNo":1','"lineNo":32768')}]),()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line().replace('"lineNo":1','"lineNo":32767')}])],
  cd:[()=>db(async tx=>{const o=await cOrder(tx,ord(),true,false);const l=await cInsertRaw(tx,'OrderLine',propsText(enc('OrderLine',line().replace('"lineNo":1','"lineNo":32768')).props));await edge(tx,'order-lines',o,'Order',l,'OrderLine');await edge(tx,'line-product',l,'OrderLine',await objId(tx,'Product','1'),'Product');}),
      ()=>db(async tx=>{const o=await cOrder(tx,ord(),true,false);const l=await cInsertRaw(tx,'OrderLine',propsText(enc('OrderLine',line().replace('"lineNo":1','"lineNo":32767')).props));await edge(tx,'order-lines',o,'Order',l,'OrderLine');await edge(tx,'line-product',l,'OrderLine',await objId(tx,'Product','1'),'Product');})]},
 {id:'W2',assertion:'integer width 64-bit signed: Customer.id 9223372036854775808',
  a:[()=>db(tx=>tx.unsafe(custSql('','').replace('900001,','9223372036854775808,'))),()=>db(tx=>tx.unsafe(custSql('','').replace('900001,','9223372036854775807,')))],
  ce:[()=>engine([{type:'Customer',json:cust().replace('900001,','9223372036854775808,')}]),()=>engine([{type:'Customer',json:cust().replace('900001,','9223372036854775807,')}])],
  cd:[()=>db(async tx=>{await cCust(tx,cust().replace('900001,','9223372036854775808,'));}),()=>db(async tx=>{await cCust(tx,cust().replace('900001,','9223372036854775807,'));})]},
 {id:'S1',assertion:'scalar family: Order.status (string) given the number 42',
  a:[()=>db(async tx=>{await tx.unsafe(ordSql('10.00','1','42'));await tx.unsafe(lineSql());const r=await tx`SELECT status FROM sales.orders WHERE id=900001`;throw Object.assign(new Error(`(accepted; stored as text '${r[0].status}')`),{code:'SILENT'});}),()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(lineSql());})],
  ce:[()=>engine([{type:'Order',json:ord().replace('"paid"','42')},{type:'OrderLine',json:line()}]),()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line()}])],
  cd:[()=>db(async tx=>{await cOrder(tx,ord().replace('"paid"','42'));}),()=>db(async tx=>{await cOrder(tx,ord());})]},
 {id:'K1',assertion:'primary key Customer.identity: duplicate id 1',
  a:[()=>db(tx=>tx.unsafe(custSql('','').replace('900001,','1,'))),()=>db(tx=>tx.unsafe(custSql('','')))],
  ce:[()=>engine([{type:'Customer',json:cust().replace('900001,','1,')}]),()=>engine([{type:'Customer',json:cust()}])],
  cd:[()=>db(async tx=>{await cCust(tx,cust().replace('900001,','1,'));}),()=>db(async tx=>{await cCust(tx,cust());})]},
 {id:'K2',assertion:'alternate key Customer.account-code: duplicate code C0000001 (control: c0000001)',
  a:[()=>db(tx=>tx.unsafe(custSql('','').replace("'T900001'","'C0000001'"))),()=>db(tx=>tx.unsafe(custSql('','').replace("'T900001'","'c0000001'")))],
  ce:[()=>engine([{type:'Customer',json:cust().replace('T900001','C0000001')}]),()=>engine([{type:'Customer',json:cust().replace('T900001','c0000001')}])],
  cd:[()=>db(async tx=>{await cCust(tx,cust().replace('T900001','C0000001'));}),()=>db(async tx=>{await cCust(tx,cust().replace('T900001','c0000001'));})]},
 {id:'R1',assertion:'relationship endpoint: Order.customer must reference an existing Customer (violating: a Product / missing key)',
  a:[()=>db(async tx=>{await tx.unsafe(ordSql('10.00','999999999'));await tx.unsafe(lineSql());}),()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(lineSql());})],
  ce:[()=>engine([{type:'Order',json:ord('','999999999')},{type:'OrderLine',json:line()}]),()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line()}])],
  cd:[()=>db(async tx=>{const o=await cOrder(tx,ord(),false,true);await edge(tx,'order-customer',o,'Order',await objId(tx,'Product','1'),'Product');}),()=>db(async tx=>{await cOrder(tx,ord());})]},
 {id:'R2',assertion:'multiplicity Order.customer max 1: second customer for one order',
  a:[()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(lineSql());await tx.unsafe(`INSERT INTO sales.orders (id,"placedAt",status,total,"customerId","customerId") VALUES (1,now(),'x',1,1,2)`);}),()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(lineSql());})],
  ce:[()=>engine([{type:'Order',json:ord().replace('"customer":1','"customer":[1,2]')}]),()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line()}])],
  cd:[()=>db(async tx=>{const o=await cOrder(tx,ord());await edge(tx,'order-customer',o,'Order',await objId(tx,'Customer','2'),'Customer');}),()=>db(async tx=>{await cOrder(tx,ord());})]},
 {id:'R3',assertion:'multiplicity Order.customer min 1: order without customer',
  a:[()=>db(async tx=>{await tx.unsafe(`INSERT INTO sales.orders (id,"placedAt",status,total) VALUES (900001,now(),'paid',10.00)`);await tx.unsafe(lineSql());}),()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(lineSql());})],
  ce:[()=>engine([{type:'Order',json:`{"id":900001,"placedAt":"2026-09-25T10:00:00Z","status":"paid","total":10.00}`},{type:'OrderLine',json:line()}]),()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line()}])],
  cd:[()=>db(async tx=>{await cOrder(tx,ord(),false,true);}),()=>db(async tx=>{await cOrder(tx,ord());})]},
 {id:'R4',assertion:'multiplicity Order.lines min 1: order without any OrderLine',
  a:[()=>db(async tx=>{await tx.unsafe(ordSql());}),()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(lineSql());})],
  ce:[()=>engine([{type:'Order',json:ord()}]),()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line()}])],
  cd:[()=>db(async tx=>{await cOrder(tx,ord(),true,false);}),()=>db(async tx=>{await cOrder(tx,ord());})]},
 {id:'R5',assertion:'multiplicity OrderLine<-Order max 1 (a line in two orders)',
  a:[()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(lineSql());await tx.unsafe(`UPDATE sales.order_lines SET "orderId" = ARRAY[900001,1] WHERE id=900001`);}),()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(lineSql());})],
  ce:[()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line().replace('"order":900001','"order":[900001,1]')}]),()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line()}])],
  cd:[()=>db(async tx=>{const o=await cOrder(tx,ord());const l=(await tx.unsafe(`SELECT target_id FROM c.edge WHERE source_id=${o} AND rel_type_id=${rel('order-lines')}`))[0].target_id;await edge(tx,'order-lines',await objId(tx,'Order','1'),'Order',l,'OrderLine');}),()=>db(async tx=>{await cOrder(tx,ord());})]},
 {id:'R6',assertion:'multiplicity OrderLine.product min 1: line without product',
  a:[()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(`INSERT INTO sales.order_lines (id,"lineNo",quantity,"unitPrice","lineTotal","orderId") VALUES (900001,1,2,5.00,10.00,900001)`);}),()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(lineSql());})],
  ce:[()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line().replace(',"product":1','')}]),()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line()}])],
  cd:[()=>db(async tx=>{const o=await cOrder(tx,ord(),true,false);const l=await cInsertRaw(tx,'OrderLine',propsText(enc('OrderLine',line()).props));await edge(tx,'order-lines',o,'Order',l,'OrderLine');}),()=>db(async tx=>{await cOrder(tx,ord());})]},
 {id:'I1',assertion:'record invariant OrderLine.line-total: lineTotal = quantity * unitPrice (violating 2 x 5.00 = 11.00)',
  a:[()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(lineSql({lt:'11.00'}));}),()=>db(async tx=>{await tx.unsafe(ordSql());await tx.unsafe(lineSql());})],
  ce:[()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line().replace('"lineTotal":10.00','"lineTotal":11.00')}]),()=>engine([{type:'Order',json:ord()},{type:'OrderLine',json:line()}])],
  cd:[()=>db(async tx=>{const o=await cOrder(tx,ord(),true,false);const l=await cInsertRaw(tx,'OrderLine',propsText(enc('OrderLine',line().replace('"lineTotal":10.00','"lineTotal":11.00')).props));await edge(tx,'order-lines',o,'Order',l,'OrderLine');await edge(tx,'line-product',l,'OrderLine',await objId(tx,'Product','1'),'Product');}),()=>db(async tx=>{await cOrder(tx,ord());})]},
 {id:'U1',assertion:'undeclared data: Customer with unknown field legacyScore (C-db: undeclared id "99" inside props)',
  a:[()=>db(tx=>tx.unsafe(custSql(',"legacyScore"',',7'))),()=>db(tx=>tx.unsafe(custSql('','')))],
  ce:[()=>engine([{type:'Customer',json:cust(',"legacyScore":7')}]),()=>engine([{type:'Customer',json:cust()}])],
  cd:[()=>db(async tx=>{const e=enc('Customer',cust());e.props['99']={kind:'number',value:'7'};await cInsertRaw(tx,'Customer',propsText(e.props));}),()=>db(async tx=>{await cInsertRaw(tx,'Customer',propsText(enc('Customer',cust()).props),'{"legacyScore":7}');})]},
];
const layerOf=(opt:string,r:{ok:boolean;msg:string})=>r.ok?'-':r.msg.startsWith('ENGINE')?'engine':r.msg.startsWith('SILENT')?'none (silent change)':r.msg.includes('column "customerId" specified more than once')||r.msg.includes('bigint')&&r.msg.includes('ARRAY')||r.msg.includes('cannot be cast')||r.msg.includes('is of type bigint but expression is of type')?'structural (not expressible)':'database';
const matrix:string[]=[];
for(const c of cases){
  log(`\n[${c.id}] ${c.assertion}`);
  const row=[c.id];
  for(const [label,pair] of [['A',c.a],['C-engine',c.ce],['C-db',c.cd]] as const){
    const v=await pair[0](),k=await pair[1]();
    log(`  ${label.padEnd(8)} violating: ${v.ok?'ACCEPTED':'rejected'} | ${v.msg}`);
    log(`  ${label.padEnd(8)} control:   ${k.ok?'accepted':'REJECTED'} | ${k.msg}`);
    row.push(v.ok?(v.msg.includes('retained=')?'retained (by design)':k.ok?'none':'none?'):(k.ok?layerOf(label,v):'INVALID (control rejected)'));
  }
  matrix.push(row.join(' | '));
}
log('\n== matrix (violating write rejected by; "none" = violating write accepted; every control write accepted unless marked)');
log('id | A | C-engine | C-db');for(const m of matrix)log(m);

// ---- concurrency caveat: two transactions each delete one of an order's two lines ----
log('\n== concurrency: order with 2 lines; T1 and T2 each delete a different line; both fire deferred checks before either commits (READ COMMITTED)');
async function race(label:string,setup:(tx:any)=>Promise<[string,string,string]>,del:(tx:any,id:string,parent:string)=>Promise<void>,count:(parent:string)=>Promise<number>){
  let ids:[string,string,string]=['','',''];await sql.begin(async(tx:any)=>{ids=await setup(tx);});
  const [parent,l1,l2]=ids;const s1=await sql.reserve(),s2=await sql.reserve();
  const res:string[]=[];
  try{
    await s1`BEGIN`;await s2`BEGIN`;
    await del(s1,l1,parent);
    const p2=(async()=>{try{await del(s2,l2,parent);await s2`SET CONSTRAINTS ALL IMMEDIATE`;return 'T2 checks passed';}catch(e:any){return 'T2 '+errText(e);}})();
    await Bun.sleep(300);
    try{await s1`SET CONSTRAINTS ALL IMMEDIATE`;res.push('T1 checks passed');await s1`COMMIT`;res.push('T1 committed');}catch(e:any){res.push('T1 '+errText(e));await s1`ROLLBACK`;}
    res.push(await p2);try{await s2`COMMIT`;res.push('T2 commit issued');}catch(e:any){res.push('T2 '+errText(e));}
  }finally{s1.release();s2.release();}
  log(`  ${label}: ${res.join(' -> ')} -> lines left for order: ${await count(parent)}`);
}
async function cleanupRace(){
  await sql.unsafe(`DELETE FROM sales.order_lines WHERE "orderId"=900100; DELETE FROM sales.orders WHERE id=900100`);
  const os=await sql.unsafe(`SELECT id FROM c.object WHERE (type_id=${T('Order')} AND (props->>'12')::bigint>=900000) OR (type_id=${T('OrderLine')} AND (props->>'17')::bigint>=900000)`);
  if(!os.length)return;
  await sql.unsafe(`ALTER TABLE c.edge DISABLE TRIGGER edge_min_multiplicity`);
  for(const r of os){const ls=await sql.unsafe(`SELECT target_id FROM c.edge WHERE source_id=${r.id} AND rel_type_id=${rel('order-lines')}`);
    await sql.unsafe(`DELETE FROM c.edge WHERE source_id=${r.id} OR target_id=${r.id}`);
    for(const l of ls)await sql.unsafe(`DELETE FROM c.edge WHERE source_id=${l.target_id} OR target_id=${l.target_id}; DELETE FROM c.object WHERE id=${l.target_id}`);
    await sql.unsafe(`DELETE FROM c.object WHERE id=${r.id}`);}
  await sql.unsafe(`ALTER TABLE c.edge ENABLE TRIGGER edge_min_multiplicity`);
}
await cleanupRace();
await race('A (HAND-12 deferred trigger)',async tx=>{await tx.unsafe(`INSERT INTO sales.orders (id,"placedAt",status,total,"customerId") VALUES (900100,now(),'paid',20.00,1)`);await tx.unsafe(`INSERT INTO sales.order_lines VALUES (900101,1,2,5.00,10.00,900100,1),(900102,2,2,5.00,10.00,900100,1)`);return ['900100','900101','900102'];},
  async(tx,id)=>{await tx.unsafe(`DELETE FROM sales.order_lines WHERE id=${id}`);},async p=>(await sql.unsafe(`SELECT count(*)::int n FROM sales.order_lines WHERE "orderId"=${p}`))[0].n);
const cSetup=async(tx:any):Promise<[string,string,string]>=>{const e=enc('Order',ord().replace('900001','900100'));const o=await cInsertRaw(tx,'Order',propsText(e.props));await edge(tx,'order-customer',o,'Order',await objId(tx,'Customer','1'),'Customer');
  const l1=await cInsertRaw(tx,'OrderLine',propsText(enc('OrderLine',line('','900101')).props));await edge(tx,'order-lines',o,'Order',l1,'OrderLine');await edge(tx,'line-product',l1,'OrderLine',await objId(tx,'Product','1'),'Product');const l2=await cInsertRaw(tx,'OrderLine',propsText(enc('OrderLine',line('','900102')).props));await edge(tx,'order-lines',o,'Order',l2,'OrderLine');await edge(tx,'line-product',l2,'OrderLine',await objId(tx,'Product','1'),'Product');
  const [a,b]=(await tx.unsafe(`SELECT target_id FROM c.edge WHERE source_id=${o} AND rel_type_id=${rel('order-lines')} ORDER BY 1`));return [String(o),String(a.target_id),String(b.target_id)];};
const cCount=async(p:string)=>(await sql.unsafe(`SELECT count(*)::int n FROM c.edge WHERE source_id=${p} AND rel_type_id=${rel('order-lines')}`))[0].n;
const cDel=async(tx:any,id:string)=>{await tx.unsafe(`DELETE FROM c.edge WHERE target_id=${id} OR source_id=${id}`);await tx.unsafe(`DELETE FROM c.object WHERE id=${id}`);};
await cleanupRace();
await race('C-db (generic deferred trigger)',cSetup,cDel,cCount);
await cleanupRace();
await race('C-engine (locks parent FOR NO KEY UPDATE, then counts)',cSetup,async(tx,id,parent)=>{await tx.unsafe(`SELECT id FROM c.object WHERE id=${parent} FOR NO KEY UPDATE`);await cDel(tx,id);
  const n=(await tx.unsafe(`SELECT count(*)::int n FROM c.edge WHERE source_id=${parent} AND rel_type_id=${rel('order-lines')}`))[0].n;if(n<1)throw Object.assign(new Error(`ENGINE rel:order-lines:target-min (order ${parent} would have ${n} lines)`),{code:'ENGINE'});},cCount);
await cleanupRace();
writeFileSync(join(spike,`out/20_enforcement_pg${process.env.PGVER??'17'}.txt`),out.join('\n')+'\n');
await sql.close();
