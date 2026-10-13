/** Thin native observation → original semantic owner handoff. No credentials. */
import {createHash} from 'node:crypto';
import {types as nativeTypes} from 'node:util';
import type {NativeConnection} from '@documentdrivendx/truss-postgresql';
import type {OrdinarySubjectObservation} from './index';
export interface OriginalSubjectKeyOwner {
  readJsonValue:(text:string,format:'json')=>unknown;
  encodeCoreKeyTuple:(source:unknown,identity:unknown,values:unknown)=>unknown;
  readCoreKeyTupleBytes:(receipt:unknown,source:unknown)=>Uint8Array;
}
export interface SubjectKeyBindingOptions {
  readonly host:{observeOrdinarySubject:(connection:NativeConnection)=>OrdinarySubjectObservation};
  /** Exact original owner functions; shape and output do not authenticate code. */
  readonly owner:OriginalSubjectKeyOwner;
  /** Original source-bound ontology Subject/Record/Key inspection; no issuer proof. */
  readonly inspectSubjectKey:(selection:{readonly sourceSha256:string;readonly identity:SubjectKeyBindingOptions['identity']})=>undefined;
  readonly sourceText:string;
  readonly identity:{readonly module:string;readonly element:string;readonly key:string};
  readonly keyColumns:readonly string[];
  readonly encodings:readonly ('string'|'core-literal-json')[];
}
export interface ObservedSubjectKey {
  readonly principal:string;readonly sourceSha256:string;
  /** Exact observed input bytes remain available beside owner interpretation. */
  readonly observation:OrdinarySubjectObservation;
  readonly identity:SubjectKeyBindingOptions['identity'];
  readonly bytesHex:string;readonly originalReceiptText:string;
}
/** The trusted host selects model, ordered native mapping and original owner.
 * Returned tuple evidence is an observation, not authenticated subject issuance,
 * current authority, referenced-record existence or protected release. */
export function createOrdinarySubjectKeyBinding(options:SubjectKeyBindingOptions):{
  readonly encode:(connection:NativeConnection)=>ObservedSubjectKey;
}{
 const refuse=()=>{throw Error('Original subject key binding refused');};
 const sourceText=options.sourceText;
 if(typeof sourceText!=='string'||!sourceText.length||Buffer.byteLength(sourceText)>1048576||Buffer.from(sourceText,'utf8').toString('utf8')!==sourceText)return refuse();
 const identity=Object.freeze({...options.identity});
 if(Object.keys(identity).sort().join(',')!=='element,key,module'||Object.values(identity).some(v=>typeof v!=='string'||!v.length||v.includes('\0')||Buffer.byteLength(v)>4096))return refuse();
 const columns=Object.freeze([...options.keyColumns]),encodings=Object.freeze([...options.encodings]);
 if(!columns.length||columns.length>32||columns.length!==encodings.length||new Set(columns).size!==columns.length||columns.some(c=>typeof c!=='string'||!c.length||Buffer.byteLength(c)>63)||encodings.some(e=>e!=='string'&&e!=='core-literal-json'))return refuse();
 const observe=options.host.observeOrdinarySubject.bind(options.host);
 const read=options.owner.readJsonValue.bind(options.owner),encode=options.owner.encodeCoreKeyTuple.bind(options.owner),bytes=options.owner.readCoreKeyTupleBytes.bind(options.owner);
 const sourceSha256=createHash('sha256').update(sourceText).digest('hex');
 const inspect=options.inspectSubjectKey;
 if(typeof inspect!=='function'||nativeTypes.isAsyncFunction(inspect)||nativeTypes.isGeneratorFunction(inspect))return refuse();
 // Selection is immutable, and a deferred result cannot constitute inspection.
 const inspected=inspect(Object.freeze({sourceSha256,identity}));
 if(nativeTypes.isPromise(inspected)){
  // Ordinary Promise returns are observed. Configured code, including mutated
  // Promise constructors/species or hidden async wrappers, remains trusted.
  Promise.prototype.then.call(inspected,undefined,()=>{});return refuse();
 }
 if(inspected!==undefined)return refuse();
 return Object.freeze({encode(connection){
  const observation=observe(connection);
  if(JSON.stringify(observation.keyColumns)!==JSON.stringify(columns)||observation.keyValues.length!==encodings.length)return refuse();
  if(observation.keyValues.reduce((n,v)=>n+Buffer.byteLength(v),0)>1048576)return refuse();
  // Native TEXT has no implied semantic family. No numeric conversion is added.
  const values=observation.keyValues.map((text,i)=>encodings[i]==='string'?{string:text}:read(text,'json'));
  const source=read(sourceText,'json');
  const receipt=encode(source,identity,values),tuple=bytes(receipt,source);
  if(!(tuple instanceof Uint8Array)||tuple.length>4194304)return refuse();
  const originalReceiptText=JSON.stringify(receipt);
  if(typeof originalReceiptText!=='string'||Buffer.byteLength(originalReceiptText)>8388608)return refuse();
  const value=receipt as {bytesHex?:unknown};const bytesHex=Buffer.from(tuple).toString('hex');
  if(value?.bytesHex!==bytesHex)return refuse();
  return Object.freeze({principal:observation.principal,sourceSha256,identity,observation,bytesHex,originalReceiptText});
 }});
}
