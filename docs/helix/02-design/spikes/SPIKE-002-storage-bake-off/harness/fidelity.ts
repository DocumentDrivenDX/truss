// SPIKE-002 Method 4 / Question 3: round-trip a fixed value corpus through both options with Bun.sql and compare
// exact JSON renderings of what was written and what came back. Two read paths per option: the client's default
// decoding, and the careful path (A: columns cast to text; C: props::text parsed with UMF's parseNativeJson).
// Writes run in one transaction that is rolled back. Usage: bun harness/fidelity.ts -> out/21_fidelity_pg$PGVER.txt
import {SQL} from 'bun';
import {writeFileSync} from 'node:fs';
import {join,dirname} from 'node:path';
import {parseExact,render,type NJ} from '../loader/exact-json';
import {encodeRecord,insertEncoded,loadCatalog,validateEncoded} from '../loader/engine';
const spike=join(dirname(new URL(import.meta.url).pathname),'..');
const {parseNativeJson,renderTree}=await import(join(process.env.UMF_DIR!,'src/model/native-json.ts'));
const sql=new SQL({path:`${process.env.PGHOST??'/tmp'}/.s.PGSQL.${process.env.PGPORT}`,username:'postgres',database:process.env.PGDATABASE??'bakeoff',max:2});
const out:string[]=[];const log=(s:string)=>{out.push(s);console.log(s);};
log(`== ${(await sql`SELECT version() v`)[0].v}; Bun ${Bun.version}; UMF parseNativeJson for exact reads`);
const cat=await loadCatalog(sql);
class Rollback extends Error{}
// Corpus: author-shaped records with exact tokens. Binary is base64 in the author form.
const customers=[
 `{"id":9223372036854775807,"code":"FID-MAX","name":"é vs é 👍🏽","email":null,"createdAt":"2026-09-25T10:00:00.123456+02:00","tags":["a","a","b"],"attributes":{"z":"1","a":"2","":"empty key","ключ":"v"},"legacyScore":12345678901234567890.5,"legacyNested":{"x":[1,null,1.50]}}`,
 `{"id":-9223372036854775808,"code":"FID-MIN","name":"é","createdAt":"2026-09-25T10:00:00","tags":[],"attributes":{}}`,
 `{"id":9007199254740993,"code":"FID-2P53","name":"combining é","email":"x@example.com","createdAt":"2026-09-25T08:00:00Z","address":{"street":"1 Main St","city":"Zürich","country":"CH"}}`,
];
const products=[
 `{"id":900101,"sku":"FID-P1","name":"trailing zero","price":10.10,"image":"AP8AEA=="}`,
 `{"id":900102,"sku":"FID-P2","name":"short scale","price":10.1}`,
 `{"id":900103,"sku":"FID-P3","name":"max","price":9999999999.99}`,
 `{"id":900104,"sku":"FID-P4","name":"zero","price":0.00}`,
];
const J=(s:string)=>parseExact(s) as {kind:'object';members:Record<string,NJ>};
const diffs:string[]=[];
function compare(opt:string,path:string,input:Record<string,NJ>,got:Record<string,NJ|undefined>){
  for(const k of new Set([...Object.keys(input),...Object.keys(got)])){
    const a=input[k],b=got[k];const ra=a===undefined?'<absent>':render(a),rb=b===undefined?'<absent>':render(b);
    if(ra!==rb)diffs.push(`${opt.padEnd(14)} ${path}.${k}: wrote ${ra} -> read ${rb}`);
  }
}
const nj=(v:any):NJ|undefined=>v===null?{kind:'null'}:v===undefined?undefined:typeof v==='string'?{kind:'string',value:v}:typeof v==='number'||typeof v==='bigint'?{kind:'number',value:String(v)}:typeof v==='boolean'?{kind:'boolean',value:v}:v instanceof Date?{kind:'string',value:v.toISOString()}:v instanceof Uint8Array?{kind:'string',value:Buffer.from(v).toString('base64')}:parseExact(JSON.stringify(v));
const fromNative=(t:any):NJ=>parseExact(renderTree(t));

