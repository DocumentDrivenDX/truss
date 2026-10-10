/** Experimental actual-owner IR consumer. A packet is not authority: registered
 * compiler provenance, native mapping/cut and final-release guard are host duties. */
import {lowerSecurityRowPredicate,type SecurityPhysicalType} from './security-predicate';
import {lowerSecuritySourceCompleteness} from './security-source-completeness';
const issuedPrograms=new WeakSet<object>();
const fail=():never=>{throw Error('TRUSS_SECURITY_QUERY_USE_UNSUPPORTED');};
const key=(v:any)=>JSON.stringify([v.documentId,v.moduleId??v.module,v.elementId??v.element]);
const ident=(v:unknown)=>{if(typeof v!=='string'||!v||v.includes('\0')||new TextEncoder().encode(v).length>63||[...v].some(c=>{const n=c.codePointAt(0)!;return n>=0xd800&&n<=0xdfff;}))return fail();return '"'+v.replaceAll('"','""')+'"';};
export async function lowerSecurityOriginalUseProgram(input:{handoff:any;expectedHandoffSha256:string;bindingJson:string;ontologyJson:string;queryProfileJson:string;expectedProfileSha256:string;target:SecurityPhysicalType['type'];subject:SecurityPhysicalType['type'];types:readonly SecurityPhysicalType[];home:{schema:string;table:string;fields:{ref:SecurityPhysicalType['type'];column:string;family:'string'|'integer';protected:boolean}[]}}){
 const original=structuredClone(input),{handoff,target,subject,types,home}=original;
 if(!/^[0-9a-f]{64}$/.test(original.expectedProfileSha256)||handoff.version!=='weft.security.mapping-handoff/0.2.0'||handoff.profile.sha256!==original.expectedProfileSha256)return fail();
 if(typeof original.bindingJson!=='string'||new TextEncoder().encode(original.bindingJson).length>4000000)return fail();
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(original.bindingJson))),b=>b.toString(16).padStart(2,'0')).join('');
 if(digest!==handoff.binding.sha256)return fail();
 const binding=JSON.parse(original.bindingJson);
 const canonical=(v:any):any=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
 if(binding.version!=='truss.security.raw-query-home/0.2.0'||Object.keys(binding).some(k=>!['version','target','subject','types','home'].includes(k))||JSON.stringify(canonical(binding.target))!==JSON.stringify(canonical(target))||JSON.stringify(canonical(binding.home))!==JSON.stringify(canonical(home)))return fail();
 if(JSON.stringify(canonical(binding.subject))!==JSON.stringify(canonical(subject))||JSON.stringify(canonical(binding.types))!==JSON.stringify(canonical(types)))return fail();
 const sourceHash=async(v:unknown)=>{
  if(typeof v!=='string'||new TextEncoder().encode(v).length>4000000)return fail();
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(v))),b=>b.toString(16).padStart(2,'0')).join('');
 };
 if(!/^[0-9a-f]{64}$/.test(original.expectedHandoffSha256)||await sourceHash(JSON.stringify(canonical(handoff)))!==original.expectedHandoffSha256)return fail();
 if(await sourceHash(original.ontologyJson)!==handoff.ontologySha256||await sourceHash(original.queryProfileJson)!==handoff.profile.sha256)return fail();
 const ontology=JSON.parse(original.ontologyJson),profile=JSON.parse(original.queryProfileJson);
 if(profile.ontologySha256!==handoff.ontologySha256||JSON.stringify(canonical(ontology.subject))!==JSON.stringify(canonical(subject)))return fail();
 if(JSON.stringify(canonical(profile.binding))!==JSON.stringify(canonical(handoff.binding)))return fail();
 const targetSource=[...ontology.entities,...ontology.associations].find((t:any)=>key(t.type)===key(target));
 if(!targetSource)return fail();
 for(const mapped of home.fields){
  const definition=targetSource.fields.find((f:any)=>key(f.ref)===key(mapped.ref));
  if(!definition||!['protected','unprotected'].includes(definition.protection)||mapped.protected!==(definition.protection==='protected'))return fail();
 }
 const plan=handoff.applicationPlan;
 if(plan.irVersion!=='weft-ir/0.2.0'||plan.readProfile!==null||plan.pageKey!==null||plan.limit!==null||!Array.isArray(plan.filters)||!Array.isArray(plan.order)||!Array.isArray(plan.groups)||!Array.isArray(plan.joins)||!Array.isArray(plan.outputs)||plan.outputs.length<1||plan.outputs.length>32||plan.joins.length>8)return fail();
 const capabilities=new Set(['scan','project','filter','equal','innerJoin','order.asc','group','aggregate','aggregate.count','sum','type.string','type.integer']);
 if(!Array.isArray(plan.requiredCapabilities)||plan.requiredCapabilities.some((c:unknown)=>typeof c!=='string'||!capabilities.has(c)))return fail();
 const scans=new Map<string,any>();
 for(const scan of [plan.source,...plan.joins.map((j:any)=>j.right)]){
  if(key(scan.record)!==key(target)||scans.has(scan.occurrence)||!/^s[0-9]+$/.test(scan.occurrence))return fail();
  scans.set(scan.occurrence,scan);
 }
 const uses=new Map<string,any>();
 for(const use of handoff.uses){
  if(!scans.has(use.scan)||key(use.target)!==key(target)||!['predicate','order','group','join','aggregate'].includes(use.operator))return fail();
  const definition=targetSource.fields.find((f:any)=>key(f.ref)===key(use.field));if(!definition)return fail();
  const mode=definition.queryUse?.[use.operator]??(definition.protection==='protected'?'prohibited':'disclosed');
  const selected=profile.bindings.find((b:any)=>key(b.target)===key(use.target)&&key(b.field)===key(use.field)&&b.operator===use.operator);
  if(mode==='original-authorized'?(typeof selected?.originalAction!=='string'||use.originalAction!==selected.originalAction):mode!=='disclosed'||use.originalAction!==null)return fail();
  const id=JSON.stringify([use.scan,key(use.field),use.operator]);if(uses.has(id))return fail();uses.set(id,use);
 }
 const consumed=new Set<string>();
 const field=(v:any,operator?:string,projection=false)=>{
  if(!v||!scans.has(v.scan))return fail();const mapped=home.fields.find(f=>key(f.ref)===key(v.identity));if(!mapped||projection&&mapped.protected)return fail();
  if(operator){const id=JSON.stringify([v.scan,key(v.identity),operator]),use=uses.get(id);if(!use||mapped.protected&&typeof use.originalAction!=='string'||!mapped.protected&&use.originalAction!==null)return fail();consumed.add(id);}
  if(v.type){
   if(v.type.nullable!==false||v.type.family!==mapped.family)return fail();
   const facets=v.type.facets;
   if(!facets||typeof facets!=='object'||Array.isArray(facets))return fail();
   if(mapped.family==='integer'?(Object.keys(facets).length!==1||!facets.integerWidth||Object.keys(facets.integerWidth).length!==2||facets.integerWidth.bits!==64||facets.integerWidth.signed!==true):Object.keys(facets).length)return fail();
  }
  return ident(v.scan)+'.'+ident(mapped.column);
 };
 const comparison=(v:any,operator:string)=>{
  if(v.op!=='equal')return fail();const left=field(v.left,operator),right=v.right;
  if(right.kind==='field'){if(v.left.type?.family!==right.field?.type?.family)return fail();return '('+left+' OPERATOR(pg_catalog.=) '+field(right.field,operator)+')';}
  if(right.kind!=='literal'||typeof right.value!=='string'||right.type?.nullable!==false||v.left.type?.family!==right.type.family)return fail();
  if(right.type.family==='integer'){
   if(!/^(0|-?[1-9][0-9]*)$/.test(right.value)||right.value.length>20)return fail();const n=BigInt(right.value);if(n<-(1n<<63n)||n>=(1n<<63n))return fail();
   return '('+left+' OPERATOR(pg_catalog.=) '+"'"+right.value+"'::pg_catalog.int8)";
  }
  if(right.type.family!=='string'||right.value.includes('\0')||right.value.length>65536)return fail();
  return '('+left+' OPERATOR(pg_catalog.=) '+"E'"+right.value.replaceAll('\\','\\\\').replaceAll("'","\\'")+"'::pg_catalog.text)";
 };
 const columns=plan.outputs.map((output:any,index:number)=>{
  const e=output.expression;let sql:string;
  if(e.op==='field')sql=field(e,undefined,true);
  else if(e.op==='count'&&!e.argument)sql='pg_catalog.count(*)';
  else if(e.op==='sum'&&e.argument.type?.family==='integer')sql='pg_catalog.sum('+field(e.argument,'aggregate')+')';
  else return fail();
  return sql+' AS '+ident('output_'+index);
 });
 const table=ident(home.schema)+'.'+ident(home.table);
 const resourceType=types.find(t=>key(t.type)===key(target));
 if(!resourceType||resourceType.discriminator||!resourceType.keyFields.length||new Set(home.fields.map(f=>key(f.ref))).size!==home.fields.length)return fail();
 const collectionReady=lowerSecuritySourceCompleteness({root:resourceType,carrier:home});
 const joins=plan.joins.map((j:any)=>{if(!Array.isArray(j.on)||!j.on.length)return fail();return ' JOIN '+table+' AS '+ident(j.right.occurrence)+' ON '+j.on.map((e:any)=>comparison(e,'join')).join(' AND ');}).join('');
 const filters=plan.filters.map((e:any)=>comparison(e,'predicate'));
 const groups=plan.groups.map((e:any)=>field(e,'group'));
 const orders=plan.order.map((e:any)=>field(e,'order'));
 if(consumed.size!==uses.size)return fail();
 // Original-value permissions in this first consumer must be independent of a
 // resource/witness. Otherwise an empty query cannot establish their authority.
 const actions=[...new Set([...uses.values()].map(u=>u.originalAction).filter(a=>a!==null))] as string[];
 let work=4096;
 const independent=(e:any,depth=0):boolean=>{
  if(--work<0||depth>32)return false;
  if(Object.hasOwn(e,'literal'))return typeof e.literal==='boolean';
  if(e.equal)return e.equal.every((t:any)=>t.constant||t.field?.binding==='subject');
  if(e.not)return independent(e.not,depth+1);
  const terms=e.and??e.or;return Array.isArray(terms)&&terms.every(t=>independent(t,depth+1));
 };
 const admission=actions.map(action=>{
  const scoped=handoff.securityLogicalPlan.rules.filter((r:any)=>key(r.target)===key(target)&&r.actions.includes(action));
  if(!scoped.length||scoped.some((r:any)=>!independent(r.condition)))return fail();
  return lowerSecurityRowPredicate({logicalPlan:handoff.securityLogicalPlan,action,target,subject,types,subjectLoginColumn:'native_login'});
 });
 const sql='SELECT '+columns.join(',')+' FROM '+table+' AS '+ident(plan.source.occurrence)+joins+(filters.length?' WHERE '+filters.join(' AND '):'')+(groups.length?' GROUP BY '+groups.join(','):'')+(orders.length?' ORDER BY '+orders.join(','):'');
 if(new TextEncoder().encode(sql).length>1000000)return fail();
 const program=Object.freeze({profileSha256:handoff.profile.sha256,sql,collectionReady,admission:Object.freeze(admission),originalActions:Object.freeze(actions),outputColumns:Object.freeze(plan.outputs.map((_:any,i:number)=>'output_'+i))});
 issuedPrograms.add(program);return program;
}


