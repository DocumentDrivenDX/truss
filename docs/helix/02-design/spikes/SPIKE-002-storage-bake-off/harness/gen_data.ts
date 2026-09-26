// SPIKE-002 Method 1: seeded synthetic sales dataset with skewed fan-out, written as exact JSON lines
// (one source for both options). Usage: bun harness/gen_data.ts <outdir> [scale=1]
// scale=1 -> 20,000 customers, 5,000 products, 100,000 orders, ~400,000 order lines.
import {mkdirSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
const out=process.argv[2]!;const scale=Number(process.argv[3]??'1');mkdirSync(out,{recursive:true});
let seed=0x5eed2002;const rnd=()=>{seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};
const pick=<T>(xs:T[])=>xs[Math.floor(rnd()*xs.length)]!;
const NC=20000*scale,NP=5000*scale,NO=100000*scale;
const syll=['ka','lo','mi','ren','sa','to','vu','xe','zo','bel','cor','dan','él','jó','ño','ü'];
const word=(n:number)=>{let s='';while([...s].length<n)s+=pick(syll);return [...s].slice(0,n).join('');};
const cents=(c:bigint)=>{const neg=c<0n;const a=neg?-c:c;return (neg?'-':'')+(a/100n).toString()+'.'+(a%100n).toString().padStart(2,'0');};
const ts=(ms:number,off:number)=>{const d=new Date(ms+off*60000);const iso=d.toISOString().replace('Z','');const us=String(Math.floor(rnd()*1000)).padStart(3,'0');const sign=off>=0?'+':'-';const ao=Math.abs(off);return `${iso}${us}${sign}${String(Math.floor(ao/60)).padStart(2,'0')}:${String(ao%60).padStart(2,'0')}`;};
const w=(f:string)=>{const lines:string[]=[];return {push:(o:string)=>lines.push(o),close:()=>writeFileSync(join(out,f),lines.join('\n')+'\n')};};

const cu=w('customers.jsonl');let longNames=0;
for(let id=1;id<=NC;id++){
  const long=rnd()<0.005;if(long)longNames++;
  const name=long?word(61+Math.floor(rnd()*40)):word(5+Math.floor(rnd()*36));
  const o:any={id,code:'C'+String(id).padStart(7,'0'),name};
  if(rnd()<0.8)o.email=`u${id}@example.com`;
  o.createdAt=ts(1.6e12+Math.floor(rnd()*1.5e11),pick([0,60,120,-300,330]));
  if(rnd()<0.6)o.tags=Array.from({length:1+Math.floor(rnd()*3)},()=>pick(['vip','b2b','new','eu','us','promo']));
  if(rnd()<0.4)o.attributes={segment:pick(['retail','smb','ent']),source:pick(['ads','ref','organic'])};
  if(rnd()<0.8)o.address={street:`${1+Math.floor(rnd()*999)} ${word(8)} St`,city:word(7),...(rnd()<0.9?{postalCode:String(10000+Math.floor(rnd()*89999))}:{}),country:pick(['US','DE','FR','JP','BR'])};
  cu.push(JSON.stringify(o));
}
cu.close();
// Exact decimal tokens must survive JSON.stringify: write them as placeholders and splice them in as numbers.
const num=(s:string)=>`@@${s}@@`;const fix=(s:string)=>s.replace(/"@@(-?[0-9.]+)@@"/g,'$1');
const pr=w('products.jsonl');const price:bigint[]=[0n];
for(let id=1;id<=NP;id++){const p=BigInt(100+Math.floor(rnd()*99900));price.push(p);
  const o:any={id,sku:'SKU-'+String(id).padStart(6,'0'),name:word(10+Math.floor(rnd()*30)),price:num(cents(p))};
  if(rnd()<0.1)o.image=Buffer.from(Array.from({length:16},()=>Math.floor(rnd()*256))).toString('base64');
  pr.push(fix(JSON.stringify(o)));}
pr.close();
const or=w('orders.jsonl'),li=w('lines.jsonl');const perCustomer=new Array(NC+1).fill(0);let lineId=0;
for(let id=1;id<=NO;id++){
  const customer=1+Math.floor(NC*rnd()**2);perCustomer[customer]++;          // skew: customer 1 is the heaviest
  const n=1+Math.floor(rnd()*7);let total=0n;
  for(let k=1;k<=n;k++){const product=1+Math.floor(NP*rnd()**2);const q=1+Math.floor(rnd()*10);const lt=price[product]!*BigInt(q);total+=lt;
    li.push(fix(JSON.stringify({id:++lineId,lineNo:k,quantity:q,unitPrice:num(cents(price[product]!)),lineTotal:num(cents(lt)),order:id,product})));}
  const o:any={id,placedAt:ts(1.7e12+Math.floor(rnd()*5e10),pick([0,60,-240,540])),status:pick(['placed','paid','shipped','delivered','cancelled']),total:num(cents(total)),customer};
  if(rnd()<0.7)o.channel=pick(['web','store','phone']);
  or.push(fix(JSON.stringify(o)));
}
or.close();li.close();
const counts=perCustomer.slice(1).sort((a,b)=>a-b);const pct=(p:number)=>counts[Math.min(counts.length-1,Math.floor(p*counts.length))];
const summary={seed:'0x5eed2002',scale,customers:NC,products:NP,orders:NO,lines:lineId,longNamesOver60:longNames,
  ordersPerCustomer:{min:counts[0],p50:pct(0.5),p95:pct(0.95),p99:pct(0.99),max:counts.at(-1),customersWithZero:counts.filter(x=>x===0).length}};
writeFileSync(join(out,'summary.json'),JSON.stringify(summary,null,1));console.log(JSON.stringify(summary));
