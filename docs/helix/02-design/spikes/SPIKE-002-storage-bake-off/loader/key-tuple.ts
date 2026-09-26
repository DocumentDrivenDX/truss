// Fast local encoder for UMF's canonical key tuple profile umf-key-tuple-v1 (CONTRACT-040 §Portable key tuple
// encoding), for bulk use: UMF's encodeCoreKeyTuple validates the whole document on every call (~124 keys/s here).
// Verified against fixtures/key/tuple-encoding-v1.json and UMF's encoder by harness/key_tuple.ts.
const te=new TextEncoder();
const leb=(n:number)=>{const o:number[]=[];do{let b=n&0x7f;n>>>=7;if(n)b|=0x80;o.push(b);}while(n);return o;};
export type KeyValue={boolean:boolean}|{integerToken:string}|{decimalToken:string;scale:number}|{string:string}|{binaryHex:string};
function payload(v:KeyValue):[number,Uint8Array]{
  if('boolean' in v)return [1,new Uint8Array([v.boolean?1:0])];
  if('integerToken' in v){if(!/^-?(0|[1-9][0-9]*)$/.test(v.integerToken))throw new Error('non-canonical integer');const t=v.integerToken==='-0'?'0':v.integerToken;return [2,te.encode(t)];}
  if('decimalToken' in v){const m=/^(-?)([0-9]+)(?:\.([0-9]+))?$/.exec(v.decimalToken);if(!m)throw new Error('bad decimal');
    let frac=m[3]??'';if(frac.length>v.scale){if(/[^0]/.test(frac.slice(v.scale)))throw new Error('rounding required');frac=frac.slice(0,v.scale);}
    let coef=(m[2]!+frac.padEnd(v.scale,'0')).replace(/^0+(?=[0-9])/,'');const neg=m[1]==='-'&&coef!=='0';
    return [3,new Uint8Array([...leb(v.scale),...te.encode((neg?'-':'')+coef)])];}
  if('string' in v)return [4,te.encode(v.string)];
  const h=v.binaryHex;const b=new Uint8Array(h.length/2);for(let i=0;i<b.length;i++)b[i]=parseInt(h.slice(i*2,i*2+2),16);return [5,b];
}
export function encodeKeyTuple(values:KeyValue[]):Uint8Array{
  const parts:number[]=[...te.encode('UMFK1'),...leb(values.length)];
  for(const v of values){const [tag,p]=payload(v);parts.push(tag,...leb(p.length),...p);}
  return new Uint8Array(parts);
}
export const hex=(b:Uint8Array)=>Array.from(b,x=>x.toString(16).padStart(2,'0')).join('');
