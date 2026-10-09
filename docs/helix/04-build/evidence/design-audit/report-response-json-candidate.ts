/** Private response-only scanner candidate. Original request parser is unchanged.
 * Fork source sha256: 14a65dc9fd67b3ab53fb080a4a05422b991af63feac52fc6e0655eb03a47ed17
 * Source/structure/logical-work limits only; no original schema/account authority. */
export type ReportResponseJson = null|boolean|string|ReportResponseJson[]|{[key:string]:ReportResponseJson};
export type WireRefusal='grammar'|'unicode'|'duplicate_member'|'numeric_node'|'resource';
export class ReportResponseJsonError extends Error {constructor(readonly reason:WireRefusal){super(reason)}}
const MAX_BYTES=4194304,MAX_DEPTH=128,MAX_NODES=100000,MAX_MEMBERS=4096,MAX_WORK=33554432;
type Frame={kind:'object';value:{[key:string]:ReportResponseJson};state:'first'|'key'|'colon'|'value'|'comma';key:string;keys:string[]}|{kind:'array';value:ReportResponseJson[];state:'first'|'value'|'comma'};
/** Caller must retain original immutable bytes; this component copies its input.
 * Finite logical limits below do not qualify host heap or the shared operation account. */
export function decodeReportResponseJson(original:Uint8Array):ReportResponseJson {
 return scanJson(original,false);
}
function scanJson(original:Uint8Array,sourceNumbers:boolean):ReportResponseJson {
 const refuse=(reason:WireRefusal):never=>{throw new ReportResponseJsonError(reason)};
 if(original.length>MAX_BYTES)refuse('resource');const bytes=original.slice();
 let index=0,nodes=0,work=bytes.length;const stack:Frame[]=[];let root:ReportResponseJson|undefined;
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
 const attach=(value:ReportResponseJson)=>{const parent=stack.at(-1);if(!parent){if(root!==undefined)refuse('grammar');root=value;return}
  if(parent.kind==='array'){if(parent.value.length>=MAX_MEMBERS)refuse('resource');parent.value.push(value);parent.state='comma'}
  else {Object.defineProperty(parent.value,parent.key,{value,enumerable:true,writable:true,configurable:true});parent.state='comma'}
 };
 const value=()=>{whitespace();if(++nodes>MAX_NODES||stack.length>MAX_DEPTH)refuse('resource');const c=bytes[index];
  if(c===34){attach(string());return}if(c===123||c===91){take();const item:ReportResponseJson=c===123?Object.create(null):[];attach(item);stack.push(c===123?{kind:'object',value:item as {[key:string]:ReportResponseJson},state:'first',key:'',keys:[]}:{kind:'array',value:item as ReportResponseJson[],state:'first'});return}
  for(const [token,result] of [['null',null],['true',true],['false',false]] as const){if(c===token.charCodeAt(0)){for(const ch of token)if(take()!==ch.charCodeAt(0))refuse('grammar');attach(result);return}}
  if(c===45||(c!==undefined&&c>=48&&c<=57)){
   if(!sourceNumbers)refuse('numeric_node');
   const digit=()=>bytes[index]!==undefined&&bytes[index]!>=48&&bytes[index]!<=57;
   if(bytes[index]===45)take();
   if(bytes[index]===48)take();else {if(!digit()||bytes[index]===48)refuse('grammar');while(digit())take()}
   if(bytes[index]===46){take();if(!digit())refuse('grammar');while(digit())take()}
   if(bytes[index]===101||bytes[index]===69){take();if(bytes[index]===43||bytes[index]===45)take();if(!digit())refuse('grammar');while(digit())take()}
   // Inert placeholder belongs only to the discarded structural scan tree.
   attach(null);return;
  }refuse('grammar');
 };
 value();while(stack.length){whitespace();const frame=stack.at(-1)!;const c=bytes[index];
  if(frame.kind==='array'){
   if(frame.state==='first'&&c===93){take();stack.pop()}
   else if(frame.state==='first'||frame.state==='value')value();
   else if(c===93){take();stack.pop()}else if(c===44){take();frame.state='value'}else refuse('grammar');
  }else{
   if(frame.state==='first'&&c===125){take();stack.pop()}
   else if(frame.state==='first'||frame.state==='key'){
    if(c!==34)refuse('grammar');if(frame.keys.length>=MAX_MEMBERS)refuse('resource');const key=string();
    for(const previous of frame.keys){charge(2*(previous.length+key.length));if(previous===key)refuse('duplicate_member')}
    frame.keys.push(key);frame.key=key;frame.state='colon';
   }else if(frame.state==='colon'){if(take()!==58)refuse('grammar');frame.state='value'}
   else if(frame.state==='value')value();else if(c===125){take();stack.pop()}else if(c===44){take();frame.state='key'}else refuse('grammar');
  }
 }
 whitespace();if(index!==bytes.length||root===undefined)refuse('grammar');return root!;
}
