// Engine-side validation cost in Bun: encode + validate N author-shaped records (Product and OrderLine) against the
// rev0 catalog; no database. Usage: bun harness/engine_cost.ts -> out/23_engine_cost.txt
import {readFileSync,writeFileSync} from 'node:fs';
import {join,dirname} from 'node:path';
import {parseExact} from '../loader/exact-json';
import {catalogFromUmf} from '../loader/catalog';
import {encodeRecord,validateEncoded,propsText} from '../loader/engine';
const spike=join(dirname(new URL(import.meta.url).pathname),'..');
const cat=catalogFromUmf(JSON.parse(readFileSync(join(spike,'model/sales.rev0.umf.json'),'utf8')),0);
const lines=[`Bun ${Bun.version}`];
for(const [type,rec] of [['Product','{"id":123,"sku":"SKU-1","name":"write cost probe","price":12.34}'],['OrderLine','{"id":1,"lineNo":1,"quantity":6,"unitPrice":435.71,"lineTotal":2614.26,"order":1,"product":13}'],['Customer','{"id":3,"code":"C0000003","name":"beldant","email":"u3@example.com","createdAt":"2025-04-13T05:04:17.102415+00:00","tags":["promo","new","vip"],"address":{"street":"810 St","city":"mimizov","postalCode":"39931","country":"JP"}}']] as const){
  const N=200000;let v=0;const t0=performance.now();
  for(let i=0;i<N;i++){const e=encodeRecord(cat,type,parseExact(rec));v+=validateEncoded(cat,e).length;propsText(e.props);}
  const ms=performance.now()-t0;lines.push(`${type}: ${N} parse+encode+validate+render in ${ms.toFixed(0)} ms = ${(ms*1000/N).toFixed(2)} us/record (${Math.round(N/ms*1000)} records/s, violations=${v})`);
}
writeFileSync(join(spike,'out/23_engine_cost.txt'),lines.join('\n')+'\n');console.log(lines.join('\n'));
