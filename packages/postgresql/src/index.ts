/** Inert construction only. No native capability, profile or permission is inferred. */
import type {ReferenceAssemblyConfiguration, ReferenceAssembly, AssemblyConstructionResult, AssemblyDisposalResult}
  from '../../../docs/helix/02-design/contracts/bindings/truss-reference-assembly-v0.1';
import type {Executor, Outcome, TransactionHandle, SavepointHandle, Statement, StatementResult, TransactionOptions, ExecutionFailure} from '../../../docs/helix/02-design/contracts/bindings/truss-execution-v0.1';
import type {ProfilePin} from '../../../docs/helix/02-design/contracts/bindings/truss-acceptance-input-v0.1';
import type {CapabilitySelection, CapabilityReadiness}
  from '../../../docs/helix/02-design/contracts/bindings/truss-capability-readiness-v0.1';
import type {HostRecoveryRegistry} from '../../../docs/helix/02-design/contracts/bindings/truss-recovery-registry-v0.1';
import type {HostRequestNamespaceAuthority} from '../../../docs/helix/02-design/contracts/bindings/truss-request-namespace-v0.1';
import type {FeedProofVerifierRegistration} from '../../../docs/helix/02-design/contracts/bindings/truss-feed-proof-verifier-v0.1';
export type {ReferenceAssemblyConfiguration, ReferenceAssembly, AssemblyConstructionResult, AssemblyDisposalRequest, AssemblyDisposalResult}
  from '../../../docs/helix/02-design/contracts/bindings/truss-reference-assembly-v0.1';
export type {Executor, TransactionHandle, SavepointHandle, Statement, StatementResult, Outcome}
  from '../../../docs/helix/02-design/contracts/bindings/truss-execution-v0.1';
export type {CapabilitySelection, CapabilityReadiness}
  from '../../../docs/helix/02-design/contracts/bindings/truss-capability-readiness-v0.1';
export type {ProfilePin} from '../../../docs/helix/02-design/contracts/bindings/truss-acceptance-input-v0.1';
export type {HostRecoveryRegistry} from '../../../docs/helix/02-design/contracts/bindings/truss-recovery-registry-v0.1';

export const INERT_ASSEMBLY_PROFILE: ProfilePin = Object.freeze({
  identity: 'truss-reference-assembly-inert', version: '0.1.0', sha256: '3cca9dddd4b39f0325392acae67832137a9f3d6ddc2824e344f6f1a182742d09'
});
const families = new Set(['catalog', 'mutation', 'group', 'import', 'direct_read', 'history', 'feed',
  'weft_execution', 'bootstrap', 'physical_optimization', 'conformance']);

function record(value: unknown): Record<string, unknown> | undefined {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return;
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) return;
  const descriptors = Object.getOwnPropertyDescriptors(value);
  if (Reflect.ownKeys(value).some(key => typeof key !== 'string' || !('value' in descriptors[key]))) return;
  const result: Record<string, unknown> = Object.create(null);
  for (const [key, descriptor] of Object.entries(descriptors)) result[key] = descriptor.value;
  return result;
}
function own(value: unknown, key: string): unknown {
  if (!value || typeof value !== 'object') return;
  const descriptor = Object.getOwnPropertyDescriptor(value, key);
  return descriptor && 'value' in descriptor ? descriptor.value : undefined;
}
function exact(value: Record<string, unknown>, required: string[], optional: string[] = []): boolean {
  return required.every(key => Object.hasOwn(value, key)) && Object.keys(value).every(key => required.includes(key) || optional.includes(key));
}
function text(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0 && value.length <= 1024 && !value.includes('\0');
}
function pin(value: unknown): ProfilePin | undefined {
  const data = record(value);
  if (!data || !exact(data, ['identity', 'version', 'sha256']) || !text(data.identity) || !text(data.version)
      || typeof data.sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(data.sha256)) return;
  return Object.freeze({identity: data.identity, version: data.version, sha256: data.sha256});
}
function same(left: ProfilePin, right: ProfilePin): boolean {
  return left.identity === right.identity && left.version === right.version && left.sha256 === right.sha256;
}
function selection(value: unknown): CapabilitySelection | undefined {
  const data = record(value);
  const keys = ['capabilityProfile', 'layoutProfile', 'adapterProfile', 'valueProfile', 'policyProfile'] as const;
  if (!data || !exact(data, ['family', ...keys]) || typeof data.family !== 'string' || !families.has(data.family)) return;
  const profiles = keys.map(key => pin(data[key]));
  if (profiles.some(value => value === undefined)) return;
  return Object.freeze({family: data.family as CapabilitySelection['family'],
    capabilityProfile: profiles[0]!, layoutProfile: profiles[1]!, adapterProfile: profiles[2]!,
    valueProfile: profiles[3]!, policyProfile: profiles[4]!});
}
function selectionKey(value: CapabilitySelection): string {
  return JSON.stringify([value.family, ...[value.capabilityProfile, value.layoutProfile, value.adapterProfile,
    value.valueProfile, value.policyProfile].map(p => [p.identity, p.version, p.sha256])]);
}

