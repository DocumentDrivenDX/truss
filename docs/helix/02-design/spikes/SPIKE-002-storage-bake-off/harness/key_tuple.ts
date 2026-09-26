// Option C alternative: UMF canonical key tuples (umf-key-tuple-v1) in a bytea key table instead of partial
// expression indexes. 1) verify the local encoder against UMF's normative vectors and UMF's own encoder on the sales
// model; 2) build c.object_key(type_id, key_id, key_bytes, object_id) for every keyed object; 3) cross-check against
// bytes computed in SQL; 4) sizes. Usage: bun harness/key_tuple.ts -> out/24_key_tuple_pg$PGVER.txt
import {SQL} from 'bun';
import {readFileSync,writeFileSync} from 'node:fs';
import {join,dirname} from 'node:path';
import {encodeKeyTuple,hex,type KeyValue} from '../loader/key-tuple';
import {loadCatalog} from '../loader/engine';
const spike=join(dirname(new URL(import.meta.url).pathname),'..');
const UMF=process.env.UMF_DIR!;const umf=await import(join(UMF,'src/index.ts'));
const out:string[]=[];const log=(s:string)=>{out.push(s);console.log(s);};
const fx=JSON.parse(readFileSync(join(UMF,'fixtures/key/tuple-encoding-v1.json'),'utf8'));
let ok=0,bad=0;
for(const v of fx.vectors){const vals:KeyValue[]=v.values.map((x:any,i:number)=>'decimalToken' in x?{decimalToken:x.decimalToken,scale:v.fields[i].scale}:x);
  const h=hex(encodeKeyTuple(vals));if(h===v.expectedHex)ok++;else{bad++;log(`vector ${v.id}: got ${h} expected ${v.expectedHex}`);}}
let refused=0;for(const r of fx.refusals??[]){try{encodeKeyTuple(r.values.map((x:any,i:number)=>'decimalToken' in x?{decimalToken:x.decimalToken,scale:r.fields[i].scale}:x));}catch{refused++;}}
log(`normative vectors: ${ok} match, ${bad} differ; refusals: ${refused}/${(fx.refusals??[]).length} refused by the local encoder (UMF's encoder also checks facets/domains the local one does not)`);
const doc=JSON.parse(readFileSync(join(spike,'model/sales.rev0.umf.json'),'utf8'));
for(const [key,vals] of [['identity',[{integerToken:'9223372036854775807'}]],['identity',[{integerToken:'-42'}]],['account-code',[{string:'C0000001'}]],['account-code',[{string:'é'}]]] as const){
  const u=umf.encodeCoreKeyTuple(doc,{module:'sales',element:'Customer',key},vals as any).bytesHex;const l=hex(encodeKeyTuple(vals as any));
  log(`Customer.${key} ${JSON.stringify(vals)}: UMF ${u} local ${l} ${u===l?'equal':'DIFFERENT'}`);}
const sql=new SQL({path:`${process.env.PGHOST??'/tmp'}/.s.PGSQL.${process.env.PGPORT}`,username:'postgres',database:process.env.PGDATABASE??'bakeoff',max:1});
log(`== ${(await sql`SELECT version() v`)[0].v}`);
const cat=await loadCatalog(sql);
await sql.unsafe(`DROP TABLE IF EXISTS c.object_key; CREATE TABLE c.object_key (type_id int NOT NULL, key_id text NOT NULL, key_bytes bytea NOT NULL, object_id bigint NOT NULL REFERENCES c.object ON DELETE CASCADE, PRIMARY KEY (type_id, key_id, key_bytes))`);
const t0=performance.now();let n=0;const rows:string[]=[];
for(const k of cat.keys){const p=cat.props.find(p=>p.prop_id===k.prop_ids[0])!;
  const objs=await sql.unsafe(`SELECT id::text AS id, props->>'${p.prop_id}' AS v FROM c.object WHERE type_id = ${k.type_id}`);
  for(const o of objs){const val:KeyValue=p.scalar_type==='integer'?{integerToken:o.v}:{string:o.v};rows.push(`${k.type_id}\t${k.key_id}\t\\\\x${hex(encodeKeyTuple([val]))}\t${o.id}`);n++;}}
const enc=performance.now()-t0;
const tsv=join(process.env.WORK!,'object_key.tsv');await Bun.write(tsv,rows.join('\n')+'\n');
const p=Bun.spawnSync(['psql','-X','-q','-c',`\\copy c.object_key FROM '${tsv}'`]);if(p.exitCode)throw new Error(p.stderr.toString());
log(`encoded ${n} key tuples (read + encode in TS) in ${enc.toFixed(0)} ms; loaded with COPY`);
// SQL-side recomputation for single-component integer/string keys: 'UMFK1' 01 tag len payload (payloads < 128 bytes)
const mism=(await sql.unsafe(`SELECT count(*)::int n FROM c.object_key k JOIN c.object o ON o.id = k.object_id JOIN c.key_def d ON d.type_id = k.type_id AND d.key_id = k.key_id JOIN c.prop_def p ON p.prop_id = d.prop_ids[1]
  WHERE k.key_bytes <> convert_to('UMFK1','UTF8') || '\\x01'::bytea || CASE p.scalar_type WHEN 'integer' THEN '\\x02'::bytea ELSE '\\x04'::bytea END
        || decode(lpad(to_hex(octet_length(convert_to(o.props->>(p.prop_id::text),'UTF8'))),2,'0'),'hex') || convert_to(o.props->>(p.prop_id::text),'UTF8')`))[0].n;
log(`cross-check TS bytes vs SQL recomputation: ${mism} mismatches`);
await sql.unsafe(`ANALYZE c.object_key`);
for(const r of await sql.unsafe(`SELECT 'c.object_key heap+pk' AS what, round(pg_total_relation_size('c.object_key')/1048576.0,1) AS mb UNION ALL SELECT 'expression key indexes (obj_key_*)', round(sum(pg_relation_size(indexrelid))/1048576.0,1) FROM pg_stat_user_indexes WHERE indexrelname LIKE 'obj_key_%'`))log(`size: ${r.what} = ${r.mb} MB`);
const dup=await sql.unsafe(`INSERT INTO c.object_key SELECT type_id, key_id, key_bytes, object_id FROM c.object_key WHERE type_id = 1 AND key_id = 'account-code' LIMIT 1`).catch((e:any)=>e.message);
log(`duplicate account-code tuple insert: ${typeof dup==='string'?dup:'accepted?!'}`);
writeFileSync(join(spike,`out/24_key_tuple_pg${process.env.PGVER??'17'}.txt`),out.join('\n')+'\n');await sql.close();
