// SPIKE-002 option A bulk-load prep: dataset JSONL -> CSV matching the UMF-generated tables (hand-written, per type).
// Usage: bun harness/load_a.ts <datadir>   (writes <datadir>/a_*.csv)
import {readFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
import {parseExact,render,type NJ} from '../loader/exact-json';
const data=process.argv[2]!;
const csv=(v:NJ|undefined)=>v===undefined||v.kind==='null'?'':v.kind==='string'?'"'+v.value.replace(/"/g,'""')+'"':v.kind==='number'?v.value:'"'+render(v).replace(/"/g,'""')+'"';
const conv=(file:string,out:string,cols:string[],payload:string[]=[],bytea:string[]=[])=>{
  const rows:string[]=[];
  for(const line of readFileSync(join(data,file),'utf8').split('\n')){if(!line)continue;const r=(parseExact(line) as any).members as Record<string,NJ>;
    const cells=cols.map(c=>bytea.includes(c)&&r[c]?.kind==='string'?'\\x'+Buffer.from((r[c] as any).value,'base64').toString('hex'):csv(r[c]));
    if(payload.length){const m:Record<string,NJ>={};for(const p of payload)if(r[p]!==undefined)m[p]=r[p]!;cells.push(Object.keys(m).length?csv({kind:'object',members:m}):'');}
    rows.push(cells.join(','));}
  writeFileSync(join(data,out),rows.join('\n')+'\n');return rows.length;};
console.log(JSON.stringify({
  customers:conv('customers.jsonl','a_customers.csv',['id','code','name','email','createdAt'],['tags','attributes','address']),
  products:conv('products.jsonl','a_products.csv',['id','sku','name','price','image'],[],['image']),
  orders:conv('orders.jsonl','a_orders.csv',['id','placedAt','status','channel','total','customer']),
  lines:conv('lines.jsonl','a_lines.csv',['id','lineNo','quantity','unitPrice','lineTotal','order','product'])}));
