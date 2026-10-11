/** Native text/int64 descriptor guard for the experimental query consumer.
 * Current source custody, view dependencies and concurrent DDL remain host duties.
 * Value nullability is checked separately by source completeness, including views. */
const refuse=():never=>{throw Error('TRUSS_SECURITY_QUERY_CARRIER_UNSUPPORTED');};
function name(value:unknown):string {
 if(typeof value!=='string'||!value||value.includes('\0')||new TextEncoder().encode(value).length>63||[...value].some(c=>{const n=c.codePointAt(0)!;return n>=0xd800&&n<=0xdfff;}))return refuse();
 return value;
}
const identifier=(value:unknown)=>'"'+name(value).replaceAll('"','""')+'"';
const literal=(value:string)=>"E'"+value.replaceAll('\\','\\\\').replaceAll("'","\\'")+"'::pg_catalog.text";
export function lowerSecurityQueryCarrierDomains(input:{schema:string;table:string;fields:readonly {column:string;family:'string'|'integer'}[]}):string {
 const carrier=structuredClone(input);
 if(!Array.isArray(carrier.fields)||carrier.fields.length<1||carrier.fields.length>128||new Set(carrier.fields.map(f=>name(f.column))).size!==carrier.fields.length)return refuse();
 const relation=literal(identifier(carrier.schema)+'.'+identifier(carrier.table));
 const fields=carrier.fields.map(field=>{
  if(!['string','integer'].includes(field.family))return refuse();
  const type=field.family==='string'?'pg_catalog.text':'pg_catalog.int8';
  return '(a.attname::pg_catalog.text OPERATOR(pg_catalog.=) '+literal(name(field.column))+' AND a.atttypid OPERATOR(pg_catalog.=) '+literal(type)+'::pg_catalog.regtype)';
 }).join(' OR ');
 return '(SELECT pg_catalog.count(*) FROM pg_catalog.pg_attribute AS a WHERE a.attrelid OPERATOR(pg_catalog.=) pg_catalog.to_regclass('+relation+') AND a.attnum OPERATOR(pg_catalog.>) 0 AND NOT a.attisdropped AND ('+fields+')) OPERATOR(pg_catalog.=) '+carrier.fields.length+'::pg_catalog.int8';
}