export function createReferenceAssembly<HostTransaction>(
  input: ReferenceAssemblyConfiguration,
  executor: Executor<HostTransaction>,
  services: {readonly recoveryRegistry: HostRecoveryRegistry;
    readonly feedProofVerifiers?: readonly FeedProofVerifierRegistration[];
    readonly requestNamespaceAuthority?: HostRequestNamespaceAuthority}
): AssemblyConstructionResult {
  const error = (code: 'invalid_configuration' | 'unsupported_profile' | 'incompatible_selection', path?: string): AssemblyConstructionResult =>
    Object.freeze({status: 'error', code, ...(path ? {path} : {}), diagnosticProfile: INERT_ASSEMBLY_PROFILE});
  const data = record(input);
  if (!data || !exact(data, ['interfaceVersion', 'assemblyId', 'assemblyProfile', 'recovery', 'databaseIdentity', 'schema', 'capabilities'], ['requestReplay'])
      || data.interfaceVersion !== 'truss-reference-assembly/0.1.0' || !text(data.assemblyId) || !text(data.databaseIdentity) || !text(data.schema)
      || !executor || typeof executor !== 'object') return error('invalid_configuration');
  const assemblyProfile = pin(data.assemblyProfile);
  if (!assemblyProfile || !same(assemblyProfile, INERT_ASSEMBLY_PROFILE)) return error('unsupported_profile', 'assemblyProfile');
  const recovery = record(data.recovery);
  const registryProfile = recovery && pin(recovery.registryProfile);
  if (!recovery || !exact(recovery, ['registryProfile', 'retention']) || !registryProfile
      || (recovery.retention !== 'process_lifetime' && recovery.retention !== 'restart_durable')) return error('invalid_configuration', 'recovery');
  const registry = own(services, 'recoveryRegistry');
  const actualRegistryProfile = pin(own(registry, 'profile'));
  if (!actualRegistryProfile || !same(registryProfile, actualRegistryProfile) || own(registry, 'retention') !== recovery.retention)
    return error('incompatible_selection', 'recovery');
  let requestReplay: ReferenceAssemblyConfiguration['requestReplay'];
  if (Object.hasOwn(data, 'requestReplay')) {
    const replay = record(data.requestReplay);
    const profile = replay && pin(replay.namespaceAuthorityProfile);
    const authority = own(services, 'requestNamespaceAuthority');
    const actual = pin(own(authority, 'profile'));
    if (!replay || !exact(replay, ['namespaceAuthorityProfile']) || !profile || !actual || !same(profile, actual))
      return error('incompatible_selection', 'requestReplay');
    requestReplay = Object.freeze({namespaceAuthorityProfile: profile});
  }
  if (!Array.isArray(data.capabilities) || data.capabilities.length < 1 || data.capabilities.length > 128)
    return error('invalid_configuration', 'capabilities');
  if (Reflect.ownKeys(data.capabilities).some(key => typeof key !== 'string' || (key !== 'length' && !/^(0|[1-9][0-9]*)$/.test(key))))
    return error('invalid_configuration', 'capabilities');
  const capabilities: CapabilitySelection[] = [];
  const keys = new Set<string>();
  for (let index = 0; index < data.capabilities.length; index++) {
    const value = selection(own(data.capabilities, String(index)));
    if (!value || keys.has(selectionKey(value))) return error('incompatible_selection', 'capabilities');
    keys.add(selectionKey(value)); capabilities.push(value);
  }
  const configuration: ReferenceAssemblyConfiguration = Object.freeze({
    interfaceVersion: 'truss-reference-assembly/0.1.0', assemblyId: data.assemblyId, assemblyProfile,
    recovery: Object.freeze({registryProfile, retention: recovery.retention}), databaseIdentity: data.databaseIdentity,
    schema: data.schema, capabilities: Object.freeze(capabilities) as readonly [CapabilitySelection, ...CapabilitySelection[]],
    ...(requestReplay ? {requestReplay} : {})
  });
  let disposed = false;
  const unavailable = () => ({status: 'unavailable' as const, reason: disposed ? 'disposed' as const : 'selection' as const});
  const disposal: AssemblyDisposalResult = Object.freeze({state: 'disposed', ownedResourcesReleased: true});
  const assembly: ReferenceAssembly = Object.freeze({configuration,
    directReads: unavailable, catalog: unavailable, groups: unavailable, mutations: unavailable,
    imports: unavailable, history: unavailable, feed: unavailable, compiledExecution: unavailable,
    async observeReadiness(request: CapabilitySelection): Promise<Outcome<CapabilityReadiness>> {
      const value = selection(request);
      if (disposed || !value || !keys.has(selectionKey(value))) return {status: 'error', error: {
        code: 'execution_obligation', retryScope: 'none', message: disposed ? 'Assembly disposed' : 'Selection not configured'}};
      // No native observer is implemented or invoked. Unverified is deliberate;
      // a valid configuration can never manufacture installed/available evidence.
      return {status: 'ok', value: Object.freeze({interfaceVersion: 'truss-capability-readiness/0.1.0', selection: value, state: 'unverified'})};
    },
    async dispose() {disposed = true; return disposal;}
  });
  return Object.freeze({status: 'ok', value: assembly});
}

