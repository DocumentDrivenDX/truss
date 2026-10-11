import {copyOriginalByteCustody,OriginalByteCustodyError} from './original-byte-custody';
/** Internal wire decoder component. Not complete input/profile/native admission. */
export type AcceptanceJson = null|boolean|string|AcceptanceJson[]|{[key:string]:AcceptanceJson};
export type WireRefusal='grammar'|'unicode'|'duplicate_member'|'numeric_node'|'resource';
export class AcceptanceJsonError extends Error {constructor(readonly reason:WireRefusal){super(reason)}}
const MAX_DEPTH=128,MAX_NODES=100000,MAX_MEMBERS=4096,MAX_WORK=2000000;
type Frame={kind:'object';value:{[key:string]:AcceptanceJson};state:'first'|'key'|'colon'|'value'|'comma';key:string;keys:string[];occurrence?:number}|{kind:'array';value:AcceptanceJson[];state:'first'|'value'|'comma';occurrence?:number};
/** Caller must retain original immutable bytes; this component copies its input.
 * Finite logical limits below do not qualify host heap or the shared operation account. */
export function decodeAcceptanceJson(original:Uint8Array):AcceptanceJson {
 return scanJson(original,false);
}
/** Structural source preflight only. Numeric lexemes are scanned, never converted
 * to JavaScript numbers. No semantic tree or precision qualification is returned. */
