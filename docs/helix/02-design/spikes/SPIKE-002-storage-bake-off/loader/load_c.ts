// SPIKE-002 option C bulk loader: UMF model -> catalog rows + generated DDL; dataset JSONL -> validated objects/edges
// CSV for COPY. Usage: bun loader/load_c.ts <datadir> <outdir-for-generated-sql>
// Writes <datadir>/c_object.csv, <datadir>/c_edge.csv and <sqlout>/{c_catalog_rev0,c_indexes,c_checks}.sql
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {join,dirname} from 'node:path';
import {createHash} from 'node:crypto';
import {parseExact,render,type NJ} from './exact-json';
import {catalogFromUmf,catalogSql,indexDdl,checkDdl,INVARIANTS} from './catalog';
import {encodeRecord,validateEncoded,propsText,type Encoded} from './engine';
const here=dirname(new URL(import.meta.url).pathname),spike=join(here,'..');
const [data,sqlOut]=[process.argv[2]!,process.argv[3]!];mkdirSync(sqlOut,{recursive:true});
const docText=readFileSync(join(spike,'model/sales.rev0.umf.json'),'utf8');const doc=JSON.parse(docText);
const binding=JSON.parse(readFileSync(join(spike,'model/sales.binding.json'),'utf8'));
const UMF=process.env.UMF_DIR;
if(UMF){const umf=await import(join(UMF,'src/index.ts'));const v=umf.validateDocument(doc);if(!v.valid)throw new Error('UMF validation failed');console.log('UMF validateDocument(rev0): valid');}
const cat=catalogFromUmf(doc,0);
const sha=createHash('sha256').update(docText).digest('hex');
writeFileSync(join(sqlOut,'c_catalog_rev0.sql'),`INSERT INTO c.schema_rev VALUES (0,'0.7.0','${sha}',${"'"+docText.replace(/'/g,"''")+"'"});\n`+catalogSql(cat));
writeFileSync(join(sqlOut,'c_indexes.sql'),indexDdl(cat,binding).join('\n')+'\n');
const checks=checkDdl(cat,INVARIANTS.sql);
writeFileSync(join(sqlOut,'c_checks.sql'),checks.map(c=>`ALTER TABLE c.object ADD CONSTRAINT ${c.name} CHECK (${c.sql}); -- rule ${c.rule}`).join('\n')+'\n');
writeFileSync(join(sqlOut,'c_checks_drop.sql'),checks.map(c=>`ALTER TABLE c.object DROP CONSTRAINT IF EXISTS ${c.name};`).join('\n')+'\n');
console.log(`catalog: ${cat.types.length} types, ${cat.props.length} props, ${cat.keys.length} keys, ${cat.rels.length} relationships; ${checks.length} CHECK constraints; ${indexDdl(cat,binding).length} indexes`);

const csv=(v:string|number|bigint|null)=>v===null?'':typeof v==='string'?'"'+v.replace(/"/g,'""')+'"':String(v);
const objects:string[]=[],edges:string[]=[];let nextId=1n;const byKey=new Map<string,bigint>();
let violations=0,validateMs=0,encodeMs=0;
function add(e:Encoded,businessKey?:string):bigint{
  const id=nextId++;objects.push([id,e.typeId,csv(propsText(e.props)),csv(e.retained?propsText(e.retained):null),0].join(','));
  if(businessKey)byKey.set(businessKey,id);
  for(const ch of e.children){const cid=add(ch.child);edges.push([nextId++,ch.relId,id,e.typeId,cid,ch.child.typeId,''].join(','));}
  return id;
}
function load(file:string,type:string){
  const t=cat.types.find(t=>t.element===type)!;let n=0;
  for(const line of readFileSync(join(data,file),'utf8').split('\n')){if(!line)continue;
    const t0=performance.now();const rec=parseExact(line);const e=encodeRecord(cat,type,rec);const t1=performance.now();
    const v=validateEncoded(cat,e);const t2=performance.now();encodeMs+=t1-t0;validateMs+=t2-t1;if(v.length){violations++;continue;}
    const key=(rec as any).members.id.value;const id=add(e,`${t.type_id}:${key}`);
    for(const r of e.refs){const tgt=byKey.get(`${r.targetType}:${render(r.key)}`);if(tgt===undefined)throw new Error('dangling ref');
      if(r.dir==='out')edges.push([nextId++,r.relId,id,t.type_id,tgt,r.targetType,''].join(','));
      else edges.push([nextId++,r.relId,tgt,r.targetType,id,t.type_id,''].join(','));}
    n++;}
  return n;
}
const counts={Customer:load('customers.jsonl','Customer'),Product:load('products.jsonl','Product'),Order:load('orders.jsonl','Order'),OrderLine:load('lines.jsonl','OrderLine')};
writeFileSync(join(data,'c_object.csv'),objects.join('\n')+'\n');writeFileSync(join(data,'c_edge.csv'),edges.join('\n')+'\n');
writeFileSync(join(data,'c_nextid.txt'),String(nextId));
const total=Object.values(counts).reduce((a,b)=>a+b,0);
console.log(JSON.stringify({records:counts,objects:objects.length,edges:edges.length,engineViolations:violations,
  encodeMs:Math.round(encodeMs),validateMs:Math.round(validateMs),validatePerSec:Math.round(total/(validateMs/1000))}));