/** CONTRACT-008 proposed native-output grammar only; caller admits field semantics. */
export type NativeVectorFamily = 'oidvector' | 'int2vector';
export interface NativeVectorLimits {
  readonly maxBytes: number;
  readonly maxTokens: number;
  readonly ledger?: NativeDecodeBudget;
}
export interface NativeVector {
  readonly family: NativeVectorFamily;
  readonly originalText: string;
  readonly tokens: readonly string[];
}
export class NativeVectorError extends Error {
  constructor(readonly code: 'output-grammar' | 'native-domain' | 'resource-limit' | 'count-correspondence') {
    super(code); this.name = 'NativeVectorError';
  }
}
/** ASCII grammar makes admitted byte count equal to code-unit count. No normalization. */
export function decodeNativeVector(family: NativeVectorFamily, text: string,
  limits: NativeVectorLimits, declaredCount?: string): NativeVector {
  if (family !== 'oidvector' && family !== 'int2vector') throw new NativeVectorError('output-grammar');
  if (typeof text !== 'string') throw new NativeVectorError('output-grammar');
  if (!Number.isSafeInteger(limits.maxBytes) || limits.maxBytes < 0 ||
      !Number.isSafeInteger(limits.maxTokens) || limits.maxTokens < 0 ||
      text.length > limits.maxBytes) throw new NativeVectorError('resource-limit');
  if (declaredCount !== undefined && (typeof declaredCount !== 'string' ||
      !/^(0|[1-9][0-9]*)$/.test(declaredCount))) throw new NativeVectorError('count-correspondence');
  // Bound count conversion independently: no unbounded bigint allocation.
  if (declaredCount !== undefined && (declaredCount.length > String(limits.maxTokens).length ||
      BigInt(declaredCount) > BigInt(limits.maxTokens))) throw new NativeVectorError('resource-limit');
  limits.ledger?.reserve(text.length, 1);
  const tokens: string[] = [];
  let start = 0;
  for (let end = 0; end <= text.length; end++) {
    if (end < text.length && text.charCodeAt(end) !== 32) continue;
    if (text.length === 0) break;
    if (tokens.length === limits.maxTokens) throw new NativeVectorError('resource-limit');
    const token = text.slice(start, end);
    const grammar = family === 'oidvector' ? /^(0|[1-9][0-9]*)$/ : /^(0|-?[1-9][0-9]*)$/;
    if (!grammar.test(token)) throw new NativeVectorError('output-grammar');
    // Reject oversized tokens before exact integer allocation.
    if (token.length > (family === 'oidvector' ? 10 : 6)) throw new NativeVectorError('native-domain');
    const value = BigInt(token);
    if (family === 'oidvector' ? value > 4294967295n : value < -32768n || value > 32767n)
      throw new NativeVectorError('native-domain');
    limits.ledger?.reserve(0, 1);
    tokens.push(token); start = end + 1;
  }
  if (declaredCount !== undefined && BigInt(declaredCount) !== BigInt(tokens.length))
    throw new NativeVectorError('count-correspondence');
  return Object.freeze({family, originalText: text, tokens: Object.freeze(tokens)});
}

