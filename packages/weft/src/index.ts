/** Browser-compatible compiler/host boundary. No SQL compiler or database ownership. */
export const WEFT_SOURCE = '2744531735c2a771fbe7ed24a7f67e3afc851b25';
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
  const registered=host ? Object.freeze(Object.fromEntries(Object.entries(host.handlers).map(([id,h])=>
    [id,Object.freeze({accepts:h.accepts.bind(h),check:h.check.bind(h)})]))) : undefined;
  return Object.freeze({
    async compile(sql: string, parameters: Readonly<Record<string, {family: string; value: string}>> = {}): Promise<Plan> {
      text(sql,262_144);
      const request={interfaceVersion:'weft-compile/0.2.0',dialect:'weft-sql/0.2.0',sql,
        modules:binding.modules,target:{backendId:'truss.postgresql',backendVersion:binding.backendVersion,
          targetProfile:binding.targetProfile,bindingJson:binding.bindingJson,bindingSha256:binding.bindingSha256},
        options:{allowCandidate:false},parameters:clone(parameters)};
      const response=await compiler.compileJson(JSON.stringify(request));text(response,8_388_608);
      let value: any;try {value=JSON.parse(response)}catch {refuse('compiler','Malformed compiler response')}
      if(value.status!=='compiled')refuse('compiler_blocked',response);
      if(value.interfaceVersion!=='weft-compile/0.2.0'||value.dialect!=='weft-sql/0.2.0'||
        value.backend?.backendId!=='truss.postgresql'||value.backend?.backendVersion!==binding.backendVersion||
        value.backend?.targetProfile!==binding.targetProfile||value.bindingSha256!==binding.bindingSha256||
        canonical(value.modelPins)!==canonical(binding.modules.map(m=>m.pin)))
          refuse('artifact_pin','Compiler artifact context drift');
      if(typeof value.sql!=='string'||!Array.isArray(value.parameters)||!Array.isArray(value.columns)||!Array.isArray(value.obligations))
        refuse('compiler','Incomplete artifact');
      value.parameters.forEach((p:any,i:number)=>{if(p.position!==i+1||typeof p.value!=='string')refuse('parameter','Non-exact parameter transport')});
      const plan=immutable({artifact:value as Artifact,originalResponse:response});plans.add(plan);return plan;
    },
    async execute(plan: Plan): Promise<readonly Json[]> {
      if(!plans.has(plan))refuse('plan','Foreign or substituted query plan');
      if(!host)refuse('runtime_unavailable','Original native query host not installed');
      const artifact=plan.artifact;
      const selected=artifact.obligations.map(o=>{
        if(o.owner!=='host'||typeof o.id!=='string')refuse('obligation','Unsupported obligation owner');
        const handler=Object.hasOwn(registered!,o.id)?registered![o.id]:undefined;
        if(!handler||!handler.accepts(o,artifact))refuse('obligation','Unknown obligation meaning: '+o.id);
        return {obligation:o,handler};
      });
      return host.withReadContext(async scope=>{
        await scope.verifyContext(artifact);
        for(const entry of selected)await entry.handler.check(scope,entry.obligation,artifact);
        const rows=await scope.query(artifact.sql,artifact.parameters.map(p=>p.value));
        if(rows.some(row=>row.length!==artifact.columns.length||row.some(v=>v!==null&&typeof v!=='string')))
          refuse('transport','Result cells must retain exact text/null shape');
        const decoded=await host.decode(artifact,rows);
        await scope.verifyContext(artifact);
        const rejectNumeric=(v: unknown):void=>{
          if(typeof v==='number')refuse('decoder','Decoded stored values must use exact carriers, not JavaScript numbers');
          if(v&&typeof v==='object')for(const child of Object.values(v))rejectNumeric(child);
        };
        rejectNumeric(decoded);
        return immutable(clone(decoded));
      });
    }
  });
}