// ---------- option A ----------
try{await sql.begin(async(tx:any)=>{
  for(const c of customers){const r=J(c).members;const payload:Record<string,NJ>={};for(const k of ['tags','attributes','address'])if(r[k])payload[k]=r[k]!;
    // unknown fields have no column; the only place they could go is the embedded payload (hand decision, not generated)
    for(const k of Object.keys(r))if(!['id','code','name','email','createdAt','tags','attributes','address'].includes(k))payload[k]=r[k]!;
    await tx.unsafe(`INSERT INTO sales.customers (id,code,name,email,"createdAt",payload) VALUES ($1::text::bigint,$2,$3,$4,$5::text::timestamptz,$6::text::jsonb)`,
      [render(r.id!),(r.code as any).value,(r.name as any).value,r.email?.kind==='string'?r.email.value:null,(r.createdAt as any).value,Object.keys(payload).length?render({kind:'object',members:payload}):null]);}
  for(const p of products){const r=J(p).members;
    await tx.unsafe(`INSERT INTO sales.products (id,sku,name,price,image) VALUES ($1::text::bigint,$2,$3,$4::text::numeric,decode($5,'base64'))`,[render(r.id!),(r.sku as any).value,(r.name as any).value,render(r.price!),r.image?(r.image as any).value:null]);}
  for(const c of customers){const r=J(c).members;const key=render(r.id!);
    const d=(await tx.unsafe(`SELECT id,code,name,email,"createdAt",payload FROM sales.customers WHERE id = $1::text::bigint`,[key]))[0];
    const t=(await tx.unsafe(`SELECT id::text,code,name,email,"createdAt"::text AS "createdAt",payload::text AS payload FROM sales.customers WHERE id = $1::text::bigint`,[key]))[0];
    for(const [label,row,exact] of [['A default',d,false],['A text',t,true]] as const){
      const got:Record<string,NJ|undefined>={id:exact?{kind:'number',value:row.id}:nj(row.id),code:nj(row.code),name:nj(row.name),createdAt:nj(row.createdAt)};
      if(row.email!==null)got.email=nj(row.email);
      const pl=row.payload===null?{}:exact?(parseExact(row.payload) as any).members:(nj(row.payload) as any).members;Object.assign(got,pl);
      compare(label,`Customer[${key}]`,r,got);}
  }
  for(const p of products){const r=J(p).members;const key=render(r.id!);
    const d=(await tx.unsafe(`SELECT id,sku,name,price,image FROM sales.products WHERE id = $1::text::bigint`,[key]))[0];
    const t=(await tx.unsafe(`SELECT id::text,sku,name,price::text,encode(image,'base64') AS image FROM sales.products WHERE id = $1::text::bigint`,[key]))[0];
    for(const [label,row] of [['A default',d],['A text',t]] as const){
      const got:Record<string,NJ|undefined>={id:{kind:'number',value:String(row.id)},sku:nj(row.sku),name:nj(row.name),price:typeof row.price==='string'?{kind:'number',value:row.price}:nj(row.price)};
      if(row.image!==null)got.image=nj(row.image);compare(label,`Product[${key}]`,r,got);}
  }
  throw new Rollback();});}catch(e){if(!(e instanceof Rollback))throw e;}

