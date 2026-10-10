/** Exact key transport comparison with an independently registered original UMF
 * producer. Neither a codec-shaped object nor namespace bytes authenticate scope. */
export interface SecurityKeyTupleProducer {
  encodeCoreKeyTuple(source:unknown,identity:{module:string;element:string;key:string},values:unknown):any;
  verifyCoreKeyTuple(receipt:any,source:unknown):any;
}
const fail=():never=>{throw Error('TRUSS_SECURITY_KEY_TRANSPORT_UNSUPPORTED');};
function hex(v:unknown,max:number):string{if(typeof v!=='string'||!v.length||v.length>max*2||v.length%2||! /^[0-9a-f]+$/.test(v))return fail();return v;}
/** Namespace must already be tied to original installation/catalog/key/codec
 * authority. Captured methods and source selection cannot change after creation. */
export function createSecurityKeyTransportVerifier(producer:SecurityKeyTupleProducer,selection:{
  source:unknown;identity:{module:string;element:string;key:string};namespaceHex:string;
}){
 if(typeof producer.encodeCoreKeyTuple!=='function'||typeof producer.verifyCoreKeyTuple!=='function')return fail();
 const encode=producer.encodeCoreKeyTuple.bind(producer),verify=producer.verifyCoreKeyTuple.bind(producer);
 const source=structuredClone(selection.source),identity=structuredClone(selection.identity),namespaceHex=hex(selection.namespaceHex,65536);
 const encodeKey=(values:unknown)=>{
  const receipt=verify(encode(source,identity,values),source);
  if(receipt.operation!=='encode-core-key-tuple'||receipt.version!=='3.0.0'||receipt.profile!=='umf-key-tuple-v1')return fail();
  const bytes=hex(receipt.bytesHex,1048576),text='umf-key-tuple-v1:hex:'+bytes;
  const transport=new TextEncoder().encode(text);if(transport.length>1048576)return fail();
  const chunks:string[]=[];
  for(let i=0;i<transport.length;i+=4096)chunks.push(Array.from(transport.subarray(i,i+4096),b=>b.toString(16).padStart(2,'0')).join(''));
  return Object.freeze({namespaceHex,keyHex:chunks.join('')});
 };
 return Object.freeze({encode:encodeKey,matches(values:unknown,stored:{namespaceHex:string;keyHex:string}):boolean{
  try{const expected=encodeKey(values);return hex(stored.namespaceHex,65536)===expected.namespaceHex&&hex(stored.keyHex,1048576)===expected.keyHex;}catch{return false;}
 }});
}
