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

/** Complete-frame admission before forwarding; delivered socket chunks already exist. */
export class ResponseIngress {
 #header=new Uint8Array(5);#headerUsed=0;#frame:Uint8Array|undefined;#used=0;
 #bytes=0;#frames=0;#failed=false;#columns:number|undefined;#phase:'start'|'rows'|'command'|'ended'='start';#rowCount=0n;
 constructor(readonly limits:WireLimits&{readonly maxTotalBytes:number;readonly maxFrames:number}){
   if(![limits.maxFrameBytes,limits.maxFields,limits.maxTotalBytes,limits.maxFrames].every(n=>Number.isSafeInteger(n)&&n>=0))throw Error('pg-ingress:invalid-limits');
   this.limits=Object.freeze({...limits});
 }
 feed(chunk:Uint8Array,forward:(frame:Uint8Array)=>void):void {
   if(this.#failed)throw Error('pg-ingress:refused');
   try{
     if(this.#phase==='ended'&&chunk.length)throw Error('pg-ingress:ended');
     if(chunk.length>this.limits.maxTotalBytes-this.#bytes)throw Error('pg-ingress:byte-limit');
     this.#bytes+=chunk.length;let at=0;
     while(at<chunk.length){
       if(!this.#frame){
         const take=Math.min(5-this.#headerUsed,chunk.length-at);this.#header.set(chunk.subarray(at,at+take),this.#headerUsed);this.#headerUsed+=take;at+=take;
         if(this.#headerUsed<5)continue;
         let size=0n;for(let i=1;i<5;i++)size=size*256n+BigInt(this.#header[i]);
         if(size<4n||size+1n>BigInt(this.limits.maxFrameBytes)||this.#frames===this.limits.maxFrames)throw Error('pg-ingress:frame-limit');
         if(![84,68,67,90].includes(this.#header[0]))throw Error('pg-ingress:unsupported-kind');
         this.#frame=new Uint8Array(Number(size)+1);this.#frame.set(this.#header);this.#used=5;this.#headerUsed=0;
       }
       const take=Math.min(this.#frame.length-this.#used,chunk.length-at);this.#frame.set(chunk.subarray(at,at+take),this.#used);this.#used+=take;at+=take;
       if(this.#used===this.#frame.length){
         const decoded=decodeResponseFrame(this.#frame,this.limits);
         if(decoded.kind==='T'){
           if(this.#phase!=='start')throw Error('pg-ingress:response-order');
           this.#phase='rows';
           if(decoded.fields.some(field=>field.format!=='0'))throw Error('pg-ingress:binary-unqualified');
           this.#columns=decoded.fields.length;
         }else if(decoded.kind==='D'){
           if(this.#phase!=='rows'||this.#columns===undefined||decoded.fields.length!==this.#columns)throw Error('pg-ingress:row-description');
           this.#rowCount++;
           for(const field of decoded.fields){if(field.hex===null)continue;
             const bytes=new Uint8Array(field.hex!.length/2);for(let i=0;i<bytes.length;i++)bytes[i]=parseInt(field.hex!.slice(i*2,i*2+2),16);
             new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);
           }
         }else if(decoded.kind==='C'){
           if(this.#phase!=='start'&&this.#phase!=='rows')throw Error('pg-ingress:response-order');
           const command=decoded.fields[0].command;
           if(command?.startsWith('SELECT ')&&(decoded.fields[0].affectedRows===null||BigInt(decoded.fields[0].affectedRows!)!==this.#rowCount))throw Error('pg-ingress:row-count');
           this.#phase='command';
         }else if(decoded.kind==='Z'){
           if(this.#phase!=='command')throw Error('pg-ingress:response-order');
           this.#columns=undefined;this.#phase='ended';
         }
         this.#frames++;const original=this.#frame;this.#frame=undefined;this.#used=0;
         forward(original);
       }
     }
   }catch(error){this.#failed=true;throw error;}
 }
 finish():void {if(this.#failed||this.#headerUsed||this.#frame||this.#phase!=='ended'){this.#failed=true;throw Error('pg-ingress:incomplete');}}
 get accounting(){return Object.freeze({bytes:this.#bytes,frames:this.#frames,refused:this.#failed});}
}