export type NativeArrayElement = string | null | readonly NativeArrayElement[];
export type NativeArray = {readonly kind: 'native-null'; readonly originalText: null} |
  {readonly kind: 'array'; readonly originalText: string; readonly bounds: readonly (readonly [string,string])[];
   readonly elements: readonly NativeArrayElement[]};
export interface NativeArrayLimits {readonly maxBytes: number; readonly maxNodes: number; readonly maxDepth: number; readonly ledger?: NativeDecodeBudget}
/** Selected comma-delimited text element output. Type/ACL authority is independently admitted. */
export function decodeNativeTextArray(text: string | null, dimensions: string | null,
  limits: NativeArrayLimits): NativeArray {
  const refuse = (reason: string): never => {throw new Error('native-array:' + reason);};
  for (const n of [limits.maxBytes, limits.maxNodes, limits.maxDepth])
    if (!Number.isSafeInteger(n) || n < 0) refuse('resource-limit');
  if (limits.maxDepth > 6) refuse('resource-limit');
  if (text === null) {
    if (dimensions !== null) refuse('native-correspondence');
    return Object.freeze({kind: 'native-null', originalText: null});
  }
  if (typeof text !== 'string' || (dimensions !== null && typeof dimensions !== 'string')) refuse('grammar');
  let bytes = 0;
  // Validate scalar UTF-8 without replacement or allocating a second full carrier.
  for (let i=0; i<text.length; i++) {
    const c = text.charCodeAt(i);
    if (c === 0) refuse('grammar');
    if (c >= 0xd800 && c <= 0xdbff) {
      const low = text.charCodeAt(++i);
      if (!(low >= 0xdc00 && low <= 0xdfff)) refuse('grammar');
      bytes += 4;
    } else if (c >= 0xdc00 && c <= 0xdfff) refuse('grammar');
    else bytes += c < 128 ? 1 : c < 2048 ? 2 : 3;
    if (bytes > limits.maxBytes) refuse('resource-limit');
  }
  limits.ledger?.reserve(bytes, 0);
  const parseBounds = (source: string): [string,string][] => {
    if (source.length > 6 * 26) refuse('resource-limit');
    const result: [string,string][] = [];
    const re = /\[(-?(?:0|[1-9][0-9]*)):(-?(?:0|[1-9][0-9]*))\]/g;
    let used = 0;
    for (const m of source.matchAll(re)) {
      if (m.index !== used || result.length === 6) refuse('grammar');
      for (const s of [m[1],m[2]]) {
        if (s === '-0' || s.length > 11) refuse('grammar');
        const n = BigInt(s);
        if (n < -2147483648n || n > 2147483647n) refuse('native-domain');
      }
      if (BigInt(m[2]) < BigInt(m[1])) refuse('native-correspondence');
      result.push([m[1],m[2]]); used += m[0].length;
    }
    if (!result.length || used !== source.length) refuse('grammar');
    return result;
  };
  let offset = 0;
  let prefix: [string,string][] | undefined;
  if (text.startsWith('[')) {
    const end = text.indexOf('=');
    if (end < 0 || end > 6*26) refuse('grammar');
    prefix = parseBounds(text.slice(0,end)); offset = end+1;
  }
  let nodes = 0;
  const node = () => {if (++nodes > limits.maxNodes) refuse('resource-limit'); limits.ledger?.reserve(0, 1);};
  const array = (depth: number): readonly NativeArrayElement[] => {
    node();
    if (depth > limits.maxDepth) refuse('resource-limit');
    if (text[offset++] !== '{') refuse('grammar');
    const values: NativeArrayElement[] = [];
    if (text[offset] === '}') {offset++; return Object.freeze(values);}
    while (true) {
      if (text[offset] === '{') values.push(array(depth+1));
      else {
        node(); let value = ''; let escaped = false;
        const quoted = text[offset] === '"';
        if (quoted) {
          offset++; let closed = false;
          while (offset < text.length) {
            let c = text[offset++];
            if (c === '"') {closed = true; break;}
            if (c === '\\') {if (offset === text.length) refuse('grammar'); c = text[offset++];}
            value += c;
          }
          if (!closed) refuse('grammar');
        } else {
          while (offset < text.length && text[offset] !== ',' && text[offset] !== '}') {
            let c = text[offset++];
            if (c === '\\') {escaped = true; if (offset === text.length) refuse('grammar'); c = text[offset++];}
            else if (c === '{' || c === '"' || /\s/.test(c)) refuse('grammar');
            value += c;
          }
          if (!value.length) refuse('grammar');
        }
        values.push(!quoted && !escaped && value === 'NULL' ? null : value);
      }
      const separator = text[offset++];
      if (separator === '}') break;
      if (separator !== ',') refuse('grammar');
    }
    return Object.freeze(values);
  };
  const elements = array(1);
  if (offset !== text.length) refuse('grammar');
  const shape = (items: readonly NativeArrayElement[]): number[] => {
    if (!items.length) return [0];
    const nested = Array.isArray(items[0]);
    let child: number[] = [];
    for (const item of items) {
      if (Array.isArray(item) !== nested) refuse('native-correspondence');
      if (Array.isArray(item)) {
        const next = shape(item);
        if (next.includes(0)) refuse('native-correspondence');
        if (child.length && (child.length !== next.length || child.some((n,i)=>n!==next[i]))) refuse('native-correspondence');
        child = next;
      }
    }
    return [items.length,...child];
  };
  const sizes = shape(elements);
  const bounds = dimensions === null ? [] : parseBounds(dimensions);
  if (!elements.length) {
    if (bounds.length || prefix) refuse('native-correspondence');
  } else {
    if (bounds.length !== sizes.length) refuse('native-correspondence');
    for (let i=0;i<sizes.length;i++) {
      if (BigInt(bounds[i][1])-BigInt(bounds[i][0])+1n !== BigInt(sizes[i])) refuse('native-correspondence');
      if (prefix ? prefix[i]?.[0] !== bounds[i][0] || prefix[i]?.[1] !== bounds[i][1] : bounds[i][0] !== '1')
        refuse('native-correspondence');
    }
    if (prefix && prefix.length !== bounds.length) refuse('native-correspondence');
  }
  return Object.freeze({kind:'array',originalText:text,bounds:Object.freeze(bounds.map(b=>Object.freeze(b))),elements});
}