export function preflightSourceJson(original:Uint8Array):void {
 scanJson(original,true);
}
type SourceOccurrence={pointer:string;kind:'object'|'array'|'string'|'number'|'boolean'|'null';start:number;end:number};
type SourceIndex=Readonly<{originalByteLength:number;occurrences:readonly Readonly<SourceOccurrence>[];scope:'original_json_value_occurrences_only'}>;
const originalIndexes=new WeakMap<object,Uint8Array>();
/** Complete JSON value positions, not assertion interpretation. Numeric lexemes stay original bytes. */
export function indexSourceJsonOccurrences(original:Uint8Array):SourceIndex{
 const capture:{occurrences:SourceOccurrence[];bytes?:Uint8Array}={occurrences:[]};
 scanJson(original,true,capture);
 const index=Object.freeze({originalByteLength:capture.bytes!.length,occurrences:Object.freeze(capture.occurrences.map(row=>Object.freeze({...row}))),scope:'original_json_value_occurrences_only' as const});
 originalIndexes.set(index,capture.bytes!);return index;
}
/** A fresh copy of the originally captured value bytes; no parse or number conversion. */
export function originalSourceOccurrenceBytes(index:SourceIndex,position:number):Uint8Array{
 const bytes=originalIndexes.get(index);
 if(!bytes)throw Error('Original source occurrence index custody required');
 if(!Number.isSafeInteger(position)||position<0||position>=index.occurrences.length)throw Error('Original source occurrence position required');
 const span=index.occurrences[position]!;return bytes.slice(span.start,span.end);
}
function scanJson(original:Uint8Array,sourceNumbers:boolean,capture?:{occurrences:SourceOccurrence[];bytes?:Uint8Array}):AcceptanceJson {
 const refuse=(reason:WireRefusal):never=>{throw new AcceptanceJsonError(reason)};
 let bytes:Uint8Array;try{bytes=copyOriginalByteCustody(original)}catch(error){if(error instanceof OriginalByteCustodyError)refuse(error.reason==='resource'?'resource':'grammar');throw error}if(capture)capture.bytes=bytes;
 let index=0,nodes=0,work=bytes.length;const stack:Frame[]=[];let root:AcceptanceJson|undefined;
 const charge=(n:number)=>{if(!Number.isSafeInteger(n)||n<0||work>MAX_WORK-n)refuse('resource');work+=n};
 const take=()=>{charge(1);return bytes[index++]};
 const whitespace=()=>{while(index<bytes.length&&[32,9,10,13].includes(bytes[index]!))take()};
 const string=():string=>{
  const start=index;if(take()!==34)refuse('grammar');let closed=false;
  while(index<bytes.length){const c=take();if(c===34){closed=true;break}if(c!<32)refuse('grammar');
   if(c===92){const e=take();if(e===117){let code=0;for(let n=0;n<4;n++){const h=take();const v=h!==undefined?parseInt(String.fromCharCode(h),16):NaN;if(!Number.isInteger(v)||!/[0-9a-fA-F]/.test(String.fromCharCode(h!)))refuse('grammar');code=code*16+v}
     if(code>=0xd800&&code<=0xdbff){if(take()!==92||take()!==117)refuse('unicode');let low=0;for(let n=0;n<4;n++){const h=take();if(h===undefined||!/[0-9a-fA-F]/.test(String.fromCharCode(h)))refuse('unicode');low=low*16+parseInt(String.fromCharCode(h),16)}if(low<0xdc00||low>0xdfff)refuse('unicode')}
     else if(code>=0xdc00&&code<=0xdfff)refuse('unicode');
    }else if(![34,92,47,98,102,110,114,116].includes(e!))refuse('grammar');
   }
  }
  if(!closed)refuse('grammar');charge(2*(index-start));let text:string;
  try{text=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes.subarray(start,index))}catch{refuse('unicode')}
  try{return JSON.parse(text!) as string}catch{return refuse('grammar')}
 };
 const attach=(value:AcceptanceJson)=>{const parent=stack.at(-1);if(!parent){if(root!==undefined)refuse('grammar');root=value;return}
  if(parent.kind==='array'){if(parent.value.length>=MAX_MEMBERS)refuse('resource');parent.value.push(value);parent.state='comma'}
  else {Object.defineProperty(parent.value,parent.key,{value,enumerable:true,writable:true,configurable:true});parent.state='comma'}
 };
 const close=()=>{take();const frame=stack.pop()!;if(capture&&frame.occurrence!==undefined)capture.occurrences[frame.occurrence]!.end=index};
 const value=()=>{whitespace();const start=index,parent=stack.at(-1);let pointer='';
  if(capture&&parent){const prefix=capture.occurrences[parent.occurrence!]!.pointer;pointer=prefix+'/'+(parent.kind==='array'?String(parent.value.length):parent.key.replace(/~/g,'~0').replace(/\//g,'~1'));charge(2*pointer.length)}
  const record=(kind:SourceOccurrence['kind'])=>{if(!capture)return undefined;const position=capture.occurrences.length;capture.occurrences.push({pointer,kind,start,end:index});return position};
  if(++nodes>MAX_NODES||stack.length>MAX_DEPTH)refuse('resource');const c=bytes[index];
  if(c===34){const text=string();record('string');attach(text);return}if(c===123||c===91){take();const item:AcceptanceJson=c===123?Object.create(null):[];const occurrence=record(c===123?'object':'array');attach(item);stack.push(c===123?{kind:'object',value:item as {[key:string]:AcceptanceJson},state:'first',key:'',keys:[],occurrence}:{kind:'array',value:item as AcceptanceJson[],state:'first',occurrence});return}
  for(const [token,result] of [['null',null],['true',true],['false',false]] as const){if(c===token.charCodeAt(0)){for(const ch of token)if(take()!==ch.charCodeAt(0))refuse('grammar');record(result===null?'null':'boolean');attach(result);return}}
  if(c===45||(c!==undefined&&c>=48&&c<=57)){
   if(!sourceNumbers)refuse('numeric_node');
   const digit=()=>bytes[index]!==undefined&&bytes[index]!>=48&&bytes[index]!<=57;
   if(bytes[index]===45)take();
   if(bytes[index]===48)take();else {if(!digit()||bytes[index]===48)refuse('grammar');while(digit())take()}
   if(bytes[index]===46){take();if(!digit())refuse('grammar');while(digit())take()}
   if(bytes[index]===101||bytes[index]===69){take();if(bytes[index]===43||bytes[index]===45)take();if(!digit())refuse('grammar');while(digit())take()}
   // Inert placeholder belongs only to the discarded structural scan tree.
   record('number');attach(null);return;
  }refuse('grammar');
 };
 value();while(stack.length){whitespace();const frame=stack.at(-1)!;const c=bytes[index];
  if(frame.kind==='array'){
   if(frame.state==='first'&&c===93){close()}
   else if(frame.state==='first'||frame.state==='value')value();
   else if(c===93){close()}else if(c===44){take();frame.state='value'}else refuse('grammar');
  }else{
   if(frame.state==='first'&&c===125){close()}
   else if(frame.state==='first'||frame.state==='key'){
    if(c!==34)refuse('grammar');if(frame.keys.length>=MAX_MEMBERS)refuse('resource');const key=string();
    for(const previous of frame.keys){charge(2*(previous.length+key.length));if(previous===key)refuse('duplicate_member')}
    frame.keys.push(key);frame.key=key;frame.state='colon';
   }else if(frame.state==='colon'){if(take()!==58)refuse('grammar');frame.state='value'}
   else if(frame.state==='value')value();else if(c===125){close()}else if(c===44){take();frame.state='key'}else refuse('grammar');
  }
 }
 whitespace();if(index!==bytes.length||root===undefined)refuse('grammar');return root!;
}
