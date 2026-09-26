// SPIKE-002 option C: turn a validated UMF 0.7.0 document into catalog rows, generic-table DDL (partial expression
// indexes, edge multiplicity indexes, optional conditional CHECK constraints) and an engine-side validator.
// Portable: no I/O and no Bun/Node APIs (the DB adapter lives in engine.ts). Throwaway spike code.
import {type NJ} from './exact-json';

export interface Prop {prop_id:number;type_id:number;element:string;name:string;scalar_type:string|null;nullability:string;cardinality:string;facets:any;item:{scalar:string;facets?:any}|null;since_rev:number}
export interface Type {type_id:number;module:string;element:string;kind:string}
export interface Key {type_id:number;key_id:string;prop_ids:number[];is_primary:boolean}
export interface Rel {rel_type_id:number;module:string;rel_id:string;name:string;source_min:number;source_max:number|null;target_min:number;target_max:number|null;lifecycle:string;directed:boolean;target_key:string|null;composition:boolean;since_rev:number;inverse:string|null;endpoints:[number,number][]}
export interface Catalog {rev:number;types:Type[];props:Prop[];keys:Key[];rels:Rel[]}
export interface Violation {rule:string;path:string;message:string}

const max=(m:any)=>m==='*'?null:m as number;
/** Build catalog rows from the document. `prior` keeps ids stable across revisions (ids are never reused). */
export function catalogFromUmf(doc:any,rev:number,prior?:Catalog):Catalog{
  const mod=doc.modules[0],els=new Map<string,any>(mod.elements.map((e:any)=>[e.id,e]));
  const nextId=(xs:{id:number}[])=>xs.reduce((m,x)=>Math.max(m,x.id),0)+1;
  const types:Type[]=[],props:Prop[]=[],keys:Key[]=[],rels:Rel[]=[];
  const pt=new Map((prior?.types??[]).map(t=>[t.element,t])),pp=new Map((prior?.props??[]).map(p=>[p.element,p])),pr=new Map((prior?.rels??[]).map(r=>[r.rel_id,r]));
  let tNext=nextId((prior?.types??[]).map(t=>({id:t.type_id}))),pNext=nextId((prior?.props??[]).map(p=>({id:p.prop_id}))),rNext=nextId((prior?.rels??[]).map(r=>({id:r.rel_type_id})));
  for(const e of mod.elements)if(e.kind==='record'){const old=pt.get(e.id);types.push({type_id:old?.type_id??tNext++,module:mod.id,element:e.id,kind:'record'});}
  const tid=(el:string)=>types.find(t=>t.element===el)!.type_id;
  for(const e of mod.elements)if(e.kind==='record'){
    for(const m of e.members){
      const f=els.get(m.element);const rt=(f.references??[]).find((r:any)=>r.role==='record-type');
      if(rt){ // record-valued field -> composition relationship to a child object (never nested JSON)
        const old=pr.get(f.id);
        rels.push({rel_type_id:old?.rel_type_id??rNext++,module:mod.id,rel_id:f.id,name:f.id.split('.').pop(),source_min:1,source_max:1,
          target_min:f.nullability==='required'?1:0,target_max:f.cardinality==='one'?1:null,lifecycle:'owned',directed:true,target_key:null,composition:true,inverse:null,
          since_rev:old?.since_rev??rev,endpoints:[[tid(e.id),tid(rt.element)]]});
        continue;
      }
      const it=f.itemType?els.get(f.itemType.element):null;const old=pp.get(f.id);
      props.push({prop_id:old?.prop_id??pNext++,type_id:tid(e.id),element:f.id,name:f.id.split('.').slice(1).join('.'),scalar_type:f.scalarType??null,
        nullability:f.nullability,cardinality:f.cardinality,facets:f.facets??null,item:it?{scalar:it.scalarType,...(it.facets?{facets:it.facets}:{})}:null,since_rev:old?.since_rev??rev});
    }
    for(const k of e.keys??[])keys.push({type_id:tid(e.id),key_id:k.id,prop_ids:k.fields.map((r:any)=>props.find(p=>p.element===r.element)!.prop_id),is_primary:!!k.primary});
  }
  for(const r of mod.relationships??[]){const old=pr.get(r.id);
    rels.push({rel_type_id:old?.rel_type_id??rNext++,module:mod.id,rel_id:r.id,name:r.name,source_min:r.sourceMultiplicity.min,source_max:max(r.sourceMultiplicity.max),
      target_min:r.targetMultiplicity.min,target_max:max(r.targetMultiplicity.max),lifecycle:r.targetLifecycle,directed:r.directed,target_key:r.target[0].key,composition:false,inverse:r.inverse??null,
      since_rev:old?.since_rev??rev,endpoints:r.source.flatMap((s:any)=>r.target.map((t:any)=>[tid(s.element),tid(t.element)] as [number,number]))});}
  return {rev,types,props,keys,rels};
}

