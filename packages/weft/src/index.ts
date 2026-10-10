/** Browser-compatible compiler/host boundary. No SQL compiler or database ownership. */
export const WEFT_SOURCE = 'f05f2df09e9c2494ac8c6d703dfe38413dbc4181';
export interface Compiler { compileJson(request: string): string | Promise<string> }
export type Json = null | boolean | number | string | Json[] | {[key: string]: Json};
export interface ModelModule {
  documentJson: string;
  pin: {documentId: string; revision: string; umfVersion: '0.7.0'; sha256: string};
  selectedModuleIds: readonly string[];
}
export interface BindingInput {
  bindingJson: string;
  bindingSha256: string;
  backendVersion: string;
  targetProfile: string;
  modules: readonly ModelModule[];
}
export interface Obligation { id: string; owner: string; failureCode: string; parameters: Json }
export interface Artifact {
  interfaceVersion: string; status: 'compiled'; compilerVersion: string; dialect: string;
  backend: {backendId: string; backendVersion: string; targetProfile: string};
  bindingSha256: string; modelPins: readonly ModelModule['pin'][];
  sql: string; parameters: readonly {position: number; logicalType: Json; value: string; origin: Json}[];
  columns: readonly Json[]; obligations: readonly Obligation[]; [key: string]: unknown;
}
export interface Plan { readonly artifact: Artifact; readonly originalResponse: string }
export interface Scope {
  /** Implemented by the original native host: one affine, authorized read context. */
  verifyContext(artifact: Artifact): Promise<void>;
  query(sql: string, parameters: readonly string[]): Promise<readonly (readonly (string | null)[])[]>;
}
export interface Handler {
  /** Admit the complete original parameter grammar; unknown meaning must return false. */
  accepts(obligation: Obligation, artifact: Artifact): boolean;
  /** Run required checks in the same original Scope before data SQL. Throw on failure. */
  check(scope: Scope, obligation: Obligation, artifact: Artifact): Promise<void>;
}
export interface Host {
  /** Must buffer private results and retain the same context through publication recheck. */
  withReadContext<T>(body: (scope: Scope) => Promise<T>): Promise<T>;
  handlers: Readonly<Record<string, Handler>>;
  /** Owner-qualified exact decoder; no generic JSON/number/Date conversion. */
  decode(artifact: Artifact, rows: readonly (readonly (string | null)[])[]): Promise<readonly Json[]>;
}
export class QueryRefusal extends Error {
  constructor(readonly code: string, message: string) { super(message); this.name = 'QueryRefusal' }
}
function refuse(code: string, message: string): never { throw new QueryRefusal(code, message) }
function text(value: unknown, max: number): asserts value is string {
  if (typeof value !== 'string' || value.length > max) refuse('input', 'Bounded scalar text required');
  for (let i=0;i<value.length;i++) {
    const c=value.charCodeAt(i);
    if(c>=0xd800&&c<=0xdbff) {const next=value.charCodeAt(++i);if(!(next>=0xdc00&&next<=0xdfff))refuse('input','Unpaired surrogate')}
    else if(c>=0xdc00&&c<=0xdfff)refuse('input','Unpaired surrogate');
  }
}
async function sha256(value: string): Promise<string> {
  const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value));
  return Array.from(new Uint8Array(bytes),v=>v.toString(16).padStart(2,'0')).join('');
}
function immutable<T>(value: T): T {
  if(value && typeof value==='object') {for(const child of Object.values(value))immutable(child);Object.freeze(value)}
  return value;
}
function canonical(value: any): string {
  if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
  if(value!==null&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
  return JSON.stringify(value);
}
const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;
/** Trusted host supplies original owner binding bytes. Rust performs full binding semantics. */
export async function createQueryEngine(compiler: Compiler, input: BindingInput, host?: Host) {
  const compileJson=compiler.compileJson.bind(compiler);
  const withReadContext=host?.withReadContext.bind(host),decode=host?.decode.bind(host);
  const registered=host ? Object.freeze(Object.fromEntries(Object.entries(host.handlers).map(([id,h])=>
    [id,Object.freeze({accepts:h.accepts.bind(h),check:h.check.bind(h)})]))) : undefined;
  let disposed=false;
  const admitting=()=>{if(disposed)refuse('disposed','Query engine disposed')};
  const binding=immutable(clone(input));
  text(binding.bindingJson,4_194_304);
  if(await sha256(binding.bindingJson)!==binding.bindingSha256)refuse('binding_pin','Binding bytes/hash mismatch');
  if(!binding.backendVersion || !binding.targetProfile)refuse('profile','Explicit backend/profile required');
  if(binding.modules.length<1||binding.modules.length>32)refuse('model','Model bundle outside limits');
  for(const module of binding.modules) {
    text(module.documentJson,4_194_304);
    if(await sha256(module.documentJson)!==module.pin.sha256)refuse('model_pin','Original module bytes/hash mismatch');
  }
  const plans=new WeakSet<object>();
  return Object.freeze({
    /** Closes new work/publication; original host still owns in-flight settlement and cleanup. */
    dispose(): void {disposed=true},
    async compile(sql: string, parameters: Readonly<Record<string, {family: string; value: string}>> = {}): Promise<Plan> {
      admitting();text(sql,262_144);
      const request={interfaceVersion:'weft-compile/0.2.0',dialect:'weft-sql/0.2.0',sql,
        modules:binding.modules,target:{backendId:'truss.postgresql',backendVersion:binding.backendVersion,
          targetProfile:binding.targetProfile,bindingJson:binding.bindingJson,bindingSha256:binding.bindingSha256},
        options:{allowCandidate:false},parameters:clone(parameters)};
      const response=await compileJson(JSON.stringify(request));admitting();text(response,8_388_608);
      let value: any;try {value=JSON.parse(response)}catch {refuse('compiler','Malformed compiler response')}
      if(value.status!=='compiled')refuse('compiler_blocked',response);
      if(value.interfaceVersion!=='weft-compile/0.2.0'||value.dialect!=='weft-sql/0.2.0'||
        value.backend?.backendId!=='truss.postgresql'||value.backend?.backendVersion!==binding.backendVersion||
        value.backend?.targetProfile!==binding.targetProfile||value.bindingSha256!==binding.bindingSha256||
        canonical(value.modelPins)!==canonical(binding.modules.map(m=>m.pin)))
          refuse('artifact_pin','Compiler artifact context drift');
      if(typeof value.sql!=='string'||!Array.isArray(value.parameters)||!Array.isArray(value.columns)||!Array.isArray(value.obligations))
        refuse('compiler','Incomplete artifact');
      // This wrapper admits only the original 0.2 response domain. New positional
      // carriers cannot be smuggled through an old version or a permissive host.
      if(value.columns.some((column:any)=>column&&typeof column==='object'&&Object.hasOwn(column,'carrierName'))||
         value.obligations.some((obligation:any)=>obligation?.id==='weft.output.positioned'))
        refuse('artifact_version','Positional output metadata requires an explicitly admitted Weft 0.3 profile');
      value.parameters.forEach((p:any,i:number)=>{if(p.position!==i+1||typeof p.value!=='string')refuse('parameter','Non-exact parameter transport')});
      const plan=immutable({artifact:value as Artifact,originalResponse:response});plans.add(plan);return plan;
    },
    async execute(plan: Plan): Promise<readonly Json[]> {
      admitting();if(!plans.has(plan))refuse('plan','Foreign or substituted query plan');
      if(!host)refuse('runtime_unavailable','Original native query host not installed');
      const artifact=plan.artifact;
      const selected=artifact.obligations.map(o=>{
        if(o.owner!=='host'||typeof o.id!=='string')refuse('obligation','Unsupported obligation owner');
        const handler=Object.hasOwn(registered!,o.id)?registered![o.id]:undefined;
        if(!handler||!handler.accepts(o,artifact))refuse('obligation','Unknown obligation meaning: '+o.id);
        return {obligation:o,handler};
      });
      const result=await withReadContext!(async scope=>{
        admitting();await scope.verifyContext(artifact);admitting();
        for(const entry of selected){await entry.handler.check(scope,entry.obligation,artifact);admitting()}
        const rows=await scope.query(artifact.sql,artifact.parameters.map(p=>p.value));
        if(rows.some(row=>row.length!==artifact.columns.length||row.some(v=>v!==null&&typeof v!=='string')))
          refuse('transport','Result cells must retain exact text/null shape');
        admitting();const decoded=await decode!(artifact,rows);
        await scope.verifyContext(artifact);
        const rejectNumeric=(v: unknown):void=>{
          if(typeof v==='number')refuse('decoder','Decoded stored values must use exact carriers, not JavaScript numbers');
          if(v&&typeof v==='object')for(const child of Object.values(v))rejectNumeric(child);
        };
        admitting();rejectNumeric(decoded);
        return immutable(clone(decoded));
      });
      admitting();return result;
    }
  });
}


export interface OwnerBindingComposition {
  /** Complete owner-produced binding graph; original source/definition artifacts remain embedded. */
  binding: Readonly<Record<string, Json>>;
  modules: readonly ModelModule[];
  backendVersion: string;
  targetProfile: string;
}
/** Serialize a trusted owner's original composition; never allocate IDs or infer storage homes. */
export async function serializeStorageBinding(source: OwnerBindingComposition): Promise<BindingInput> {
  const original=clone(source);
  const binding=original.binding;
  if(binding.interfaceVersion!=='truss-postgresql-binding/0.1.0')refuse('binding','Unsupported owner binding grammar');
  for(const key of ['basis','entities','properties','keys','relationships','executionObligations'])
    if(!Object.hasOwn(binding,key))refuse('binding','Missing original owner composition: '+key);
  const basis=binding.basis as any;
  if(typeof basis?.catalogRevision!=='string'||!/^([1-9][0-9]*)$/.test(basis.catalogRevision))
    refuse('catalog','Positive original accepted catalog revision required; fixture/genesis IDs are not acceptance');
  let bytes=0,artifacts=0;
  const visit=async(value: any):Promise<void>=>{
    if(!value||typeof value!=='object')return;
    if(Object.hasOwn(value,'bytesBase64')) {
      if(typeof value.identity!=='string'||!value.identity||typeof value.bytesBase64!=='string'||typeof value.sha256!=='string')
        refuse('binding_artifact','Incomplete original artifact');
      let decoded:string;try{decoded=atob(value.bytesBase64)}catch{refuse('binding_artifact','Malformed artifact base64')}
      bytes+=decoded.length;artifacts++;
      if(bytes>4_194_304||artifacts>4096)refuse('resource','Original binding artifact budget exceeded');
      const raw=Uint8Array.from(decoded,c=>c.charCodeAt(0));
      const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),v=>v.toString(16).padStart(2,'0')).join('');
      if(digest!==value.sha256)refuse('binding_artifact','Original artifact hash mismatch');
    }
    for(const child of Object.values(value))await visit(child);
  };
  await visit(binding);
  const bindingJson=JSON.stringify(binding);text(bindingJson,4_194_304);
  return immutable({bindingJson,bindingSha256:await sha256(bindingJson),modules:original.modules,
    backendVersion:original.backendVersion,targetProfile:original.targetProfile});
}