export interface NativeTriggerArguments {
  readonly count: string; readonly byteLength: string; readonly originalHex: string;
  readonly encoding: 'UTF8'; readonly arguments: readonly string[];
}
/** CONTRACT-008 exact tgargs framing. No trigger definition or callable authority inferred. */
export function decodeNativeTriggerArguments(count: string, hex: string | null,
  byteLength: string | null, limits: {readonly maxBytes: number; readonly maxArguments: number},
  encoding: 'UTF8'): NativeTriggerArguments {
  const refuse = (why: string): never => {throw new Error('trigger-arguments:' + why);};
  if (encoding !== 'UTF8') refuse('encoding');
  if (hex === null || byteLength === null) refuse('native-null');
  if (typeof count !== 'string' || !/^(0|[1-9][0-9]*)$/.test(count) || count.length > 5 || BigInt(count) > 32767n) refuse('count');
  for (const n of [limits.maxBytes,limits.maxArguments])
    if (!Number.isSafeInteger(n) || n < 0) refuse('resource-limit');
  if (typeof byteLength !== 'string' || !/^(0|[1-9][0-9]*)$/.test(byteLength)) refuse('byte-length');
  // Bound exact conversion and backing allocation before reading hex bytes.
  if (byteLength!.length > String(limits.maxBytes).length || BigInt(byteLength!) > BigInt(limits.maxBytes) ||
      BigInt(count) > BigInt(limits.maxArguments)) refuse('resource-limit');
  const bytesCount = Number(BigInt(byteLength!)); // admitted allocation length; not a stored native value
  if (typeof hex !== 'string' || hex.length % 2 || !/^[0-9a-f]*$/.test(hex)) refuse('hex-domain');
  if (BigInt(hex!.length) !== BigInt(byteLength!)*2n) refuse('byte-length');
  if (count === '0' && bytesCount !== 0) refuse('count');
  const bytes = new Uint8Array(bytesCount);
  for(let i=0;i<bytesCount;i++) bytes[i] = parseInt(hex!.slice(i*2,i*2+2),16);
  // ignoreBOM retains U+FEFF as actual argument data, rather than stripping it.
  const decoder = new TextDecoder('utf-8',{fatal:true,ignoreBOM:true});
  const arguments_: string[] = [];
  let start = 0;
  for(let i=0;i<bytesCount;i++) {
    if(bytes[i] !== 0) continue;
    if(BigInt(arguments_.length) === BigInt(count)) refuse('count');
    let value: string;
    try {value = decoder.decode(bytes.subarray(start,i));} catch {return refuse('encoding');}
    arguments_.push(value); start = i+1;
  }
  if(start !== bytesCount) refuse('termination');
  if(BigInt(arguments_.length) !== BigInt(count)) refuse('count');
  return Object.freeze({count,byteLength:byteLength!,originalHex:hex!,encoding,arguments:Object.freeze(arguments_)});
}