/** Issued lowering only. These checks must precede application SQL, including empty queries.
 * Native authority-cut and publication guards remain the installer's obligation. */
export function lowerOriginalUsePreExecutionChecks(program:Awaited<ReturnType<typeof lowerSecurityOriginalUseProgram>>):string{
 if(!issuedPrograms.has(program))return fail();
 return program.admission.map(guard=>"IF ("+guard+") IS NOT TRUE THEN RAISE EXCEPTION 'Original query use unavailable' USING ERRCODE='42501'; END IF; ").join('')+
  "IF ("+program.collectionReady+") IS NOT TRUE THEN RAISE EXCEPTION 'Original source unavailable' USING ERRCODE='42501'; END IF; ";
}

/** One issued PL/pgSQL return fragment: authorization and completeness precede
 * the captured application query. Results use exact native text carriers.
 * The installer still owns the enclosing authority/publication guards. */
export function lowerOriginalUseTextRowsReturn(program:Awaited<ReturnType<typeof lowerSecurityOriginalUseProgram>>):string{
 if(!issuedPrograms.has(program))return fail();
 const fields=program.outputColumns.map((column:string)=>'q.'+ident(column)+'::pg_catalog.text').join(',');
 return lowerOriginalUsePreExecutionChecks(program)+
  " RETURN (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array("+fields+")),'[]'::pg_catalog.jsonb) FROM ("+program.sql+") q); ";
}
