/** Numeric-free original wire to the existing native canonical-tree codec carrier.
 * This does not admit report shape, semantic provenance, resources or publication. */
import {decodeAcceptanceJson,type AcceptanceJson} from './acceptance-json';
type NativeTree={kind:'null'}|{kind:'boolean';value:boolean}|{kind:'string';utf8Hex:string}|{kind:'array';items:NativeTree[]}|{kind:'object';members:{keyUtf8Hex:string;node:NativeTree}[]};
const hex=(bytes:Uint8Array)=>Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
export function prepareCanonicalWireTree(original:Uint8Array){
 if(!(original.buffer instanceof ArrayBuffer))throw Error('Original ordinary wire byte custody required');
 if(original.length>1048576)throw Error('Canonical wire source capacity exceeded');
 const owned=Uint8Array.prototype.slice.call(original) as Uint8Array;
 const value=decodeAcceptanceJson(owned);let steps=0;
 // Preflight the actual native task count before constructing its tagged carrier.
 const pending:AcceptanceJson[]=[value];
 while(pending.length){const node=pending.pop()!;steps++;
  if(node!==null&&typeof node==='object'){
   const children=Array.isArray(node)?node:Object.values(node);steps+=children.length+1+(Array.isArray(node)?0:2*children.length);
   if(steps>32768)throw Error('Native canonical tree task capacity exceeded');
   for(const child of children)pending.push(child);
  }
  if(steps>32768)throw Error('Native canonical tree task capacity exceeded');
 }
 const root:{node?:NativeTree}={};const tasks:{value:AcceptanceJson;assign:(node:NativeTree)=>void}[]=[{value,assign:node=>{root.node=node}}];
 while(tasks.length){const task=tasks.pop()!,node=task.value;
  if(node===null)task.assign({kind:'null'});
  else if(typeof node==='boolean')task.assign({kind:'boolean',value:node});
  else if(typeof node==='string')task.assign({kind:'string',utf8Hex:hex(new TextEncoder().encode(node))});
  else if(Array.isArray(node)){
   const items:NativeTree[]=new Array(node.length);task.assign({kind:'array',items});
   for(let i=node.length-1;i>=0;i--)tasks.push({value:node[i],assign:child=>{items[i]=child}});
  }else{
   const entries=Object.entries(node),members:{keyUtf8Hex:string;node:NativeTree}[]=new Array(entries.length);task.assign({kind:'object',members});
   for(let i=entries.length-1;i>=0;i--){const [key,child]=entries[i];const keyUtf8Hex=hex(new TextEncoder().encode(key));tasks.push({value:child,assign:encoded=>{members[i]={keyUtf8Hex,node:encoded}}});}
  }
 }
 const nativeTreeText=JSON.stringify(root.node);
 if(nativeTreeText.length>4194304)throw Error('Native canonical tree carrier capacity exceeded');
 return Object.freeze({originalUtf8Hex:hex(owned),nativeTreeText,nativeTaskCount:String(steps),scope:'original_numeric_free_wire_codec_handoff_only' as const});
}