export interface NativeRoutineCarrier {
  readonly originalCatalogRowJson: string;
  readonly inputCount: string;
  readonly inputTypesText: string;
  readonly inputTypesDimensions: string;
  readonly names: {readonly text: string|null; readonly dimensions: string|null; readonly rawJson: string};
  readonly modes: {readonly text: string|null; readonly dimensions: string|null; readonly rawJson: string};
  readonly settings: {readonly text: string|null; readonly dimensions: string|null; readonly rawJson: string};
}
/** Composition of selected carrier codecs; full raw row is opaque custody, not accepted semantics. */
export function decodeNativeRoutineCarriers(input: NativeRoutineCarrier,
  limits: NativeArrayLimits & {readonly maxTokens:number}): {
    readonly originalCatalogRowJson:string; readonly inputTypes:NativeVector;
    readonly names:NativeArray; readonly modes:NativeArray; readonly settings:NativeArray;
  } {
  const fail = ():never=>{throw new Error('routine-carriers:native-correspondence');};
  if(typeof input.originalCatalogRowJson!=='string' || input.originalCatalogRowJson.length>limits.maxBytes) fail();
  limits.ledger?.reserve(nativeScalarByteLength(input.originalCatalogRowJson), 1);
  if(!/^(0|[1-9][0-9]*)$/.test(input.inputCount) || input.inputCount.length>5 || BigInt(input.inputCount)>32767n) fail();
  const inputTypes=decodeNativeVector('oidvector',input.inputTypesText,limits,input.inputCount);
  const upper=(BigInt(input.inputCount)-1n).toString();
  if(input.inputTypesDimensions!==`[0:${upper}]`) fail();
  const decode = (carrier:NativeRoutineCarrier['names']):NativeArray=>{
    const array=decodeNativeTextArray(carrier.text,carrier.dimensions,limits);
    if(typeof carrier.rawJson!=='string' || carrier.rawJson.length>limits.maxBytes) fail();
    limits.ledger?.reserve(nativeScalarByteLength(carrier.rawJson), 1);
    let raw:unknown;
    try{raw=JSON.parse(carrier.rawJson);}catch{return fail();}
    // This profile only interprets text leaves; original native row remains untouched.
    const expected=array.kind==='native-null'?null:array.elements;
    if(JSON.stringify(raw)!==JSON.stringify(expected)) fail();
    if(array.kind==='array' && array.bounds.length!==1 && array.elements.length) fail();
    return array;
  };
  return Object.freeze({originalCatalogRowJson:input.originalCatalogRowJson,inputTypes,
    names:decode(input.names),modes:decode(input.modes),settings:decode(input.settings)});
}


