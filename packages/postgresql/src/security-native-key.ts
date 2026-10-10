/** Experimental physical-key correspondence. Inputs must be original admitted
 * compiler declarations and original native inventory, independently held at a
 * stable cut. Shape/content equality is not source authentication or admission. */
import type {SecurityPhysicalType} from './security-predicate';
type Ref=SecurityPhysicalType['type'];
export interface SecurityNativeKeyDeclaration {
  target:Ref; keyId:string;
  fields:readonly {ref:Ref; domain:{scalarType:string;nullability:string;cardinality:string;facets:Record<string,unknown>;allowedValues:unknown}}[];
}
export interface SecurityNativeKeyInventory {
  engine:string;
  tables:readonly {
    home:{catalog:string;schema:string;table:string};
    columns:readonly {name:string;type:string;notNull:boolean;deterministic:boolean}[];
    keys:readonly {primary:boolean;validated:boolean;columns:readonly string[]}[];
    /** Original native catalog observations, not labels supplied by a request. */
    typeSources?:readonly {type:Ref;column:string;value:string;sourcePin:{documentId:string;revision:string;umfVersion:string;sha256:string}}[];
  }[];
}
const fail=():never=>{throw Error('TRUSS_SECURITY_NATIVE_KEY_UNSUPPORTED');};
function nonempty(v:unknown):string{if(typeof v!=='string'||!v||v.length>4096||v.includes('\0')||[...v].some(c=>c.codePointAt(0)!>=0xd800&&c.codePointAt(0)!<=0xdfff))return fail();return v;}
function ref(v:Ref):string{if(!v||Object.keys(v).sort().join(',')!=='documentId,elementId,moduleId')return fail();return JSON.stringify([nonempty(v.documentId),nonempty(v.moduleId),nonempty(v.elementId)]);}
const home=(v:{schema:string;table:string})=>JSON.stringify([nonempty(v.schema),nonempty(v.table)]);
/** Required unrefined TEXT logical keys; explicit native int4 type-selector bridge only.
 * A key validates uniqueness under its exact selected type, not endpoint FKs,
 * row eligibility, authenticated subject binding or full graph/business codecs. */
