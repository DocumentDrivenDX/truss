/** Draft condition, rule-fold and disclosure-metadata SQL: no source
 * authentication, fact completeness, native inventory admission or authorization permit. */
import {bindCandidateSecurityEndpoint,type CandidateEndpointColumns} from './security-candidate-endpoint';
import {isCandidateGraphSource,requireCandidateGraphSource,candidateGraphSourcePopulation,type CandidateGraphSource} from './security-graph-source';
type Ref={documentId:string;moduleId:string;elementId:string};
type Association=Ref|{documentId:string;moduleId:string;relationshipId:string};
export interface CandidateConditionScan{association:Association;home:{schema:string;table:string}|{source:CandidateGraphSource};endpoints:readonly CandidateEndpointColumns[];fields?:readonly CandidateConditionField[];discriminator?:{column:string;carrier:'text'|'int4'|'int8';value:string};record?:{owner:Ref;keyId:string;keyFields:readonly Ref[];columns:readonly string[]}}
export interface CandidateConditionField{owner:Ref;field:Ref;domain:unknown;column:string}
export interface CandidateConditionValue{binding:'subject'|'resource'|'context';field:Ref;domain:unknown;parameter:number;owner?:Ref}
export interface CandidateConditionIdentity{target:Ref;keyId:string;keyFields:readonly Ref[];parameters:readonly number[]}
const fail=():never=>{throw Error('TRUSS_SECURITY_CANDIDATE_CONDITION_UNSUPPORTED');};
function object(v:unknown,keys:readonly string[]):Record<string,any>{if(!v||typeof v!=='object'||Array.isArray(v)||![Object.prototype,null].includes(Object.getPrototypeOf(v)))return fail();const ds=Object.getOwnPropertyDescriptors(v);if(Reflect.ownKeys(ds).length!==keys.length||keys.some(k=>!Object.hasOwn(ds,k)||!Object.hasOwn(ds[k]!,'value')||!ds[k]!.enumerable))return fail();return Object.fromEntries(keys.map(k=>[k,ds[k]!.value]));}
function ref(v:unknown):string{const r=object(v,['documentId','moduleId','elementId']);if(Object.values(r).some(x=>typeof x!=='string'||!x||x.length>8192||[...x].length>4096||x.includes('\0')||[...x].some(c=>{const p=c.codePointAt(0)!;return p>=0xd800&&p<=0xdfff;})))return fail();return JSON.stringify(r);}
function assoc(v:unknown):string{if(!v||typeof v!=='object')return fail();if(Object.hasOwn(v,'relationshipId')){const r=object(v,['documentId','moduleId','relationshipId']);if(Object.values(r).some(x=>typeof x!=='string'||!x||x.length>8192||[...x].length>4096||x.includes('\0')||[...x].some(c=>{const p=c.codePointAt(0)!;return p>=0xd800&&p<=0xdfff;})))return fail();return JSON.stringify(r);}return ref(v);}
function quote(v:unknown):string{if(typeof v!=='string'||!v||new TextEncoder().encode(v).length>63||v.includes('\0')||[...v].some(c=>{const n=c.codePointAt(0)!;return n>=0xd800&&n<=0xdfff;}))return fail();return '"'+v.replaceAll('"','""')+'"';}
 function candidateDomain(v:unknown):string{
  const d=object(v,['scalarType','nullability','cardinality','facets','allowedValues']);if(!['string','boolean','integer','decimal','binary'].includes(d.scalarType)||d.nullability!=='required'||d.cardinality!=='one'||d.allowedValues!==null)return fail();
  if(d.scalarType==='decimal'){const f=object(d.facets,['precision','scale']);if(!Number.isSafeInteger(f.precision)||f.precision<1||f.precision>1000||!Number.isSafeInteger(f.scale)||f.scale<0||f.scale>f.precision)return fail();return 'decimal:'+f.precision+':'+f.scale;}
  if(d.scalarType==='integer'&&Object.hasOwn(d.facets??{},'integerWidth')){const f=object(object(d.facets,['integerWidth']).integerWidth,['bits','signed']);if(!Number.isSafeInteger(f.bits)||f.bits<1||f.bits>4096||typeof f.signed!=='boolean')return fail();return 'integer:'+f.bits+':'+f.signed;}
  object(d.facets,[]);return d.scalarType;
 }
 /** Exact coefficient conversion. Metadata counts use numbers; values never do. */
 function candidateNumeric(token:unknown,d:string):string{
  if(typeof token!=='string'||token.length>65536)return fail();const m=/^(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$/.exec(token);if(!m||m[0]!==token)return fail();
  const parts=d.split(':'),scale=d.startsWith('decimal:')?Number(parts[2]):0,precision=d.startsWith('decimal:')?Number(parts[1]):65536;
  let digits=(m[2]!+(m[3]??'')).replace(/^0+/,'');if(!digits)return '0';const exponent=m[4]??'0';if(exponent.length>32)return fail();const shift=BigInt(exponent)-BigInt((m[3]??'').length)+BigInt(scale);
  if(shift<0n){const cut=-shift;if(cut>BigInt(digits.length))return fail();const at=digits.length-Number(cut);if(!/^0*$/.test(digits.slice(at)))return fail();digits=digits.slice(0,at);}
  else{if(BigInt(digits.length)+shift>BigInt(precision))return fail();digits+='0'.repeat(Number(shift));}
  if(digits.length>precision)return fail();const coefficient=BigInt((m[1]??'')+(digits||'0'));
  if(d.startsWith('integer:')){const bits=BigInt(parts[1]!),signed=parts[2]==='true',limit=1n<<(signed?bits-1n:bits);if(coefficient<(signed?-limit:0n)||coefficient>=limit)return fail();}
  if(!scale)return coefficient.toString();const negative=coefficient<0n,body=(negative?-coefficient:coefficient).toString().padStart(scale+1,'0');return (negative?'-':'')+body.slice(0,-scale)+'.'+body.slice(-scale);
 }

/** Snapshot plain data without invoking source getters; bounded before traversal. */
function snapshot(v:unknown):unknown{
 let nodes=4096,text=4_000_000;const active=new WeakSet<object>();
 function copy(x:unknown,depth:number):unknown{
  if(--nodes<0||depth>32)return fail();if(typeof x==='string'){text-=x.length;if(text<0)return fail();return x;}
  if(x===null||typeof x==='boolean'||(typeof x==='number'&&Number.isFinite(x)))return x;
  if(!x||typeof x!=='object'||active.has(x))return fail();
  // Preserve immutable local issuance through repeated fold/disclosure snapshots.
  // A copied SQL packet follows ordinary validation and cannot regain issuance.
  if(isCandidateGraphSource(x)){text-=x.sql.length+x.validitySql.length;if(text<0)return fail();return x;}
  active.add(x);
  const ds=Object.getOwnPropertyDescriptors(x);let result:unknown;
  if(Array.isArray(x)){const length=ds.length?.value;if(Object.getPrototypeOf(x)!==Array.prototype||!Number.isSafeInteger(length)||length<0||length>4096||Reflect.ownKeys(ds).length!==length+1)return fail();result=Array.from({length},(_,i)=>{const d=ds[String(i)];if(!d||!Object.hasOwn(d,'value')||!d.enumerable)return fail();return copy(d.value,depth+1);});}
  else{if(![Object.prototype,null].includes(Object.getPrototypeOf(x))||Reflect.ownKeys(ds).length>256)return fail();const entries=[];for(const key of Reflect.ownKeys(ds)){if(typeof key!=='string'||!Object.hasOwn(ds[key]!,'value')||!ds[key]!.enumerable)return fail();text-=key.length;if(text<0)return fail();entries.push([key,copy(ds[key]!.value,depth+1)]);}result=Object.fromEntries(entries);}
  active.delete(x);return result;
 }
 return copy(v,0);
}
/** Intrinsic Key values are numbered native parameters, never supplied SQL. */
export function lowerCandidateSecurityCondition(input:{condition:unknown;scans:readonly CandidateConditionScan[];subject?:CandidateConditionIdentity;resource?:CandidateConditionIdentity;values?:readonly CandidateConditionValue[]}):string{
 input=snapshot(input) as typeof input;object(input,['condition','scans',...(['subject','resource','values'] as const).filter(k=>Object.hasOwn(input,k))]);
 if(!Array.isArray(input.scans)||input.scans.length>64)return fail();const scans=new Map(input.scans.map(s=>[assoc(s.association),s]));if(scans.size!==input.scans.length)return fail();
 const keys=new Map<string,string>();
 function key(target:Ref,id:string,fields:readonly Ref[],arity:number):string{
  if(typeof id!=='string'||!id||id.length>8192||[...id].length>4096||id.includes('\0')||[...id].some(c=>{const n=c.codePointAt(0)!;return n>=0xd800&&n<=0xdfff;})||!Array.isArray(fields)||!fields.length||fields.length>256||fields.length!==arity)return fail();
  const ordered=fields.map(ref);if(new Set(ordered).size!==ordered.length)return fail();const nominal=ref(target)+JSON.stringify(id),definition=JSON.stringify(ordered);if(keys.has(nominal)&&keys.get(nominal)!==definition)return fail();keys.set(nominal,definition);return nominal+definition;
 }
 for(const name of ['subject','resource'] as const)if(Object.hasOwn(input,name)){const intrinsic=input[name]??fail();object(intrinsic,['target','keyId','keyFields','parameters']);if(!Array.isArray(intrinsic.parameters)||intrinsic.parameters.some(p=>!Number.isSafeInteger(p)||p<1||p>65535))return fail();key(intrinsic.target,intrinsic.keyId,intrinsic.keyFields,intrinsic.parameters.length);}
 const sources=new Map<CandidateConditionScan,CandidateGraphSource>();
 function relation(scan:CandidateConditionScan):string{const source=sources.get(scan);if(source)return '('+source.sql+')';const home=scan.home as {schema:string;table:string};return quote(home.schema)+'.'+quote(home.table);}
 for(const scan of scans.values()){
  object(scan,['association','home','endpoints',...(scan.record?['record']:[]),...(Object.hasOwn(scan,'fields')?['fields']:[]),...(Object.hasOwn(scan,'discriminator')?['discriminator']:[])]);if(Object.hasOwn(scan.home,'source')){const home=object(scan.home,['source']);requireCandidateGraphSource(home.source);sources.set(scan,home.source);}else{const home=object(scan.home,['schema','table']);quote(home.schema);quote(home.table);}if(!Array.isArray(scan.endpoints)||scan.endpoints.length>64)return fail();const roles=new Set<string>();
  for(const m of scan.endpoints){if(roles.has(m.role)||assoc(m.association)!==assoc(scan.association))return fail();roles.add(m.role);const endpoint=bindCandidateSecurityEndpoint({endpoint:{binding:{variable:0},association:m.association,role:m.role,target:m.target,keyId:m.keyId,carrier:m.carrier}},m);key(endpoint.target,endpoint.keyId,endpoint.targetKeyFields,endpoint.columns.length);}
  if(scan.record){object(scan.record,['owner','keyId','keyFields','columns']);ref(scan.record.owner);if(typeof scan.record.keyId!=='string'||!scan.record.keyId||!Array.isArray(scan.record.columns)||!scan.record.columns.length||scan.record.columns.length>256||new Set(scan.record.columns).size!==scan.record.columns.length)return fail();scan.record.columns.forEach(quote);key(scan.record.owner,scan.record.keyId,scan.record.keyFields,scan.record.columns.length);}
 }

 const fieldDomains=new Map<string,string>();
 function fieldDomain(field:Ref,value:unknown){const id=ref(field),d=candidateDomain(value);if(fieldDomains.has(id)&&fieldDomains.get(id)!==d)return fail();fieldDomains.set(id,d);return d;}
 const fieldOwners=new Map<string,string>();
 function fieldOwner(field:Ref,owner:Ref){const f=ref(field),o=ref(owner);if(fieldOwners.has(f)&&fieldOwners.get(f)!==o)return fail();fieldOwners.set(f,o);}
 for(const scan of scans.values())if(Object.hasOwn(scan,'fields')){if(!Array.isArray(scan.fields)||scan.fields.length>256||!scan.record)return fail();const seen=new Set<string>();for(const f of scan.fields){object(f,['owner','field','domain','column']);if(ref(f.owner)!==ref(scan.record.owner)||seen.has(ref(f.field)))return fail();seen.add(ref(f.field));fieldOwner(f.field,f.owner);fieldDomain(f.field,f.domain);quote(f.column);const at=scan.record.keyFields.findIndex((k:Ref)=>ref(k)===ref(f.field));if(at>=0&&scan.record.columns[at]!==f.column)return fail();for(const endpoint of scan.endpoints){const carrier=endpoint.carrier as any;if(carrier.members){const member=carrier.members.fields.findIndex((k:Ref)=>ref(k)===ref(f.field));if(member>=0&&endpoint.columns[member]!==f.column)return fail();}}}}
 const values=new Map<string,CandidateConditionValue>();
 if(Object.hasOwn(input,'values')){if(!Array.isArray(input.values)||input.values.length>256)return fail();for(const v of input.values){object(v,['binding','field','domain','parameter',...(Object.hasOwn(v,'owner')?['owner']:[])]);if(!['subject','resource','context'].includes(v.binding)||!Number.isSafeInteger(v.parameter)||v.parameter<1||v.parameter>65535)return fail();fieldDomain(v.field,v.domain);const id=JSON.stringify([v.binding,ref(v.field)]);if(values.has(id))return fail();values.set(id,v);if(v.binding==='context'){if(Object.hasOwn(v,'owner'))return fail();}else{const intrinsic=input[v.binding as 'subject'|'resource']??fail();if(!Object.hasOwn(v,'owner')||ref(v.owner)!==ref(intrinsic.target))return fail();fieldOwner(v.field,v.owner!);const at=intrinsic.keyFields.findIndex(k=>ref(k)===ref(v.field));if(at>=0&&intrinsic.parameters[at]!==v.parameter)return fail();}}}
 function scalar(v:unknown,vars:Map<number,Bound>):{key:string;sql:string[]}|undefined{
  if(!v||typeof v!=='object'||!Object.hasOwn(v,'value'))return undefined;const value=object(v,['value']).value;if(!value||typeof value!=='object'||Object.hasOwn(value,'identity'))return undefined;
  const names=Reflect.ownKeys(value);if(names.length!==1||!['field','context','constant'].includes(String(names[0])))return fail();const kind=String(names[0]),t=object(value,[kind])[kind],d=fieldDomain(t.field,t.domain);ref(t.field);let sql:string;
  if(kind==='constant'){object(t,['field','domain','literal']);const literalKey=d.startsWith('integer')?'integerToken':d.startsWith('decimal:')?'decimalToken':d==='binary'?'binaryHex':d,literal=object(t.literal,[literalKey]);if(d==='boolean'){if(typeof literal.boolean!=='boolean')return fail();sql=literal.boolean?'TRUE':'FALSE';}else if(d.startsWith('integer')||d.startsWith('decimal:')){sql="E'"+candidateNumeric(literal[literalKey],d)+"'::pg_catalog.numeric";}else if(d==='binary'){const hex=literal.binaryHex;if(typeof hex!=='string'||hex.length>65536||hex.length%2||/[^0-9a-fA-F]/.test(hex))return fail();sql="pg_catalog.decode(E'"+hex.toLowerCase()+"'::pg_catalog.text,E'hex'::pg_catalog.text)";}else{const text=literal.string;if(typeof text!=='string'||text.length>65536||text.includes('\0')||[...text].some(c=>{const n=c.codePointAt(0)!;return n>=0xd800&&n<=0xdfff;}))return fail();sql="E'"+text.replaceAll('\\','\\\\').replaceAll("'","\\'")+"'::pg_catalog.text";}}
  else{object(t,kind==='context'?['field','domain']:['binding','field','domain']);if(kind==='context'||t.binding==='subject'||t.binding==='resource'){const binding=kind==='context'?'context':t.binding,m=values.get(JSON.stringify([binding,ref(t.field)]))??fail();if(candidateDomain(m.domain)!==d)return fail();sql='$'+m.parameter+'::pg_catalog.'+(d==='string'?'text':d==='boolean'?'bool':d==='binary'?'bytea':'numeric');}else{const b=vars.get(object(t.binding,['variable']).variable)??fail(),m=b.scan.fields?.find(f=>ref(f.field)===ref(t.field))??fail();if(!b.scan.record||candidateDomain(m.domain)!==d)return fail();sql=quote(b.alias)+'.'+quote(m.column);}}
  return {key:'scalar:'+d,sql:[d==='string'?'('+sql+' COLLATE pg_catalog."C")':sql]};
 }
 const selectors=new Map<CandidateConditionScan,{column:string;carrier:string;value:string}>(),homes=new Map<string,CandidateConditionScan[]>();
 for(const scan of scans.values()){
  const source=sources.get(scan),home=source?candidateGraphSourcePopulation(source):relation(scan);homes.set(home,[...(homes.get(home)??[]),scan]);
  if(Object.hasOwn(scan,'discriminator')){const d=object(scan.discriminator,['column','carrier','value']);quote(d.column);
   if(!['text','int4','int8'].includes(d.carrier)||typeof d.value!=='string'||!d.value||d.value.length>65536||d.value.includes('\0')||[...d.value].some(c=>{const n=c.codePointAt(0)!;return n>=0xd800&&n<=0xdfff;}))return fail();
   if(d.carrier!=='text'){if(!/^(0|-?[1-9][0-9]*)$/.test(d.value)||d.value.length>20)return fail();const n=BigInt(d.value),bits=d.carrier==='int4'?31n:63n;if(n<-(1n<<bits)||n>=(1n<<bits))return fail();}
   selectors.set(scan,d as {column:string;carrier:string;value:string});
  }
 }
 for(const group of homes.values())if(group.length>1){const ds=group.map(s=>selectors.get(s)??fail()),first=ds[0]!;if(ds.some(d=>d.column!==first.column||d.carrier!==first.carrier)||new Set(ds.map(d=>d.value)).size!==ds.length)return fail();}
 function selected(scan:CandidateConditionScan,alias:string):string{const d=selectors.get(scan);if(!d)return '';const literal="E'"+d.value.replaceAll('\\','\\\\').replaceAll("'","\\'")+"'::pg_catalog."+d.carrier;const column=quote(alias)+'.'+quote(d.column);return '('+(d.carrier==='text'?'('+column+' COLLATE pg_catalog."C")':column)+' OPERATOR(pg_catalog.=) '+(d.carrier==='text'?'('+literal+' COLLATE pg_catalog."C")':literal)+') IS TRUE AND ';}
 let work=4096;const bounded=(sql:string)=>{if(sql.length>250000)return fail();return sql;};
 type Bound={scan:CandidateConditionScan;alias:string};
 function term(v:unknown,vars:Map<number,Bound>):{key:string;sql:string[]}{
  const scalarValue=scalar(v,vars);if(scalarValue)return scalarValue;
  if(v&&typeof v==='object'&&Object.hasOwn(v,'endpoint')){const e=object(object(v,['endpoint']).endpoint,['binding','association','role','target','keyId','carrier']),slot=object(e.binding,['variable']).variable,b=vars.get(slot)??fail();if(assoc(e.association)!==assoc(b.scan.association))return fail();const mapping=b.scan.endpoints.find(m=>m.role===e.role)??fail(),bound=bindCandidateSecurityEndpoint(v,mapping);return {key:key(bound.target,bound.keyId,bound.targetKeyFields,bound.columns.length),sql:bound.columns.map(c=>quote(b.alias)+'.'+quote(c))};}
  const value=object(object(v,['value']).value,['identity']),i=object(value.identity,['binding','target','keyId']);let sql:string[],fields:readonly Ref[];
  if(i.binding==='subject'||i.binding==='resource'){const binding=input[i.binding as 'subject'|'resource']??fail();if(ref(binding.target)!==ref(i.target)||binding.keyId!==i.keyId||!binding.parameters.length||binding.parameters.length>256||binding.parameters.some(p=>!Number.isSafeInteger(p)||p<1||p>65535))return fail();sql=binding.parameters.map(p=>'$'+p);fields=binding.keyFields;}
  else{const b=vars.get(object(i.binding,['variable']).variable)??fail(),record=b.scan.record??fail();if(ref(record.owner)!==ref(i.target)||record.keyId!==i.keyId||!record.columns.length||record.columns.length>256)return fail();fields=record.keyFields;sql=record.columns.map(c=>quote(b.alias)+'.'+quote(c));}
  return {key:key(i.target,i.keyId,fields,sql.length),sql};
 }
 function expression(v:unknown,vars:Map<number,Bound>,depth:number):string{
  if(--work<0||depth>16)return fail();if(!v||typeof v!=='object'||Reflect.ownKeys(v).length!==1)return fail();const op=Reflect.ownKeys(v)[0];if(typeof op!=='string'||!['literal','equal','and','or','not','exists'].includes(op))return fail();const e=object(v,[op])[op];
  if(op==='literal'){if(typeof e!=='boolean')return fail();return e?'TRUE':'FALSE';}
  if(op==='equal'){if(!Array.isArray(e)||e.length!==2)return fail();const a=term(e[0],vars),b=term(e[1],vars);if(a.key!==b.key||a.sql.length!==b.sql.length)return fail();return bounded('('+a.sql.map((s,i)=>'('+s+' OPERATOR(pg_catalog.=) '+b.sql[i]+')').join(' AND ')+')');}
  if(op==='not')return bounded('(NOT '+expression(e,vars,depth+1)+')');
  if(op==='and'||op==='or'){if(!Array.isArray(e)||!e.length||e.length>4096)return fail();return bounded('('+e.map(x=>expression(x,vars,depth+1)).join(op==='and'?' AND ':' OR ')+')');}
  const x=object(e,['slot','association','witness','condition']);if(!Number.isSafeInteger(x.slot)||x.slot<0||vars.has(x.slot))return fail();const scan=scans.get(assoc(x.association))??fail();
  if(x.witness==='opaqueExistential'){if(!Object.hasOwn(scan.association,'relationshipId')||scan.record)return fail();}
  else{const r=object(object(x.witness,['recordKey']).recordKey,['owner','keyId','key']),record=scan.record??fail();if(ref(r.owner)!==ref(record.owner)||r.keyId!==record.keyId)return fail();const original=object(r.key,['id','name','fields',...(Object.hasOwn(r.key??{},'primary')?['primary']:[])]);if(original.id!==r.keyId||typeof original.name!=='string'||!original.name||('primary' in original&&typeof original.primary!=='boolean')||!Array.isArray(original.fields))return fail();const originalFields=original.fields.map(f=>{const field=object(f,['module','element']);return {documentId:r.owner.documentId,moduleId:field.module,elementId:field.element};});key(r.owner,r.keyId,originalFields,record.columns.length);}
  const alias='candidate_'+x.slot,nested=new Map(vars);nested.set(x.slot,{scan,alias});const child=expression(x.condition,nested,depth+1);const from=' FROM '+relation(scan)+' AS '+quote(alias)+' WHERE '+selected(scan,alias)+'('+child+')';
  return bounded('(CASE WHEN EXISTS(SELECT 1'+from+' IS TRUE) THEN TRUE WHEN EXISTS(SELECT 1'+from+' IS NULL) THEN NULL::pg_catalog.bool ELSE FALSE END)');
 }
 const condition=expression(input.condition,new Map(),0);
 function valid(sql:string,d:string):string{
  const n='('+sql+')',parts=d.split(':'),checks=[n+' IS NOT NULL'];
  if(d.startsWith('integer')||d.startsWith('decimal:')){
   for(const special of ['NaN','Infinity','-Infinity'])checks.push(n+" OPERATOR(pg_catalog.<>) E'"+special+"'::pg_catalog.numeric");
   if(d.startsWith('integer')){checks.push('pg_catalog.trunc('+n+') OPERATOR(pg_catalog.=) '+n);if(parts.length===3){const bits=BigInt(parts[1]!),signed=parts[2]==='true',limit=1n<<(signed?bits-1n:bits);checks.push(n+" OPERATOR(pg_catalog.>=) E'"+(signed?-limit:0n).toString()+"'::pg_catalog.numeric",n+" OPERATOR(pg_catalog.<) E'"+limit.toString()+"'::pg_catalog.numeric");}}
   else{const precision=Number(parts[1]),scale=Number(parts[2]),factor="E'1"+'0'.repeat(scale)+"'::pg_catalog.numeric",scaled='('+n+' OPERATOR(pg_catalog.*) '+factor+')';checks.push('pg_catalog.abs('+n+") OPERATOR(pg_catalog.<) E'1"+'0'.repeat(precision-scale)+"'::pg_catalog.numeric");return '(CASE WHEN ('+checks.join(' AND ')+') IS TRUE THEN (pg_catalog.trunc('+scaled+') OPERATOR(pg_catalog.=) '+scaled+') IS TRUE ELSE FALSE END)';}
  }
  return '('+checks.join(' AND ')+')';
 }
 const guards:string[]=[...new Set(sources.values())].map(source=>'((SELECT valid FROM ('+source.validitySql+') candidate_source_validity)::pg_catalog.bool) IS TRUE');
 for(const value of values.values()){const d=candidateDomain(value.domain),carrier=d==='string'?'text':d==='boolean'?'bool':d==='binary'?'bytea':'numeric';guards.push(valid('$'+value.parameter+'::pg_catalog.'+carrier,d));}
 let index=0;for(const scan of scans.values())if(scan.fields?.length){const alias='candidate_admission_'+index++,fields=scan.fields.map((f:CandidateConditionField)=>valid(quote(alias)+'.'+quote(f.column),candidateDomain(f.domain)));guards.push('(NOT EXISTS(SELECT 1 FROM '+relation(scan)+' AS '+quote(alias)+' WHERE '+selected(scan,alias)+'('+fields.join(' AND ')+') IS NOT TRUE))');}
 // The guard is outside authored NOT/OR/EXISTS: invalid mappings cannot become
 // True through negation or disappear behind a successful sibling expression.
 // NULL is a diagnostic indeterminate result, not an admission permit.
 return guards.length?bounded('(CASE WHEN ('+guards.join(' AND ')+') IS TRUE THEN '+condition+' ELSE NULL::pg_catalog.bool END)'):condition;

}

/** Intermediate rule-truth fold only. Empty disclosure profile; no data release,
 * source authentication, native authority or authorization capability. */
export function lowerCandidateSecurityRuleFold(input:Omit<Parameters<typeof lowerCandidateSecurityCondition>[0],'condition'>&{rules:readonly unknown[];target:Ref;action:string}):{sql:string;ruleIds:readonly string[];truthCte:string;decisionSql:string}{
 input=snapshot(input) as typeof input;object(input,['rules','target','action','scans',...(['subject','resource','values'] as const).filter(k=>Object.hasOwn(input,k))]);
 const target=ref(input.target);ref({documentId:'metadata',moduleId:'metadata',elementId:input.action});
 if(!Array.isArray(input.rules)||input.rules.length>64)return fail();
 const shared={scans:input.scans,...Object.fromEntries((['subject','resource','values'] as const).filter(k=>Object.hasOwn(input,k)).map(k=>[k,input[k]]))};
 lowerCandidateSecurityCondition({...shared,condition:{literal:false}});
 if(input.resource&&ref(input.resource.target)!==target)return fail();
 const seen=new Set<string>(),selected:Record<string,any>[]=[];
 for(const value of input.rules){const r=object(value,['id','effect','actions','target','condition','disclosure']);ref({documentId:'metadata',moduleId:'metadata',elementId:r.id});const ruleTarget=ref(r.target),identity=JSON.stringify([r.id,ruleTarget]);if(seen.has(identity))return fail();seen.add(identity);
  if(!['permit','require','forbid'].includes(r.effect)||!Array.isArray(r.actions)||!r.actions.length||r.actions.length>64||new Set(r.actions).size!==r.actions.length||!Array.isArray(r.disclosure)||r.disclosure.length)return fail();
  for(const action of r.actions)ref({documentId:'metadata',moduleId:'metadata',elementId:action});
  if(ruleTarget===target&&r.actions.includes(input.action))selected.push(r);
 }
 const ruleDomains=new Map<string,string>();
 function domains(node:unknown):void{if(!node||typeof node!=='object')return;if(Array.isArray(node)){node.forEach(domains);return;}const n=node as Record<string,any>;if(n.value&&typeof n.value==='object')for(const kind of ['field','context','constant'])if(Object.hasOwn(n.value,kind)){const t=n.value[kind],id=ref(t?.field),d=candidateDomain(t?.domain);if(ruleDomains.has(id)&&ruleDomains.get(id)!==d)return fail();ruleDomains.set(id,d);}Object.values(n).forEach(domains);}
 for(const r of selected)domains(r.condition);
 const ruleIds=Object.freeze(selected.map(r=>r.id as string));
 if(!selected.length){const truthCte='candidate_rule_truths(rule_index,effect,truth) AS MATERIALIZED (SELECT NULL::pg_catalog.int4,NULL::pg_catalog.text COLLATE pg_catalog."C",NULL::pg_catalog.bool WHERE FALSE)',decisionSql="SELECT E'deny'::pg_catalog.text AS decision";return Object.freeze({sql:decisionSql,ruleIds,truthCte,decisionSql});}
 const tuples=selected.map((r,i)=>"("+i+"::pg_catalog.int4, E'"+r.effect+"'::pg_catalog.text COLLATE pg_catalog.\"C\", "+lowerCandidateSecurityCondition({...shared,condition:r.condition})+')');
 const truthCte='candidate_rule_truths(rule_index,effect,truth) AS MATERIALIZED (VALUES '+tuples.join(', ')+')';
 const decisionSql="SELECT CASE WHEN EXISTS(SELECT 1 FROM candidate_rule_truths WHERE truth IS NULL) THEN E'indeterminate'::pg_catalog.text WHEN NOT EXISTS(SELECT 1 FROM candidate_rule_truths WHERE effect OPERATOR(pg_catalog.=) E'permit'::pg_catalog.text COLLATE pg_catalog.\"C\" AND truth IS TRUE) OR EXISTS(SELECT 1 FROM candidate_rule_truths WHERE (effect OPERATOR(pg_catalog.=) E'require'::pg_catalog.text COLLATE pg_catalog.\"C\" AND truth IS NOT TRUE) OR (effect OPERATOR(pg_catalog.=) E'forbid'::pg_catalog.text COLLATE pg_catalog.\"C\" AND truth IS TRUE)) THEN E'deny'::pg_catalog.text ELSE E'permit'::pg_catalog.text END AS decision";
 const sql='WITH '+truthCte+' '+decisionSql;if(sql.length>1_000_000)return fail();return Object.freeze({sql,ruleIds,truthCte,decisionSql});
}

export interface CandidateDisclosureField{owner:Ref;field:Ref;domain:unknown;protection:'protected'|'unprotected'}
/** Diagnostic disposition SQL. Returns metadata only, never native field values
 * or an authorization capability. Supplied ontology inventory is not authenticated. */
export function lowerCandidateSecurityDisclosure(input:Parameters<typeof lowerCandidateSecurityRuleFold>[0]&{fields:readonly CandidateDisclosureField[];outputFields:readonly Ref[]}):{sql:string;ruleIds:readonly string[]}{
 input=snapshot(input) as typeof input;object(input,['rules','target','action','scans','fields','outputFields',...(['subject','resource','values'] as const).filter(k=>Object.hasOwn(input,k))]);
 if(!Array.isArray(input.fields)||input.fields.length>256||!Array.isArray(input.outputFields)||input.outputFields.length>256||!Array.isArray(input.rules)||input.rules.length>64)return fail();
 const target=ref(input.target),fields=new Map<string,CandidateDisclosureField>();
 for(const f of input.fields){object(f,['owner','field','domain','protection']);const id=ref(f.field);ref(f.owner);candidateDomain(f.domain);if(fields.has(id)||!['protected','unprotected'].includes(f.protection))return fail();fields.set(id,f);}
 const requested=new Set<string>();for(const f of input.outputFields){const id=ref(f),metadata=fields.get(id)??fail();if(requested.has(id)||ref(metadata.owner)!==target)return fail();requested.add(id);}
 function checkDomain(field:Ref,d:unknown){const declared=fields.get(ref(field))??fail();if(candidateDomain(declared.domain)!==candidateDomain(d))return fail();}
 function conditions(node:unknown):void{if(!node||typeof node!=='object')return;if(Array.isArray(node)){node.forEach(conditions);return;}const n=node as Record<string,any>;if(n.value&&typeof n.value==='object')for(const kind of ['field','context','constant'])if(Object.hasOwn(n.value,kind)){const t=n.value[kind];checkDomain(t?.field,t?.domain);}Object.values(n).forEach(conditions);}
 for(const value of input.values??[]){checkDomain(value.field,value.domain);if(value.binding!=='context'&&ref(value.owner)!==ref(fields.get(ref(value.field))!.owner))return fail();}
 for(const scan of input.scans)for(const f of scan.fields??[]){checkDomain(f.field,f.domain);if(ref(f.owner)!==ref(fields.get(ref(f.field))!.owner))return fail();}
 type Disposition={field:Ref;payload:unknown;kind:'original'|'withheld'|'transformed';identity?:string};
 const declarations=new Map<string,Disposition[]>();
 for(const value of input.rules){const r=object(value,['id','effect','actions','target','condition','disclosure']);if(!Array.isArray(r.disclosure)||r.disclosure.length>256||(r.effect!=='permit'&&r.disclosure.length))return fail();conditions(r.condition);const seen=new Set<string>(),ds:Disposition[]=[];
  for(const tuple of r.disclosure){if(!Array.isArray(tuple)||tuple.length!==2)return fail();const id=ref(tuple[0]),metadata=fields.get(id)??fail();if(seen.has(id)||ref(metadata.owner)!==ref(r.target))return fail();seen.add(id);const payload=tuple[1];
   if(payload==='original'||payload==='withheld'){ds.push({field:tuple[0],payload,kind:payload});continue;}
   const mask=object(object(payload,['transformed']).transformed,['transform','version','outputField','domain','literal']);if(mask.transform!=='constant'||mask.version!=='0.1.0')return fail();checkDomain(mask.outputField,mask.domain);
   const constant={value:{constant:{field:mask.outputField,domain:mask.domain,literal:mask.literal}}};lowerCandidateSecurityCondition({scans:[],condition:{equal:[constant,constant]}});
   const d=candidateDomain(mask.domain),literal=mask.literal;let normalized:unknown;
   if(d.startsWith('integer'))normalized=candidateNumeric(literal.integerToken,d);else if(d.startsWith('decimal:'))normalized=candidateNumeric(literal.decimalToken,d);else if(d==='binary')normalized=literal.binaryHex.toLowerCase();else normalized=literal[d];
   ds.push({field:tuple[0],payload,kind:'transformed',identity:JSON.stringify([mask.transform,mask.version,ref(mask.outputField),normalized])});
  }
  const key=JSON.stringify([r.id,ref(r.target)]);if(declarations.has(key))return fail();declarations.set(key,ds);
 }
 const {fields:unusedFields,outputFields:unusedOutputs,...shared}=input;
 const fold=lowerCandidateSecurityRuleFold({...shared,rules:input.rules.map(r=>({...r as Record<string,unknown>,disclosure:[]}))});
 const selected=input.rules.filter((r:any)=>ref(r.target)===target&&r.actions.includes(input.action)) as Record<string,any>[];
 const quoteJson=(value:unknown)=>"E'"+JSON.stringify(value).replaceAll('\\','\\\\').replaceAll("'","\\'")+"'::pg_catalog.jsonb";
 const active=(index:number)=>'(EXISTS(SELECT 1 FROM candidate_rule_truths WHERE rule_index OPERATOR(pg_catalog.=) '+index+'::pg_catalog.int4 AND truth IS TRUE))';
 const any=(terms:string[])=>terms.length?'('+terms.join(' OR ')+')':'FALSE';
 let work=4096;const tick=()=>{if(--work<0)return fail();};const checks:string[]=[],payloads:string[]=[];
 for(const field of input.outputFields){tick();const id=ref(field),metadata=fields.get(id)!,obligations:{disposition:Disposition;active:string}[]=[];
  selected.forEach((r,index)=>{tick();if(r.effect==='permit')for(const d of declarations.get(JSON.stringify([r.id,ref(r.target)]))!)if(ref(d.field)===id)obligations.push({disposition:d,active:active(index)});});
  const withholds=any(obligations.filter(o=>o.disposition.kind==='withheld').map(o=>o.active)),masks=obligations.filter(o=>o.disposition.kind==='transformed'),conflicts:string[]=[];
  if(metadata.protection==='protected')checks.push('WHEN NOT '+any(obligations.map(o=>o.active))+" THEN E'indeterminate'::pg_catalog.text");
  for(let i=0;i<masks.length;i++)for(let j=i+1;j<masks.length;j++){tick();if(masks[i]!.disposition.identity!==masks[j]!.disposition.identity)conflicts.push('('+masks[i]!.active+' AND '+masks[j]!.active+')');}
  if(conflicts.length)checks.push('WHEN (NOT '+withholds+' AND '+any(conflicts)+") THEN E'conflict'::pg_catalog.text");
  const transformed=masks.map(o=>'WHEN '+o.active+' THEN '+quoteJson({field,disposition:o.disposition.payload}));
  payloads.push('(CASE WHEN '+withholds+' THEN '+quoteJson({field,disposition:'withheld'})+' '+transformed.join(' ')+' ELSE '+quoteJson({field,disposition:'original'})+' END)');
 }
 const decision="SELECT CASE WHEN decision OPERATOR(pg_catalog.<>) E'permit'::pg_catalog.text COLLATE pg_catalog.\"C\" THEN decision "+checks.join(' ')+" ELSE E'permit'::pg_catalog.text END AS decision FROM candidate_policy_base";
 const disclosure=payloads.length?'pg_catalog.to_jsonb(ARRAY['+payloads.join(', ')+'])':"E'[]'::pg_catalog.jsonb";
 const sql='WITH '+fold.truthCte+', candidate_policy_base AS MATERIALIZED ('+fold.decisionSql+'), candidate_policy_final AS MATERIALIZED ('+decision+") SELECT decision, CASE WHEN decision OPERATOR(pg_catalog.=) E'permit'::pg_catalog.text COLLATE pg_catalog.\"C\" THEN "+disclosure+" ELSE E'[]'::pg_catalog.jsonb END AS disclosure FROM candidate_policy_final";
 if(sql.length>1_000_000)return fail();return Object.freeze({sql,ruleIds:fold.ruleIds});
}