// ---------- option C ----------
try{await sql.begin(async(tx:any)=>{
  const ids:{type:string;rec:string;id:bigint}[]=[];
  for(const [type,recs] of [['Customer',customers],['Product',products]] as const)for(const rec of recs){
    const e=encodeRecord(cat,type,parseExact(rec));const v=validateEncoded(cat,e);if(v.length)log(`C engine rejected ${type}: ${JSON.stringify(v)}`);
    ids.push({type,rec,id:await insertEncoded(tx,cat,e,{validate:true,journal:false})});}
  const back=(type:string,props:Record<string,NJ>,retained:Record<string,NJ>|null,children:Record<string,NJ>)=>{
    const t=cat.types.find(t=>t.element===type)!;const o:Record<string,NJ>={};
    for(const [k,v] of Object.entries(props)){const p=cat.props.find(p=>String(p.prop_id)===k)!;o[p.name]=v;}
    return {...o,...(retained??{}),...children};};
  for(const {type,rec,id} of ids){
    const r=J(rec).members;
    const d=(await tx.unsafe(`SELECT props, retained FROM c.object WHERE id = ${id}`))[0];
    const t=(await tx.unsafe(`SELECT props::text AS props, retained::text AS retained FROM c.object WHERE id = ${id}`))[0];
    const kids=await tx.unsafe(`SELECT r.name, o.props::text AS props FROM c.edge e JOIN c.rel_def r USING (rel_type_id) JOIN c.object o ON o.id = e.target_id WHERE e.source_id = ${id} AND r.composition`);
    const childExact:Record<string,NJ>={};for(const k of kids){const cp=fromNative(parseNativeJson(k.props)) as any;const ct=cat.rels.find(r=>r.name===k.name)!.endpoints[0]![1];childExact[k.name]={kind:'object',members:back(cat.types.find(x=>x.type_id===ct)!.element,cp.members,null,{})};}
    // default decoding: Bun.sql hands jsonb to JSON.parse
    const dp=(nj(d.props) as any).members,dr=d.retained?(nj(d.retained) as any).members:null;
    compare('C default',`${type}[${render(r.id!)}]`,r,back(type,dp,dr,childExact));
    const tp=(fromNative(parseNativeJson(t.props)) as any).members,tr=t.retained?(fromNative(parseNativeJson(t.retained)) as any).members:null;
    compare('C text+UMF',`${type}[${render(r.id!)}]`,r,back(type,tp,tr,childExact));
  }
  throw new Rollback();});}catch(e){if(!(e instanceof Rollback))throw e;}

// ---------- U+0000 ----------
for(const [label,fn] of [
  ['A varchar',async(tx:any)=>tx.unsafe(`INSERT INTO sales.customers (id,code,name,"createdAt") VALUES (900201,'NUL',$1,now())`,['a\u0000b'])],
  ['A jsonb payload',async(tx:any)=>tx.unsafe(`INSERT INTO sales.customers (id,code,name,"createdAt",payload) VALUES (900201,'NUL','n',now(),$1::text::jsonb)`,['{"tags":["a\\u0000b"]}'])],
  ['C jsonb props (raw SQL)',async(tx:any)=>tx.unsafe(`INSERT INTO c.object (type_id,props,rev) VALUES (1,$1::text::jsonb,0)`,['{"3":"a\\u0000b"}'])],
] as const){try{await sql.begin(async(tx:any)=>{await fn(tx);throw new Rollback();});diffs.push(`${label}: U+0000 accepted`);}catch(e:any){if(e instanceof Rollback)diffs.push(`${label}: U+0000 accepted (then rolled back)`);else diffs.push(`${label.padEnd(14)} U+0000: rejected with error: ${e.message}`);}}
{const e=encodeRecord(cat,'Customer',parseExact(`{"id":900201,"code":"NUL","name":"a\\u0000b","createdAt":"2026-09-25T10:00:00Z"}`));diffs.push(`C engine       U+0000: ${JSON.stringify(validateEncoded(cat,e))}`);}
log('\n== differences between written and read values (anything not listed round-tripped exactly)');
for(const d of diffs)log(d);
log(`\n== corpus: ${customers.length} customers, ${products.length} products; read paths: A default, A text, C default (JSON.parse), C text+UMF parseNativeJson`);
writeFileSync(join(spike,`out/21_fidelity_pg${process.env.PGVER??'17'}.txt`),out.join('\n')+'\n');
await sql.close();
