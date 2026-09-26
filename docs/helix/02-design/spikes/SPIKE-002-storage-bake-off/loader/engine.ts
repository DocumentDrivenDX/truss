// SPIKE-002 option C engine (throwaway): encode author-shaped records into props maps keyed by property-definition
// id, validate them against the catalog, and write objects/edges/journal rows. DB access via Bun.sql (adapter layer).
import {type NJ,render} from './exact-json';
import {type Catalog,type Violation,validateProps,INVARIANTS} from './catalog';

export class EngineViolation extends Error{constructor(public violations:Violation[]){super('engine rejected write: '+violations.map(v=>`${v.rule} (${v.path}: ${v.message})`).join('; '));}}
export interface Encoded {typeId:number;props:Record<string,NJ>;retained:Record<string,NJ>|null;children:{relId:number;child:Encoded}[];refs:{relId:number;dir:'out'|'in';targetType:number;keyPropId:number;key:NJ}[]}

/** Author-shaped record (field names, relationship names, nested records) -> props map + retained + children + refs. */
export function encodeRecord(c:Catalog,typeElement:string,rec:NJ):Encoded{
  if(rec.kind!=='object')throw new Error('record must be an object');
  const t=c.types.find(t=>t.element===typeElement)!;
  const props:Record<string,NJ>={},retained:Record<string,NJ>={},children:Encoded['children']=[],refs:Encoded['refs']=[];
  for(const [name,v] of Object.entries(rec.members)){
    const p=c.props.find(p=>p.type_id===t.type_id&&p.name===name);
    if(p){props[String(p.prop_id)]=v;continue;}
    const inv=c.rels.find(r=>!r.composition&&r.inverse===name&&r.endpoints.some(([,tt])=>tt===t.type_id));
    if(inv){const [st]=inv.endpoints.find(([,tt])=>tt===t.type_id)!;const k=c.keys.find(k=>k.type_id===st&&k.is_primary)!;for(const kv of v.kind==='array'?v.items:[v])refs.push({relId:inv.rel_type_id,dir:'in',targetType:st,keyPropId:k.prop_ids[0]!,key:kv});continue;}
    const r=c.rels.find(r=>r.name===name&&r.endpoints.some(([s])=>s===t.type_id));
    if(r&&r.composition){if(v.kind==='object'){const [,tt]=r.endpoints[0]!;children.push({relId:r.rel_type_id,child:encodeRecord(c,c.types.find(x=>x.type_id===tt)!.element,v)});continue;}if(v.kind==='null')continue;}
    if(r&&!r.composition){const [,tt]=r.endpoints.find(([s])=>s===t.type_id)!;const k=c.keys.find(k=>k.type_id===tt&&k.key_id===r.target_key)!;for(const kv of v.kind==='array'?v.items:[v])refs.push({relId:r.rel_type_id,dir:'out',targetType:tt,keyPropId:k.prop_ids[0]!,key:kv});continue;}
    retained[name]=v;   // matches no definition: kept, never dropped
  }
  return {typeId:t.type_id,props,retained:Object.keys(retained).length?retained:null,children,refs};
}
export function validateEncoded(c:Catalog,e:Encoded):Violation[]{
  return [...validateProps(c,e.typeId,e.props,INVARIANTS.js),...e.children.flatMap(ch=>validateEncoded(c,ch.child))];
}
export const propsText=(p:Record<string,NJ>)=>render({kind:'object',members:p});

export async function loadCatalog(sql:any):Promise<Catalog>{
  const types=await sql`SELECT type_id,module,element,kind FROM c.type_def ORDER BY type_id`;
  const props=await sql`SELECT prop_id,type_id,element,name,scalar_type,nullability,cardinality,facets::text AS facets,item::text AS item,since_rev FROM c.prop_def ORDER BY prop_id`;
  const keys=await sql`SELECT type_id,key_id,prop_ids,is_primary FROM c.key_def`;
  const rels=await sql`SELECT * FROM c.rel_def ORDER BY rel_type_id`;const eps=await sql`SELECT * FROM c.rel_endpoint`;
  const rev=(await sql`SELECT coalesce(max(rev),0) AS r FROM c.schema_rev`)[0].r;
  return {rev,types:[...types],props:props.map((p:any)=>({...p,facets:p.facets?JSON.parse(p.facets):null,item:p.item?JSON.parse(p.item):null})),
    keys:keys.map((k:any)=>({...k,prop_ids:[...k.prop_ids].map(Number)})),
    rels:rels.map((r:any)=>({...r,endpoints:eps.filter((e:any)=>e.rel_type_id===r.rel_type_id).map((e:any)=>[e.source_type,e.target_type])}))};
}

/** Engine write path: validate (optional), then insert the object tree and its edges in the caller's transaction. */
export async function insertEncoded(tx:any,c:Catalog,e:Encoded,opts:{validate:boolean;journal:boolean;origin?:string}):Promise<bigint>{
  if(opts.validate){const v=validateEncoded(c,e);if(v.length)throw new EngineViolation(v);}
  const [{id}]=await tx`INSERT INTO c.object (type_id,props,retained,rev) VALUES (${e.typeId},${propsText(e.props)}::text::jsonb,${e.retained?propsText(e.retained):null}::text::jsonb,${c.rev}) RETURNING id`;
  if(opts.journal)await tx`INSERT INTO c.journal (object_id,op,new_value,rev,origin) VALUES (${id},'create',${propsText(e.props)}::text::jsonb,${c.rev},${opts.origin??'engine'})`;
  for(const ch of e.children){const cid=await insertEncoded(tx,c,ch.child,opts);
    await tx`INSERT INTO c.edge (rel_type_id,source_id,source_type,target_id,target_type) VALUES (${ch.relId},${id},${e.typeId},${cid},${ch.child.typeId})`;}
  for(const r of e.refs){
    const rows=await tx.unsafe(`SELECT id FROM c.object WHERE type_id = $1 AND (props->>'${r.keyPropId}')::bigint = $2`,[r.targetType,render(r.key)]);
    if(!rows.length)throw new EngineViolation([{rule:`rel:${r.relId}:endpoint`,path:String(r.relId),message:`no ${c.types.find(t=>t.type_id===r.targetType)!.element} with key ${render(r.key)}`}]);
    if(r.dir==='out')await tx`INSERT INTO c.edge (rel_type_id,source_id,source_type,target_id,target_type) VALUES (${r.relId},${id},${e.typeId},${rows[0].id},${r.targetType})`;
    else await tx`INSERT INTO c.edge (rel_type_id,source_id,source_type,target_id,target_type) VALUES (${r.relId},${rows[0].id},${r.targetType},${id},${e.typeId})`;
  }
  return BigInt(id);
}
