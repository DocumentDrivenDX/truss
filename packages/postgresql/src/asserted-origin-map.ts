/** Pure candidate mapping; role text is a supplied fact, never native authority. */
import {decodeAcceptanceJson,type AcceptanceJson} from './acceptance-json';
type ExactOriginValue={kind:'null'}|{kind:'boolean';value:boolean}|{kind:'string';text:string}|{kind:'sequence';items:ExactOriginValue[]}|{kind:'map';entries:{key:string;value:ExactOriginValue}[]};
const freeze=<T>(value:T):T=>{if(value!==null&&typeof value==='object'){for(const child of Object.values(value))freeze(child);Object.freeze(value);}return value;};
/** Numeric-free canonical-tree strings remain strings, including decimal-looking
 * text and user-authored kind tags. No interpretation of actor labels occurs. */
export function mapAssertedOrigin(original:Uint8Array,databaseRole:string){
 if(!(original.buffer instanceof ArrayBuffer))throw Error('Original ordinary origin bytes required');
 const bytes=Uint8Array.prototype.slice.call(original) as Uint8Array;
 if(!databaseRole||new TextEncoder().encode(databaseRole).length>1024||databaseRole.includes('\0')||/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(databaseRole))throw Error('Exact scalar database role text required');
 const asserted=decodeAcceptanceJson(bytes);let nodes=0;
 const map=(node:AcceptanceJson):ExactOriginValue=>{
  if(++nodes>32768)throw Error('Origin mapping node capacity exceeded');
  if(node===null)return {kind:'null'};
  if(typeof node==='boolean')return {kind:'boolean',value:node};
  if(typeof node==='string')return {kind:'string',text:node};
  if(Array.isArray(node))return {kind:'sequence',items:node.map(map)};
  const encoder=new TextEncoder();const entries=Object.entries(node).map(([key,value])=>({key,value,bytes:encoder.encode(key)}));
  entries.sort((a,b)=>{for(let i=0;i<Math.min(a.bytes.length,b.bytes.length);i++)if(a.bytes[i]!==b.bytes[i])return a.bytes[i]-b.bytes[i];return a.bytes.length-b.bytes.length;});
  return {kind:'map',entries:entries.map(({key,value})=>({key,value:map(value)}))};
 };
 const journalOrigin={asserted:map(asserted),databaseRole};
 if(new TextEncoder().encode(JSON.stringify(journalOrigin)).length>4194304)throw Error('Origin mapping output capacity exceeded');
 return freeze({origin:{asserted,databaseRole},journalOrigin,originalUtf8Hex:Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join(''),scope:'pure_asserted_origin_mapping_candidate_only' as const});
}
