/** Bounded original PostgreSQL response-frame subset; not a socket/authority producer. */
export interface WireLimits {readonly maxFrameBytes:number;readonly maxFields:number}
export function decodeResponseFrame(frame:Uint8Array,limits:WireLimits): {
 readonly kind:string;readonly originalHex:string;readonly fields:readonly Readonly<Record<string,string|null>>[];
} {
 const fail=():never=>{throw Error('pg-wire:unsupported-or-malformed');};
 if(![limits.maxFrameBytes,limits.maxFields].every(n=>Number.isSafeInteger(n)&&n>=0)||frame.length>limits.maxFrameBytes||frame.length<5)fail();
 let offset=1;
 const uint=(bytes:number):bigint=>{if(offset+bytes>frame.length)fail();let n=0n;for(let i=0;i<bytes;i++)n=n*256n+BigInt(frame[offset++]);return n;};
 const length=uint(4);if(length<4n||length+1n!==BigInt(frame.length))fail();
 const text=()=>{const start=offset;while(offset<frame.length&&frame[offset]!==0)offset++;
   if(offset===frame.length)fail();let value:string;
   try{value=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(frame.subarray(start,offset));}catch{return fail();}
   offset++;return value;};
 const signed=(n:bigint,bits:bigint)=>n>=(1n<<(bits-1n))?n-(1n<<bits):n;
 const hex=(bytes:Uint8Array)=>{let value='';for(const byte of bytes)value+=byte.toString(16).padStart(2,'0');return value;};
 const kind=String.fromCharCode(frame[0]);const fields:Readonly<Record<string,string|null>>[]=[];
 if(kind==='T'){
   const count=uint(2);if(count>BigInt(limits.maxFields)||count>32767n)fail();
   for(let i=0n;i<count;i++)fields.push(Object.freeze({name:text(),tableOid:uint(4).toString(),attribute:signed(uint(2),16n).toString(),typeOid:uint(4).toString(),typeSize:signed(uint(2),16n).toString(),typeModifier:signed(uint(4),32n).toString(),format:uint(2).toString()}));
   if(fields.some(field=>field.format!=='0'&&field.format!=='1'))fail();
 }else if(kind==='D'){
   const count=uint(2);if(count>BigInt(limits.maxFields)||count>32767n)fail();
   for(let i=0n;i<count;i++){
     const size=signed(uint(4),32n);
     if(size===-1n){fields.push(Object.freeze({hex:null}));continue;}
     if(size<0n||size>BigInt(frame.length-offset))fail();
     const end=offset+Number(size);fields.push(Object.freeze({hex:hex(frame.subarray(offset,end))}));offset=end;
   }
 }else if(kind==='C'){
   const command=text();const match=/^(SELECT|UPDATE|DELETE|MOVE|FETCH|COPY) (0|[1-9][0-9]*)$/.exec(command)||/^INSERT (?:0|[1-9][0-9]*) (0|[1-9][0-9]*)$/.exec(command);
   fields.push(Object.freeze({command,affectedRows:match?match[2]??match[1]:null}));
   // INSERT's capture differs from other command tags; preserve exact original tag regardless.
   if(command.startsWith('INSERT ')){const parts=command.split(' ');if(parts.length!==3||!parts.every((p,i)=>i===0||/^(0|[1-9][0-9]*)$/.test(p)))fail();fields[0]=Object.freeze({command,affectedRows:parts[2]});}
 }else if(kind==='Z'){
   if(offset+1!==frame.length)fail();const status=String.fromCharCode(frame[offset++]);if(!['I','T','E'].includes(status))fail();fields.push(Object.freeze({status}));
 }else fail();
 if(offset!==frame.length)fail();
 return Object.freeze({kind,originalHex:hex(frame),fields:Object.freeze(fields)});
}