/** Aggregate decode-accounting subset; transport/deadline/containment remain separate. */
export class NativeDecodeBudget {
  #remainingBytes: number; #remainingNodes: number; #exhausted = false;
  constructor(readonly maxBytes: number, readonly maxNodes: number) {
    if (![maxBytes,maxNodes].every(n=>Number.isSafeInteger(n)&&n>=0)) throw new Error('native-budget:invalid');
    this.#remainingBytes=maxBytes; this.#remainingNodes=maxNodes; Object.freeze(this);
  }
  reserve(bytes: number, nodes: number): void {
    if(this.#exhausted) throw new Error('native-budget:exhausted');
    if(![bytes,nodes].every(n=>Number.isSafeInteger(n)&&n>=0) ||
       bytes>this.#remainingBytes || nodes>this.#remainingNodes) {
      this.#exhausted=true; throw new Error('native-budget:exhausted');
    }
    this.#remainingBytes-=bytes; this.#remainingNodes-=nodes;
  }
  get remaining(): {readonly bytes:number;readonly nodes:number;readonly exhausted:boolean} {
    return Object.freeze({bytes:this.#remainingBytes,nodes:this.#remainingNodes,exhausted:this.#exhausted});
  }
}
function nativeScalarByteLength(text:string):number {
  let bytes=0;
  for(let i=0;i<text.length;i++) {
    const c=text.charCodeAt(i);
    if(c>=0xd800&&c<=0xdbff){const low=text.charCodeAt(++i);
      if(!(low>=0xdc00&&low<=0xdfff))throw new Error('native-budget:invalid-scalar'); bytes+=4;
    } else if(c>=0xdc00&&c<=0xdfff)throw new Error('native-budget:invalid-scalar');
    else bytes+=c<128?1:c<2048?2:3;
  }
  return bytes;
}

/** Host must retain original native attempt and quarantine uncertain resources. */
export interface NativeConnection {
  begin(options:TransactionOptions):Promise<void>;
  execute(statement:Statement):Promise<StatementResult>;
  control(sql:string):Promise<void>;
  commit():Promise<'committed'|{readonly status:'rejected';readonly sqlState:string}>;
  rollback():Promise<'rolled_back'>;
  release():Promise<void>;
  quarantine(reason:'commit_unknown'|'transaction_unusable'):Promise<void>;
}
export interface NativeConnectionSource {acquire():Promise<NativeConnection>}
type Entry={connection:NativeConnection;live:boolean;busy:boolean;failed:boolean;nativeFailure?:ExecutionFailure;savepoints:SavepointHandle[]};
const failure=(code:ExecutionFailure['code']):Outcome<never>=>({status:'error',error:code==='retry'?{code,message:code,retryScope:'whole_transaction'}:{code,message:code,retryScope:'none'}});
/** Engine-owned executor composition. Caller adoption deliberately refuses until native custody is implemented. */
export function createEngineExecutor(source:NativeConnectionSource):Executor<never> {
  const entries=new WeakMap<TransactionHandle,Entry>();
  const points=new WeakMap<SavepointHandle,{entry:Entry;name:string}>();
  let sequence=0n;
  const call=async<T>(handle:TransactionHandle,fn:(entry:Entry)=>Promise<T>,containment=false):Promise<Outcome<T>>=>{
    const entry=entries.get(handle);
    if(!entry||!entry.live||entry.busy||(entry.failed&&(!containment||entry.nativeFailure?.code==='retry')))return failure('invalid_transaction');
    entry.busy=true;
    try{return {status:'ok',value:await fn(entry)};}
    catch(error){
      entry.failed=true;
      const code = error && typeof error==='object' ? Object.getOwnPropertyDescriptor(error,'code')?.value : undefined;
      const sqlState=typeof code==='string'&&/^[0-9A-Z]{5}$/.test(code)?code:undefined;
      entry.nativeFailure = sqlState==='40001'||sqlState==='40P01'
        ? {code:'retry',message:'Native transaction must retry',retryScope:'whole_transaction',sqlState}
        : {code:'transaction_unusable',message:'Native execution failed',retryScope:'none',...(sqlState?{sqlState}:{})};
      return {status:'error',error:entry.nativeFailure};
    }
    finally{entry.busy=false;}
  };
  return {
    async adoptTransaction(){return failure('execution_obligation');},
    async withTransaction<T>(options:TransactionOptions,callback:(t:TransactionHandle)=>Promise<T>) {
      if(!['read_committed','repeatable_read','serializable'].includes(options.isolation)||
         !['read_only','read_write'].includes(options.accessMode)||options.cancellation)return failure('execution_obligation');
      let connection:NativeConnection;
      try{connection=await source.acquire();}catch{return failure('transaction_unusable');}
      let entry:Entry|undefined;
      const quarantine=async(reason:'commit_unknown'|'transaction_unusable')=>{
        if(entry)entry.live=false;
        try{await connection.quarantine(reason);}catch{/* Original resource must remain held by the host source. */}
        return failure(reason);
      };
      try{await connection.begin(options);}catch{return quarantine('transaction_unusable');}
      // The canonical brand's runtime authority is this issuer's WeakMap, never a caller cast.
      const handle=Object.freeze({ownership:'engine',isolation:options.isolation,accessMode:options.accessMode}) as TransactionHandle;
      entry={connection,live:true,busy:false,failed:false,savepoints:[]}; entries.set(handle,entry);
      let value:T;
      try{value=await callback(handle);}
      catch(original){
        entry.live=false;
        if(entry.busy)return quarantine('transaction_unusable');
        try{if(await connection.rollback()!=='rolled_back')return quarantine('transaction_unusable');}
        catch{return quarantine('transaction_unusable');}
        try{await connection.release();}catch{return quarantine('transaction_unusable');}
        throw original;
      }
      entry.live=false;
      if(entry.busy)return quarantine('transaction_unusable');
      if(entry.failed){
        try{if(await connection.rollback()!=='rolled_back')return quarantine('transaction_unusable');await connection.release();}
        catch{return quarantine('transaction_unusable');}
        return entry.nativeFailure ? {status:'error' as const,error:entry.nativeFailure} : failure('transaction_unusable');
      }
      try{
        const settlement=await connection.commit();
        if(settlement!=='committed'){
          if(settlement.status!=='rejected'||! /^(23|40)[0-9A-Z]{3}$/.test(settlement.sqlState))return quarantine('commit_unknown');
          // Rejection port requires original server ErrorResponse plus confirmed rollback.
          try{await connection.release();}catch{return quarantine('transaction_unusable');}
          return {status:'error' as const,error:settlement.sqlState==='40001'||settlement.sqlState==='40P01'
            ? {code:'retry' as const,message:'Native commit rejected',retryScope:'whole_transaction' as const,sqlState:settlement.sqlState}
            : {code:'transaction_unusable' as const,message:'Native commit rejected',retryScope:'none' as const,sqlState:settlement.sqlState}};
        }
      }catch{return quarantine('commit_unknown');}
      // Cleanup failure cannot cause a retry of an already confirmed commit.
      try{await connection.release();}catch{return quarantine('transaction_unusable');}
      return {status:'ok' as const,value:{value,durability:'committed' as const}};
    },
    execute(handle,statement){return call(handle,async entry=>{
      if(typeof statement.sql!=='string'||!statement.sql.length)throw Error('invalid statement');
      const parameters=statement.parameters.map((p,i)=>{
        if(p.position!==i+1||!['null','text','integer','decimal','boolean','json'].includes(p.carrier))throw Error('invalid parameter');
        if(p.carrier==='null'){if('text'in p)throw Error('invalid null');}
        else {
          if(typeof p.text!=='string')throw Error('invalid text');
          if(p.carrier==='integer'&&!/^-?(0|[1-9][0-9]*)$/.test(p.text))throw Error('invalid integer');
          if(p.carrier==='decimal'&&!/^-?(0|[1-9][0-9]*)(\.[0-9]+)?$/.test(p.text))throw Error('invalid decimal');
          if(p.carrier==='boolean'&&p.text!=='true'&&p.text!=='false')throw Error('invalid boolean');
          // Syntax check only: retain and transmit the original JSON text, never the decoded tree.
          if(p.carrier==='json'){try{JSON.parse(p.text);}catch{throw Error('invalid JSON');}}
        }
        return Object.freeze({...p});
      });
      const result=await entry.connection.execute(Object.freeze({sql:statement.sql,parameters:Object.freeze(parameters)}));
      if(!/^(0|[1-9][0-9]*)$/.test(result.affectedRows)||typeof result.command!=='string'||result.columns.some(c=>typeof c!=='string'))throw Error('invalid result');
      const rows=result.rows.map(row=>{
        if(row.length!==result.columns.length)throw Error('row width');
        return Object.freeze(row.map(cell=>{
          if(cell.state==='null')return Object.freeze({state:'null' as const});
          if(cell.state!=='text'||typeof cell.text!=='string')throw Error('non-text cell');
          return Object.freeze({state:'text' as const,text:cell.text});
        }));
      });
      return Object.freeze({columns:Object.freeze([...result.columns]),rows:Object.freeze(rows),affectedRows:result.affectedRows,command:result.command});
    });},
    savepoint(handle){return call(handle,async entry=>{
      const name='truss_sp_'+(++sequence).toString();
      await entry.connection.control('SAVEPOINT '+name);
      const point=Object.freeze({}) as SavepointHandle;
      points.set(point,{entry,name});entry.savepoints.push(point);return point;
    });},
    rollbackToSavepoint(handle,point){return call(handle,async entry=>{
      const found=points.get(point);const index=entry.savepoints.indexOf(point);
      if(!found||found.entry!==entry||index<0)throw Error('invalid savepoint');
      await entry.connection.control('ROLLBACK TO SAVEPOINT '+found.name);
      entry.savepoints.splice(index+1);entry.failed=false;entry.nativeFailure=undefined;
    },true);},
    releaseSavepoint(handle,point){return call(handle,async entry=>{
      const found=points.get(point);const index=entry.savepoints.indexOf(point);
      if(!found||found.entry!==entry||index<0)throw Error('invalid savepoint');
      await entry.connection.control('RELEASE SAVEPOINT '+found.name);entry.savepoints.splice(index);
    });}
  };
}