const q=(s:string)=>"'"+s.replace(/'/g,"''")+"'";
const js=(v:any)=>v===null||v===undefined?'NULL':q(JSON.stringify(v))+'::jsonb';
/** Idempotent catalog upsert statements for one accepted revision. */
export function catalogSql(c:Catalog):string{
  const out:string[]=[];
  for(const t of c.types)out.push(`INSERT INTO c.type_def VALUES (${t.type_id},${q(t.module)},${q(t.element)},${q(t.kind)}) ON CONFLICT (type_id) DO NOTHING;`);
  for(const p of c.props)out.push(`INSERT INTO c.prop_def (prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets,item,since_rev) VALUES (${p.prop_id},${p.type_id},${q(p.element)},${q(p.name)},${p.scalar_type?q(p.scalar_type):'NULL'},${q(p.nullability)},${q(p.cardinality)},${js(p.facets)},${js(p.item)},${p.since_rev}) ON CONFLICT (prop_id) DO UPDATE SET scalar_type=EXCLUDED.scalar_type,nullability=EXCLUDED.nullability,cardinality=EXCLUDED.cardinality,facets=EXCLUDED.facets,item=EXCLUDED.item;`);
  for(const k of c.keys)out.push(`INSERT INTO c.key_def VALUES (${k.type_id},${q(k.key_id)},ARRAY[${k.prop_ids.join(',')}],${k.is_primary}) ON CONFLICT DO NOTHING;`);
  for(const r of c.rels){
    out.push(`INSERT INTO c.rel_def VALUES (${r.rel_type_id},${q(r.module)},${q(r.rel_id)},${q(r.name)},${r.source_min},${r.source_max??'NULL'},${r.target_min},${r.target_max??'NULL'},${q(r.lifecycle)},${r.directed},${r.target_key?q(r.target_key):'NULL'},${r.composition},${r.since_rev},${r.inverse?q(r.inverse):'NULL'}) ON CONFLICT (rel_type_id) DO UPDATE SET source_min=EXCLUDED.source_min,source_max=EXCLUDED.source_max,target_min=EXCLUDED.target_min,target_max=EXCLUDED.target_max;`);
    for(const [s,t] of r.endpoints)out.push(`INSERT INTO c.rel_endpoint VALUES (${r.rel_type_id},${s},${t}) ON CONFLICT DO NOTHING;`);
  }
  return out.join('\n')+'\n';
}

/** Index expression for a property value; must match the query templates in queries.ts. */
export function valueExpr(p:Prop,alias=''):string{
  const a=alias?alias+'.':'';const raw=`(${a}props->>'${p.prop_id}')`;
  if(p.scalar_type==='integer'){const w=p.facets?.integerWidth;return w&&w.bits<=64&&w.signed?`(${raw}::bigint)`:`(${raw}::numeric)`;}
  if(p.scalar_type==='decimal')return `(${raw}::numeric)`;
  return `(${raw} COLLATE "C")`;
}
export function indexDdl(c:Catalog,binding?:any):string[]{
  const out:string[]=[];
  for(const k of c.keys){const ps=k.prop_ids.map(id=>c.props.find(p=>p.prop_id===id)!);
    out.push(`CREATE UNIQUE INDEX IF NOT EXISTS obj_key_t${k.type_id}_${k.key_id.replace(/\W/g,'_')} ON c.object (${ps.map(p=>valueExpr(p)).join(', ')}) WHERE type_id = ${k.type_id};`);}
  for(const ix of binding?.extensions?.['umf.binding']?.indexes??[]){
    const refs=ix.on.map((o:any)=>o.field).filter(Boolean);
    const ps=refs.map((r:any)=>c.props.find(p=>p.element===`${r.element}.${r.field}`)).filter(Boolean) as Prop[];
    if(ps.length!==refs.length||ix.kind!=='btree')continue; // unique binding indexes duplicate authored keys here
    out.push(`CREATE INDEX IF NOT EXISTS obj_idx_t${ps[0]!.type_id}_${ix.name} ON c.object (${ps.map(p=>valueExpr(p)).join(', ')}) WHERE type_id = ${ps[0]!.type_id};`);
  }
  for(const r of c.rels){
    if(r.target_max===1)out.push(`CREATE UNIQUE INDEX IF NOT EXISTS edge_max_src_r${r.rel_type_id} ON c.edge (source_id) WHERE rel_type_id = ${r.rel_type_id};`);
    if(r.source_max===1)out.push(`CREATE UNIQUE INDEX IF NOT EXISTS edge_max_tgt_r${r.rel_type_id} ON c.edge (target_id) WHERE rel_type_id = ${r.rel_type_id};`);
  }
  return out;
}

// ---- rules: one definition drives both the engine validator and the conditional CHECK constraints ----
const TS_RE='^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\\.[0-9]{1,9})?(Z|[+-][0-9]{2}:[0-9]{2})?$';
const B64_RE='^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$';
const jtype:Record<string,string>={integer:'number',decimal:'number',string:'string',binary:'string',timestamp:'string',boolean:'boolean'};
function scalarCheckSql(scalar:string,facets:any,x:string /* jsonb expr */):string[]{
  const t=`${x}->>0`; // not used
  void t;
  const txt=`(${x} #>> '{}')`;
  const out=[`jsonb_typeof(${x}) = '${jtype[scalar]}'`];
  if(scalar==='integer'){out.push(`scale(${txt}::numeric) = 0`);const w=facets?.integerWidth;if(w){const lo=w.signed?-(2n**BigInt(w.bits-1)):0n,hi=w.signed?2n**BigInt(w.bits-1)-1n:2n**BigInt(w.bits)-1n;out.push(`${txt}::numeric BETWEEN ${lo} AND ${hi}`);}}
  if(scalar==='decimal'&&facets?.precision!==undefined){out.push(`scale(${txt}::numeric) <= ${facets.scale}`,`abs(${txt}::numeric) < 1e${facets.precision-facets.scale}`);}
  if(scalar==='string'&&facets?.length)out.push(`length(${txt}) <= ${facets.length.max}`);
  if(scalar==='binary'){out.push(`${txt} ~ '${B64_RE}'`);if(facets?.length)out.push(`length(decode(${txt}, 'base64')) <= ${facets.length.max}`);}
  if(scalar==='timestamp')out.push(`${txt} ~ '${TS_RE}'`);
  return out;
}
/** Conditional CHECK constraints on the shared objects table, one per (property, rule) so a violation names its rule. */
export function checkDdl(c:Catalog,invariants:{type:string;name:string;sql:(e:(n:string)=>string)=>string}[]=[]):{name:string;rule:string;sql:string}[]{
  const out:{name:string;rule:string;sql:string}[]=[];
  for(const p of c.props){
    const T=p.type_id,x=`(props->'${p.prop_id}')`,present=`jsonb_typeof(${x}) IS NOT NULL AND jsonb_typeof(${x}) <> 'null'`,guard=`type_id <> ${T} OR NOT (${present})`;
    if(p.nullability==='required')out.push({name:`ck_t${T}_p${p.prop_id}_required`,rule:`${p.element}:required`,sql:`type_id <> ${T} OR (${present})`});
    if(p.cardinality==='one'&&p.scalar_type)out.push({name:`ck_t${T}_p${p.prop_id}_value`,rule:`${p.element}:value`,sql:`${guard} OR (${scalarCheckSql(p.scalar_type,p.facets,x).join(' AND ')})`});
    if(p.cardinality==='array'||p.cardinality==='map'){
      const kind=p.cardinality==='array'?'array':'object',sel=p.cardinality==='array'?'$[*]':'$.*';
      let cond=`jsonb_typeof(${x}) = '${kind}'`;
      if(p.item?.scalar==='string'){const len=p.item.facets?.length?.max;cond+=` AND NOT jsonb_path_exists(${x}, '${sel} ? (@.type() != "string"${len!==undefined?` || !(@ like_regex "^.{0,${len}}$" flag "s")`:''})')`;}
      out.push({name:`ck_t${T}_p${p.prop_id}_${p.cardinality}`,rule:`${p.element}:${p.cardinality}`,sql:`${guard} OR (${cond})`});
    }
  }
  for(const t of c.types){const ids=c.props.filter(p=>p.type_id===t.type_id).map(p=>`'${p.prop_id}'`);
    out.push({name:`ck_t${t.type_id}_declared_only`,rule:`${t.element}:declared-properties`,sql:`type_id <> ${t.type_id} OR (props - ARRAY[${ids.join(',')}]::text[]) = '{}'::jsonb`});}
  for(const inv of invariants){const t=c.types.find(x=>x.element===inv.type)!;
    const e=(n:string)=>{const p=c.props.find(pp=>pp.element===`${inv.type}.${n}`)!;return `(props->>'${p.prop_id}')::numeric`;};
    out.push({name:`ck_t${t.type_id}_inv_${inv.name.replace(/\W/g,'_')}`,rule:`${inv.type}:invariant:${inv.name}`,sql:`type_id <> ${t.type_id} OR (${inv.sql(e)})`});}
  return out;
}

// ---- engine-side validation (exact: numbers are source tokens) ----
const INT=/^-?(0|[1-9][0-9]*)$/,DEC=/^-?(0|[1-9][0-9]*)(\.[0-9]+)?$/,TS=new RegExp(TS_RE),B64=new RegExp(B64_RE);
function scalarViolations(scalar:string,facets:any,v:NJ,rule:string,path:string):Violation[]{
  const bad=(message:string)=>[{rule,path,message}];
  if(scalar==='integer'){if(v.kind!=='number'||!INT.test(v.value))return bad('not an integer token');const w=facets?.integerWidth;if(w){const b=BigInt(v.value),lo=w.signed?-(2n**BigInt(w.bits-1)):0n,hi=w.signed?2n**BigInt(w.bits-1)-1n:2n**BigInt(w.bits)-1n;if(b<lo||b>hi)return bad(`outside ${w.signed?'signed':'unsigned'} ${w.bits}-bit range`);}return [];}
  if(scalar==='decimal'){if(v.kind!=='number'||!DEC.test(v.value))return bad('not a plain decimal token');if(facets?.precision!==undefined){const [i,f='']=v.value.replace('-','').split('.');if(f.length>facets.scale)return bad(`scale ${f.length} > ${facets.scale} (no implicit rounding)`);if(i!.replace(/^0+/,'').length>facets.precision-facets.scale)return bad(`precision ${facets.precision} exceeded`);}return [];}
  if(scalar==='string'){if(v.kind!=='string')return bad('not a string');if(v.value.includes('\u0000'))return bad('U+0000 cannot be stored in jsonb text');const n=[...v.value].length;if(facets?.length&&n>facets.length.max)return bad(`length ${n} > ${facets.length.max} Unicode scalars`);return [];}
  if(scalar==='binary'){if(v.kind!=='string'||!B64.test(v.value))return bad('not canonical base64');const n=Math.floor(v.value.length*3/4)-(v.value.endsWith('==')?2:v.value.endsWith('=')?1:0);if(facets?.length&&n>facets.length.max)return bad(`byte length ${n} > ${facets.length.max}`);return [];}
  if(scalar==='timestamp'){if(v.kind!=='string'||!TS.test(v.value))return bad('not an RFC 3339 timestamp');return [];}
  if(scalar==='boolean'){if(v.kind!=='boolean')return bad('not a boolean');return [];}
  return bad('unknown scalar family');
}
export function validateProps(c:Catalog,typeId:number,props:Record<string,NJ>,invariants:{type:string;name:string;js:(get:(n:string)=>string)=>boolean}[]=[]):Violation[]{
  const out:Violation[]=[];
  for(const p of c.props.filter(p=>p.type_id===typeId)){
    const v=props[String(p.prop_id)],present=v!==undefined&&v.kind!=='null';
    if(p.nullability==='required'&&!present){out.push({rule:`${p.element}:required`,path:p.element,message:v===undefined?'absent':'explicit null'});continue;}
    if(!present)continue;
    if(p.cardinality==='one'&&p.scalar_type)out.push(...scalarViolations(p.scalar_type,p.facets,v!,`${p.element}:value`,p.element));
    if(p.cardinality==='array'){if(v!.kind!=='array')out.push({rule:`${p.element}:array`,path:p.element,message:'not an array'});else v!.items.forEach((it,i)=>out.push(...scalarViolations(p.item!.scalar,p.item!.facets,it,`${p.element}:array`,`${p.element}[${i}]`)));}
    if(p.cardinality==='map'){if(v!.kind!=='object')out.push({rule:`${p.element}:map`,path:p.element,message:'not an object'});else for(const [k,it] of Object.entries(v!.members))out.push(...scalarViolations(p.item!.scalar,p.item!.facets,it,`${p.element}:map`,`${p.element}[${JSON.stringify(k)}]`));}
  }
  const t=c.types.find(t=>t.type_id===typeId)!;
  for(const k of Object.keys(props))if(!c.props.some(p=>p.type_id===typeId&&String(p.prop_id)===k))out.push({rule:`${t.element}:declared-properties`,path:k,message:'undeclared property id in props'});
  for(const inv of invariants)if(inv.type===t.element&&!out.length){
    const get=(n:string)=>{const p=c.props.find(pp=>pp.element===`${inv.type}.${n}`)!;const v=props[String(p.prop_id)];return v?.kind==='number'?v.value:'';};
    if(!inv.js(get))out.push({rule:`${inv.type}:invariant:${inv.name}`,path:inv.type,message:'invariant false'});
  }
  return out;
}

// Exact decimal arithmetic for the line-total invariant (engine side): compare a*b with c without floats.
const scaled=(s:string):[bigint,number]=>{const neg=s.startsWith('-');const [i,f='']=s.replace('-','').split('.');return [(neg?-1n:1n)*BigInt(i!+f),f.length];};
export function decMulEq(a:string,b:string,c:string):boolean{const [x,xs]=scaled(a),[y,ys]=scaled(b),[z,zs]=scaled(c);const ps=xs+ys;const s=Math.max(ps,zs);return x*y*10n**BigInt(s-ps)===z*10n**BigInt(s-zs);}
export const INVARIANTS={
  js:[{type:'OrderLine',name:'line-total',js:(g:(n:string)=>string)=>decMulEq(g('quantity'),g('unitPrice'),g('lineTotal'))}],
  sql:[{type:'OrderLine',name:'line-total',sql:(e:(n:string)=>string)=>`${e('lineTotal')} = ${e('quantity')} * ${e('unitPrice')}`}],
};