export function securityNativeKeysCorrespond(input:{
  declarations:readonly SecurityNativeKeyDeclaration[];types:readonly (SecurityPhysicalType & {nativePrimaryKeyColumns?:readonly string[]})[];
  catalog:string;modelPins:readonly {documentId:string;revision:string;umfVersion:string;sha256:string}[];
  inventory:SecurityNativeKeyInventory;
}):boolean{
 try{
  nonempty(input.catalog);
  if(input.inventory.engine!=='170009'||!input.types.length||input.types.length>64||!input.declarations.length||input.declarations.length>4096||input.inventory.tables.length>128||!input.modelPins.length||input.modelPins.length>32)return false;
  const pins=new Map(input.modelPins.map(p=>{if(Object.keys(p).sort().join(',')!=='documentId,revision,sha256,umfVersion'||! /^[0-9a-f]{64}$/.test(p.sha256)||p.umfVersion!=='0.8.0')return fail();nonempty(p.revision);return [nonempty(p.documentId),p] as const;}));
  if(pins.size!==input.modelPins.length)return false;
  const types=new Map(input.types.map(t=>[ref(t.type),t]));if(types.size!==input.types.length)return false;
  const tables=new Map(input.inventory.tables.map(t=>[home(t.home),t]));if(tables.size!==input.inventory.tables.length||input.inventory.tables.some(t=>t.home.catalog!==input.catalog))return false;
  const groups=new Map<string,SecurityPhysicalType[]>();
  for(const type of types.values()){const key=home(type.home);groups.set(key,[...(groups.get(key)??[]),type]);}
  for(const group of groups.values())if(group.length>1){
   const first=group[0]!.discriminator??fail();
   if(group.some(t=>!t.discriminator||t.discriminator.column!==first.column||t.discriminator.carrier!==first.carrier)||new Set(group.map(t=>t.discriminator!.value)).size!==group.length)return false;
  }
  const covered=new Set<string>(),declared=new Map<string,string>();
  for(const declaration of input.declarations){
   const target=ref(declaration.target),type=types.get(target)??fail();nonempty(declaration.keyId);
   if(type.keyId!==declaration.keyId||!declaration.fields.length||declaration.fields.length>32||type.keyFields.length!==declaration.fields.length)return false;
   if(!pins.has(declaration.target.documentId)||declaration.fields.some(f=>!pins.has(f.ref.documentId)))return false;
   if(type.fields.length>256||new Set(type.fields.map(f=>ref(f.ref))).size!==type.fields.length||type.keyFields.some(k=>type.fields.find(f=>ref(f.ref)===ref(k.ref))?.column!==k.column))return false;
   const original=declaration.fields.map(f=>ref(f.ref));if(new Set(original).size!==original.length||original.some((value,i)=>value!==ref(type.keyFields[i]!.ref)))return false;
   const columns=type.keyFields.map(f=>nonempty(f.column));if(new Set(columns).size!==columns.length)return false;
   for(const f of declaration.fields){const d=f.domain;if(!d||Object.keys(d).sort().join(',')!=='allowedValues,cardinality,facets,nullability,scalarType'||d.scalarType!=='string'||d.nullability!=='required'||d.cardinality!=='one'||d.allowedValues!==null||!d.facets||typeof d.facets!=='object'||Array.isArray(d.facets)||Object.keys(d.facets).length)return false;}
   const identity=JSON.stringify([target,declaration.keyId]),meaning=JSON.stringify(declaration.fields);
   if(declared.has(identity)&&declared.get(identity)!==meaning)return false;declared.set(identity,meaning);
   const table=tables.get(home(type.home))??fail();if(table.columns.length>256||table.keys.length>64||table.keys.some(k=>typeof k.primary!=='boolean'||typeof k.validated!=='boolean'))return false;
   const native=new Map(table.columns.map(c=>[nonempty(c.name),c]));if(native.size!==table.columns.length)return false;
   for(const column of columns){const c=native.get(column)??fail();if(c.type!=='text'||c.notNull!==true||c.deterministic!==true)return false;}
   let physical=[...columns];
   if(type.discriminator){
    const d=type.discriminator;nonempty(d.column);nonempty(d.value);
    if(d.carrier!=='int4'||! /^(0|-?[1-9][0-9]*)$/.test(d.value)||d.value.length>11||columns.includes(d.column))return false;
    const n=BigInt(d.value);if(n<-(1n<<31n)||n>=(1n<<31n))return false;
    const c=native.get(d.column)??fail();if(c.type!=='integer'||c.notNull!==true)return false;
    const pin=pins.get(type.type.documentId)??fail(),sources=table.typeSources??fail();if(sources.length>64)return false;
    const matches=sources.filter(source=>source.value===d.value||ref(source.type)===target);
    if(matches.length!==1||ref(matches[0]!.type)!==target||matches[0]!.value!==d.value||matches[0]!.column!==d.column)return false;
    const sourcePin=matches[0]!.sourcePin;
    if(!sourcePin||Object.keys(sourcePin).sort().join(',')!=='documentId,revision,sha256,umfVersion'||sourcePin.documentId!==pin.documentId||sourcePin.revision!==pin.revision||sourcePin.umfVersion!==pin.umfVersion||sourcePin.sha256!==pin.sha256)return false;
    physical=[d.column,...physical];
   }else if(groups.get(home(type.home))!.length>1)return false;
   // Preserve the explicitly declared native index order independently from
   // logical key component order. It must contain exactly the same carriers.
   const ordered=type.nativePrimaryKeyColumns??physical;
   if(!Array.isArray(ordered)||ordered.length!==physical.length||new Set(ordered).size!==ordered.length||ordered.some(c=>!physical.includes(nonempty(c))))return false;
   const primary=table.keys.filter(k=>k.primary);
   if(primary.length!==1||primary[0]!.validated!==true||JSON.stringify(primary[0]!.columns)!==JSON.stringify(ordered))return false;
   covered.add(target);
  }
  return covered.size===types.size;
 }catch{return false;}
}
