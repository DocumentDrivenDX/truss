// SPIKE-002 Method 5: the six query shapes. Option A is hand-written per type (what a team or runtime must produce);
// option C is ONE generic template per shape, instantiated from catalog ids derived from the UMF model.
// `bun harness/queries.ts` writes sql/queries_a.sql, sql/queries_c.sql and out/40_query_code.txt (line counts).
import {readFileSync,writeFileSync} from 'node:fs';
import {join,dirname} from 'node:path';
import {catalogFromUmf,valueExpr,type Catalog} from '../loader/catalog';
const here=dirname(new URL(import.meta.url).pathname),spike=join(here,'..');

// ---------- option A: per-type SQL (params :k key, :lo range start, :s status) ----------
export const A:Record<string,string>={
  q1_fetch:`SELECT * FROM sales.customers WHERE id = :k;`,
  q2_hop1:`SELECT * FROM sales.order_lines WHERE "orderId" = :k;`,
  q3_hop2:`SELECT l.* FROM sales.orders o
  JOIN sales.order_lines l ON l."orderId" = o.id
  WHERE o."customerId" = :k;`,
  q4_hop3:`SELECT p.* FROM sales.orders o
  JOIN sales.order_lines l ON l."orderId" = o.id
  JOIN sales.products p ON p.id = l."productId"
  WHERE o."customerId" = :k;`,
  q5_range:`SELECT * FROM sales.orders WHERE total BETWEEN :lo AND :lo + 10;`,
  q6_update:`UPDATE sales.orders SET status = :s WHERE id = :k;`,
};

// ---------- option C: generic templates ----------
type Step={rel:string;dir:'out'|'in'};
const prop=(c:Catalog,el:string)=>c.props.find(p=>p.element===el)!;
const typeOf=(c:Catalog,el:string)=>c.types.find(t=>t.element===el)!.type_id;
const relId=(c:Catalog,id:string)=>c.rels.find(r=>r.rel_id===id)!.rel_type_id;
const keyExpr=(c:Catalog,type:string,alias:string)=>{const t=typeOf(c,type);const k=c.keys.find(k=>k.type_id===t&&k.is_primary)!;return valueExpr(c.props.find(p=>p.prop_id===k.prop_ids[0])!,alias);};
/** Fetch by primary key. */
export function cFetch(c:Catalog,type:string){return `SELECT id, props::text, retained::text FROM c.object o
  WHERE o.type_id = ${typeOf(c,type)} AND ${keyExpr(c,type,'o')} = :k;`;}
/** Traverse n hops from a keyed start object; edge-to-edge joins, objects fetched only at the end. */
export function cPath(c:Catalog,start:string,steps:Step[]){
  const lines=[`SELECT x.id, x.props::text FROM c.object s`];let prev='s.id';
  steps.forEach((st,i)=>{const e=`e${i}`;const r=relId(c,st.rel);
    lines.push(st.dir==='out'?`  JOIN c.edge ${e} ON ${e}.source_id = ${prev} AND ${e}.rel_type_id = ${r}`:`  JOIN c.edge ${e} ON ${e}.target_id = ${prev} AND ${e}.rel_type_id = ${r}`);
    prev=st.dir==='out'?`${e}.target_id`:`${e}.source_id`;});
  lines.push(`  JOIN c.object x ON x.id = ${prev}`,`  WHERE s.type_id = ${typeOf(c,start)} AND ${keyExpr(c,start,'s')} = :k;`);
  return lines.join('\n');}
/** Range filter on an indexed property (index declared in the binding, expression from the catalog). */
export function cRange(c:Catalog,field:string){const p=prop(c,field);return `SELECT id, props::text FROM c.object
  WHERE type_id = ${p.type_id} AND ${valueExpr(p)} BETWEEN :lo AND :lo + 10;`;}
/** Single-property update (atomic jsonb_set) with the per-property journal row. */
export function cUpdate(c:Catalog,field:string,journal=true){const p=prop(c,field);const t=c.types.find(t=>t.type_id===p.type_id)!.element;
  const set=`jsonb_set(o.props, '{${p.prop_id}}', to_jsonb(:s::text))`,where=`o.type_id = ${p.type_id} AND ${keyExpr(c,t,'o')} = :k`;
  if(!journal)return `UPDATE c.object o SET props = ${set} WHERE ${where};`;
  return `WITH old AS (SELECT o.id, o.props->'${p.prop_id}' AS v FROM c.object o WHERE ${where} FOR NO KEY UPDATE),
  upd AS (UPDATE c.object o SET props = ${set} FROM old WHERE o.id = old.id RETURNING o.id)
INSERT INTO c.journal (object_id, prop_id, op, old_value, new_value, rev, origin)
  SELECT old.id, ${p.prop_id}, 'set', old.v, to_jsonb(:s::text), 0, 'bench' FROM old JOIN upd USING (id);`;}
export function C(c:Catalog):Record<string,string>{return {
  q1_fetch:cFetch(c,'Customer'),
  q2_hop1:cPath(c,'Order',[{rel:'order-lines',dir:'out'}]),
  q3_hop2:cPath(c,'Customer',[{rel:'order-customer',dir:'in'},{rel:'order-lines',dir:'out'}]),
  q4_hop3:cPath(c,'Customer',[{rel:'order-customer',dir:'in'},{rel:'order-lines',dir:'out'},{rel:'line-product',dir:'out'}]),
  q5_range:cRange(c,'Order.total'),
  q6_update:cUpdate(c,'Order.status'),
  q6_update_nojournal:cUpdate(c,'Order.status',false),
};}
export const catalog=()=>catalogFromUmf(JSON.parse(readFileSync(join(spike,'model/sales.rev0.umf.json'),'utf8')),0);

if(import.meta.main){
  const c=catalog(),cq=C(c);
  writeFileSync(join(spike,'sql/queries_a.sql'),Object.entries(A).map(([k,v])=>`-- ${k} (per type, hand-written)\n${v}`).join('\n\n')+'\n');
  writeFileSync(join(spike,'sql/queries_c.sql'),Object.entries(cq).map(([k,v])=>`-- ${k} (instantiated from generic template)\n${v}`).join('\n\n')+'\n');
  const src=readFileSync(new URL(import.meta.url).pathname,'utf8');
  const fnLines=(name:string)=>{const i=src.indexOf(`export function ${name}(`);const j=src.indexOf('\n',src.indexOf(';}',i));return src.slice(i,j).split('\n').length;};
  const rows=[['shape','A lines (SQL)','C lines (instantiated SQL)','C generic template','template lines (TS)']];
  const tmpl:Record<string,string>={q1_fetch:'cFetch',q2_hop1:'cPath',q3_hop2:'cPath',q4_hop3:'cPath',q5_range:'cRange',q6_update:'cUpdate'};
  for(const k of Object.keys(A))rows.push([k,String(A[k]!.split('\n').length),String(cq[k]!.split('\n').length),tmpl[k]!,String(fnLines(tmpl[k]!))]);
  const txt=rows.map(r=>r.join('\t')).join('\n')+`\nC shared helpers (prop/typeOf/relId/keyExpr + catalog.valueExpr): ${src.slice(src.indexOf('type Step'),src.indexOf('/** Fetch by primary key')).split('\n').length-1} lines\n`;
  writeFileSync(join(spike,'out/40_query_code.txt'),txt);console.log(txt);
}
