/** Namespace grammar/correspondence only. Original installation/catalog/codec
 * authority and native canonical producer custody must be qualified separately. */
export interface SecurityKeyNamespaceSelection {
  profile:'truss-key-bucket/0.1.0'|'truss-key-bucket/0.2.0';
  sourceEpoch:string;installationId:string;typeId:string;keyNumber:string;
  encoding:{identity:string;version:string;sha256:string};
}
const refuse=():never=>{throw Error('TRUSS_SECURITY_KEY_NAMESPACE_UNSUPPORTED');};
function scalar(v:unknown):string{
 if(typeof v!=='string'||!v||new TextEncoder().encode(v).length>65536||[...v].some(c=>c.codePointAt(0)!>=0xd800&&c.codePointAt(0)!<=0xdfff))return refuse();return v;
}
function keys(v:unknown,expected:string[]):void{
 if(!v||typeof v!=='object'||Array.isArray(v)||Object.keys(v).sort().join(',')!==[...expected].sort().join(','))return refuse();
}
function namespaceHex(v:unknown):string{if(typeof v!=='string'||!v.length||v.length>131072||v.length%2||! /^[0-9a-f]+$/.test(v))return refuse();return v;}
/** Opaque producer is independently registered, never supplied by an operation.
 * Both supplied selection and native bytes are captured before awaiting it. */
export async function securityKeyNamespaceCorresponds(selection:SecurityKeyNamespaceSelection,stored: string,
 canonicalStringArrayHex:(values:readonly string[])=>Promise<string>|string):Promise<boolean>{
 try{
  keys(selection,['profile','sourceEpoch','installationId','typeId','keyNumber','encoding']);keys(selection.encoding,['identity','version','sha256']);
  const input=structuredClone(selection),original=namespaceHex(stored);
  if(!['truss-key-bucket/0.1.0','truss-key-bucket/0.2.0'].includes(input.profile)||! /^[0-9a-f]{64}$/.test(input.encoding.sha256))return false;
  for(const [value,bits] of [[input.typeId,31n],[input.keyNumber,15n]] as const){
   if(typeof value!=='string'||! /^(0|-?[1-9][0-9]*)$/.test(value)||value.length>11)return false;
   const n=BigInt(value);if(n<-(1n<<bits)||n>=(1n<<bits)||input.profile==='truss-key-bucket/0.1.0'&&n<=0n)return false;
  }
  const values=[input.profile,input.sourceEpoch,input.installationId,input.typeId,input.keyNumber,input.encoding.identity,input.encoding.version,input.encoding.sha256].map(scalar);
  const bytes=new Uint8Array(original.length/2);for(let i=0;i<bytes.length;i++)bytes[i]=parseInt(original.slice(i*2,i*2+2),16);
  const parsed:unknown=JSON.parse(new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes));
  if(!Array.isArray(parsed)||parsed.length!==8||parsed.some((value,i)=>typeof value!=='string'||value!==values[i]))return false;
  // Native canonical spelling is supplied by its owner, not JSON.stringify.
  // Equivalent whitespace/escape spellings must not silently replace originals.
  return namespaceHex(await canonicalStringArrayHex(Object.freeze([...values])))===original;
 }catch{return false;}
}

/** Host registration convenience. Operation inputs cannot replace the retained
 * selection or canonical producer after this private verifier is constructed. */
export function createSecurityKeyNamespaceVerifier(selection:SecurityKeyNamespaceSelection,
 canonicalStringArrayHex:(values:readonly string[])=>Promise<string>|string){
 if(typeof canonicalStringArrayHex!=='function')return refuse();
 const original=structuredClone(selection),encode=canonicalStringArrayHex.bind(undefined);
 return Object.freeze({matches:(stored:string)=>securityKeyNamespaceCorresponds(original,stored,encode)});
}
