import {test,expect} from 'bun:test';
import {lowerCandidateSecurityCondition,lowerCandidateSecurityRuleFold,lowerCandidateSecurityDisclosure,type CandidateConditionScan} from '../packages/postgresql/src/security-candidate-condition';
import proof from './fixtures/security-original-graph-ir-formal.json';
const ref=(elementId:string)=>({documentId:'domain',moduleId:'m',elementId});
const raw=ref('Ownership'),graph={documentId:'domain',moduleId:'m',relationshipId:'WorksOn'};
const condition=proof.artifacts.find(a=>a.id==='mixed')!.rules[0]!.condition;
const scans:CandidateConditionScan[]=[{association:raw,home:{schema:'candidate',table:'ownership'},record:{owner:raw,keyId:'pk',keyFields:[ref('ownerId')],columns:['own_id']},endpoints:[]},{association:graph,home:{schema:'candidate',table:'works_on'},endpoints:[]}];
function walk(v:any){if(v&&typeof v==='object'){if(v.endpoint){const e=v.endpoint,scan=scans.find(s=>JSON.stringify(s.association)===JSON.stringify(e.association))!;if(!scan.endpoints.some(m=>m.role===e.role))(scan.endpoints as any[]).push({association:e.association,role:e.role,target:e.target,keyId:e.keyId,targetKeyFields:[ref(e.target.elementId.toLowerCase()+'Id')],carrier:e.carrier,columns:[e.role+'_key']});}else Object.values(v).forEach(walk);}}
walk(condition);
const input={condition,scans,subject:{target:ref('Staff'),keyId:'pk',keyFields:[ref('staffId')],parameters:[2]},resource:{target:ref('Resource'),keyId:'pk',keyFields:[ref('resourceId')],parameters:[1]}};
test('actual mixed compiler condition retains outer Project correlation',()=>{
 const sql=lowerCandidateSecurityCondition(input);expect(sql).toContain('"candidate_1"."project_key" OPERATOR(pg_catalog.=) "candidate_0"."project_key"');expect(sql).toContain('"candidate_0"."resource_key" OPERATOR(pg_catalog.=) $1');expect(sql).toContain('"candidate_1"."staff_key" OPERATOR(pg_catalog.=) $2');expect(sql).toContain('IS NULL');expect(sql).toContain('NULL::pg_catalog.bool');
});
test('source negation retains three valued quantifier SQL',()=>{const negated=proof.artifacts.find(a=>a.id==='mixed-negated')!.rules[0]!.condition;expect(lowerCandidateSecurityCondition({...input,condition:negated})).toStartWith('(NOT (CASE WHEN EXISTS');});
test('unknown profiles and substituted endpoint mappings refuse',()=>{
 expect(()=>lowerCandidateSecurityCondition({...input,scans:scans.slice(0,1)})).toThrow();
 const wrong=structuredClone(scans);wrong[1]!.endpoints[0]!.keyId='other';expect(()=>lowerCandidateSecurityCondition({...input,scans:wrong})).toThrow();
 expect(()=>lowerCandidateSecurityCondition({...input,subject:{...input.subject,parameters:[0]}})).toThrow();
 expect(()=>lowerCandidateSecurityCondition({...input,condition:{value:{context:{field:ref('active')}}}})).toThrow();
});
test('lexical slot collisions refuse and unsupported terms do not disappear',()=>{
 const collision=structuredClone(condition) as any;collision.exists.condition.and[1].exists.slot=0;expect(()=>lowerCandidateSecurityCondition({...input,condition:collision})).toThrow();
 expect(()=>lowerCandidateSecurityCondition({...input,condition:{and:[{literal:false},{equal:[{value:{field:{}}},{value:{field:{}}}]}]}})).toThrow();
});
test('array method substitution cannot turn False into True',()=>{
 let calls=0;const args:any=[{literal:false}];args.map=()=>{calls++;return ['TRUE'];};
 expect(()=>lowerCandidateSecurityCondition({condition:{and:args},scans:[]})).toThrow();expect(calls).toBe(0);
});
test('packet, nested scan, identity and array getters never run',()=>{
 for(const location of ['packet','scan','identity','array']){let calls=0;const changed:any=structuredClone(input);
  if(location==='packet')Object.defineProperty(changed,'scans',{enumerable:true,get(){calls++;return scans;}});
  if(location==='scan')Object.defineProperty(changed.scans[0].home,'table',{enumerable:true,get(){calls++;return 'ownership';}});
  if(location==='identity')Object.defineProperty(changed.subject,'parameters',{enumerable:true,get(){calls++;return [2];}});
  if(location==='array')Object.defineProperty(changed.condition.exists.condition.and,'0',{enumerable:true,get(){calls++;return {literal:true};}});
  expect(()=>lowerCandidateSecurityCondition(changed)).toThrow();expect(calls).toBe(0);
 }
});
test('unused ambiguous endpoint declarations refuse eagerly',()=>{
 const changed=structuredClone(scans);(changed[1]!.endpoints as any[]).push(structuredClone(changed[1]!.endpoints[0]));
 expect(()=>lowerCandidateSecurityCondition({...input,condition:{literal:true},scans:changed})).toThrow();
});
test('same nominal compound Key cannot cross ordered components',()=>{
 const fields=[ref('k1'),ref('k2')],mapping=(role:string,side:'source'|'target',columns:string[])=>({association:graph,role,target:ref('Project'),keyId:'compound',targetKeyFields:fields,carrier:{incidence:{side}},columns});
 const physical:CandidateConditionScan={association:graph,home:{schema:'candidate',table:'self_edge'},endpoints:[mapping('left','source',['left1','left2']),mapping('right','target',['right1','right2'])]};
 const endpoint=(role:string,side:'source'|'target')=>({endpoint:{binding:{variable:0},association:graph,role,target:ref('Project'),keyId:'compound',carrier:{incidence:{side}}}});
 const expression={exists:{slot:0,association:graph,witness:'opaqueExistential',condition:{equal:[endpoint('left','source'),endpoint('right','target')]}}};
 expect(lowerCandidateSecurityCondition({condition:expression,scans:[physical]})).toContain('"candidate_0"."left1" OPERATOR(pg_catalog.=) "candidate_0"."right1"');
 const changed=structuredClone(physical);changed.endpoints[1]!.targetKeyFields=[ref('k2'),ref('k1')];expect(()=>lowerCandidateSecurityCondition({condition:expression,scans:[changed]})).toThrow();
 expect(()=>lowerCandidateSecurityCondition({condition:{literal:true},scans:[changed]})).toThrow();
});
test('original Record Key metadata and all intrinsic mappings are checked',()=>{
 const malformed=structuredClone(condition) as any;malformed.exists.witness.recordKey.key=null;expect(()=>lowerCandidateSecurityCondition({...input,condition:malformed})).toThrow();
 const substituted=structuredClone(condition) as any;substituted.exists.witness.recordKey.key.fields[0].element='other';expect(()=>lowerCandidateSecurityCondition({...input,condition:substituted})).toThrow();
 const arity=structuredClone(condition) as any;arity.exists.witness.recordKey.key.fields.push({module:'m',element:'other'});expect(()=>lowerCandidateSecurityCondition({...input,condition:arity})).toThrow();
 expect(()=>lowerCandidateSecurityCondition({...input,condition:{literal:true},subject:{...input.subject,parameters:[0]}})).toThrow();
 expect(()=>lowerCandidateSecurityCondition({...input,condition:{literal:true},resource:{...input.resource,keyFields:[ref('other')]}})).toThrow();
});

test('supplied falsy intrinsic carriers are never omissions',()=>{for(const name of ['subject','resource'])for(const value of [null,false,0,''])expect(()=>lowerCandidateSecurityCondition({condition:{literal:true},scans:[],[name]:value} as any)).toThrow();});

test('shared homes require disjoint compatible typed selectors',()=>{
 const shared=structuredClone(scans);const raw=shared[0]!.home;if(!('table' in raw))throw Error('Expected raw fixture');shared[1]!.home={table:raw.table,schema:raw.schema};
 expect(()=>lowerCandidateSecurityCondition({...input,scans:shared})).toThrow();
 shared[0]!.discriminator={column:'type_id',carrier:'int4',value:'12'};shared[1]!.discriminator={column:'type_id',carrier:'int4',value:'11'};
 const sql=lowerCandidateSecurityCondition({...input,scans:shared});expect(sql).toContain(`"candidate_0"."type_id" OPERATOR(pg_catalog.=) E'12'::pg_catalog.int4`);expect(sql).toContain(`"candidate_1"."type_id" OPERATOR(pg_catalog.=) E'11'::pg_catalog.int4`);
 for(const patch of [{value:'12'},{column:'other'},{carrier:'int8' as const}]){const invalid=structuredClone(shared);invalid[1]!.discriminator={...invalid[1]!.discriminator!,...patch};expect(()=>lowerCandidateSecurityCondition({...input,condition:{literal:true},scans:invalid})).toThrow();}
});
test('selector bounds and malformed unused carriers refuse eagerly',()=>{
 for(const [carrier,value,valid] of [['int4','-2147483648',true],['int4','2147483647',true],['int4','2147483648',false],['int8','9223372036854775807',true],['int8','9223372036854775808',false],['int4','-0',false],['int4','1e0',false]] as const){const changed=structuredClone(scans);changed[0]!.discriminator={column:'type_id',carrier,value};if(valid)expect(()=>lowerCandidateSecurityCondition({...input,scans:changed})).not.toThrow();else expect(()=>lowerCandidateSecurityCondition({...input,condition:{literal:true},scans:changed})).toThrow();}
 const text=structuredClone(scans);text[0]!.discriminator={column:'type_id',carrier:'text',value:"a'\\b"};expect(lowerCandidateSecurityCondition({...input,scans:text})).toContain('COLLATE pg_catalog."C"');
 for(const invalid of [null,false,0,'']){const changed:any=structuredClone(scans);changed[0].discriminator=invalid;expect(()=>lowerCandidateSecurityCondition({...input,condition:{literal:true},scans:changed})).toThrow();}
});

test('scalar channels retain field ownership, context separation and exact text equality',()=>{
 const domain={scalarType:'string',nullability:'required',cardinality:'one',facets:{},allowedValues:null};
 const field=ref('label'),constant={value:{constant:{field,domain,literal:{string:"a'\\b"}}}},resource={value:{field:{binding:'resource',field,domain}}},context={value:{context:{field,domain}}};
 const packet={...input,condition:{and:[{equal:[resource,constant]},{equal:[context,constant]}]},values:[{binding:'resource' as const,owner:ref('Resource'),field,domain,parameter:3},{binding:'context' as const,field,domain,parameter:4}]};
 const sql=lowerCandidateSecurityCondition(packet);expect(sql).toContain('$3::pg_catalog.text COLLATE pg_catalog."C"');expect(sql).toContain('$4::pg_catalog.text COLLATE pg_catalog."C"');expect(sql).toContain("a\\'\\\\b");
 expect(()=>lowerCandidateSecurityCondition({...packet,values:packet.values.slice(0,1)})).toThrow();
 expect(()=>lowerCandidateSecurityCondition({...packet,values:[{...packet.values[0]!,owner:ref('Staff')},packet.values[1]!]})).toThrow();
 expect(()=>lowerCandidateSecurityCondition({...packet,values:[packet.values[0]!,{...packet.values[1]!,owner:ref('Resource')}]})).toThrow();
 expect(()=>lowerCandidateSecurityCondition({...packet,values:[...packet.values,packet.values[1]!]})).toThrow();
 expect(()=>lowerCandidateSecurityCondition({...packet,condition:{literal:true},values:[{...packet.values[0]!,parameter:0}]})).toThrow();
});
test('record scalar fields remain on the bound witness; opaque scalar access refuses',()=>{
 const domain={scalarType:'boolean',nullability:'required',cardinality:'one',facets:{},allowedValues:null},field=ref('active');
 const bound={value:{field:{binding:{variable:0},field,domain}}},constant={value:{constant:{field,domain,literal:{boolean:true}}}};
 const changed=structuredClone(input);(changed.scans[0] as any).fields=[{owner:raw,field,domain,column:'active'}];(changed.condition as any).exists.condition={equal:[bound,constant]};
 expect(lowerCandidateSecurityCondition(changed)).toContain('"candidate_0"."active" OPERATOR(pg_catalog.=) TRUE');
 const foreign=structuredClone(changed);(foreign.scans[0] as any).fields[0].owner=ref('Other');expect(()=>lowerCandidateSecurityCondition(foreign)).toThrow();
 const opaque=structuredClone(input);(opaque.scans[1] as any).fields=[{owner:raw,field,domain,column:'active'}];expect(()=>lowerCandidateSecurityCondition(opaque)).toThrow();
 for(const scalarType of ['integer','decimal','binary'])expect(()=>lowerCandidateSecurityCondition({...changed,condition:{equal:[constant,{value:{constant:{field,domain:{...domain,scalarType},literal:{boolean:true}}}}]}})).toThrow();
});
test('scalar declarations cannot contradict Key carriers or qualified field domains',()=>{
 const domain={scalarType:'string',nullability:'required',cardinality:'one',facets:{},allowedValues:null},field=ref('resourceId');
 const value={binding:'resource' as const,owner:ref('Resource'),field,domain,parameter:1};
 expect(()=>lowerCandidateSecurityCondition({...input,condition:{literal:true},values:[{...value,parameter:3}]})).toThrow();
 expect(()=>lowerCandidateSecurityCondition({...input,condition:{literal:true},values:[value,{binding:'context',field,domain:{...domain,scalarType:'boolean'},parameter:4}]})).toThrow();
 const rawFields=structuredClone(input);(rawFields.scans[0] as any).fields=[{owner:raw,field:ref('ownerId'),domain,column:'different'}];expect(()=>lowerCandidateSecurityCondition(rawFields)).toThrow();
 const member=(scans[0]!.endpoints[0]!.carrier as any).members.fields[0];(rawFields.scans[0] as any).fields=[{owner:raw,field:member,domain,column:'different'}];expect(()=>lowerCandidateSecurityCondition(rawFields)).toThrow();
 expect(lowerCandidateSecurityCondition({...input,condition:{literal:true},values:[value,{binding:'context',field,domain,parameter:4}]})).toContain('THEN TRUE ELSE NULL::pg_catalog.bool END)');
});

test('numeric constants normalize exactly without value-number conversion',()=>{
 const field=ref('salary'),base={nullability:'required',cardinality:'one',allowedValues:null};
 const term=(domain:any,literal:any)=>({value:{constant:{field,domain,literal}}});
 const sql=(domain:any,a:any,b:any)=>lowerCandidateSecurityCondition({scans:[],condition:{equal:[term(domain,a),term(domain,b)]}});
 const integer={...base,scalarType:'integer',facets:{}};
 expect(sql(integer,{integerToken:'9007199254740993'},{integerToken:'9007199254740993.0'})).toContain("E'9007199254740993'::pg_catalog.numeric");
 expect(sql(integer,{integerToken:'1e1000'},{integerToken:'10e999'})).toContain("E'1"+'0'.repeat(1000)+"'::pg_catalog.numeric");
 for(const value of ['1.1','01','+1','NaN','Infinity','1\n','1e65536'])expect(()=>sql(integer,{integerToken:value},{integerToken:'1'})).toThrow();
 expect(()=>sql(integer,{integerToken:9007199254740992},{integerToken:'1'})).toThrow();
 const decimal={...base,scalarType:'decimal',facets:{precision:20,scale:3}};
 expect(sql(decimal,{decimalToken:'9007199254740993.125'},{decimalToken:'9007199254740993125e-3'})).toContain("E'9007199254740993.125'::pg_catalog.numeric");
 expect(sql(decimal,{decimalToken:'-0.0000'},{decimalToken:'0e9999999999999999999999999999999999'})).toContain("E'0'::pg_catalog.numeric");
 for(const value of ['0.0001','999999999999999999.999'])expect(()=>sql(decimal,{decimalToken:value},{decimalToken:'1'})).toThrow();
 const signed={...integer,facets:{integerWidth:{bits:64,signed:true}}};
 expect(sql(signed,{integerToken:'-9223372036854775808'},{integerToken:'9223372036854775807'})).toContain("E'-9223372036854775808'");
 for(const value of ['-9223372036854775809','9223372036854775808'])expect(()=>sql(signed,{integerToken:value},{integerToken:'0'})).toThrow();
});
test('binary constants retain exact octets and empty value',()=>{
 const field=ref('blob'),domain={scalarType:'binary',nullability:'required',cardinality:'one',facets:{},allowedValues:null};
 const term=(binaryHex:any)=>({value:{constant:{field,domain,literal:{binaryHex}}}});
 const lower=(a:any,b:any)=>lowerCandidateSecurityCondition({scans:[],condition:{equal:[term(a),term(b)]}});
 expect(lower('00Ff','00ff')).toContain("pg_catalog.decode(E'00ff'");expect(lower('','')).toContain("pg_catalog.decode(E''");
 for(const value of ['0','a\n','gg','0x00',0])expect(()=>lower(value,'00')).toThrow();
});
test('native validity guards enclose negation and successful disjunctions',()=>{
 const field=ref('salary'),domain={scalarType:'integer',nullability:'required',cardinality:'one',facets:{integerWidth:{bits:64,signed:true}},allowedValues:null},term={value:{context:{field,domain}}},constant={value:{constant:{field,domain,literal:{integerToken:'1'}}}};
 const lower=(condition:any)=>lowerCandidateSecurityCondition({condition,scans:[],values:[{binding:'context',field,domain,parameter:3}]});
 for(const condition of [{not:{equal:[term,constant]}},{or:[{literal:true},{equal:[term,constant]}]},{literal:true}]){const sql=lower(condition);expect(sql).toStartWith('(CASE WHEN (');expect(sql).toContain("E'NaN'::pg_catalog.numeric");expect(sql).toContain('pg_catalog.trunc');expect(sql).toContain("E'-9223372036854775808'");expect(sql).toEndWith('ELSE NULL::pg_catalog.bool END)');}
});
test('rule fold retains all matching effects and unknown precedence',()=>{
 const rule=(id:string,effect:string,condition:any,action='read',target=ref('Resource'))=>({id,effect,condition,actions:[action],target,disclosure:[]});
 const rules=[rule('p','permit',{literal:true}),rule('r','require',{literal:true}),rule('f','forbid',{literal:false}),rule('unmatched','forbid',{literal:true},'write')];
 const fold=lowerCandidateSecurityRuleFold({rules,target:ref('Resource'),action:'read',scans:[]});expect(fold.ruleIds).toEqual(['p','r','f']);expect(fold.sql).toContain('AS MATERIALIZED');expect(fold.sql.indexOf('truth IS NULL')).toBeLessThan(fold.sql.indexOf("THEN E'indeterminate'"));expect(fold.sql).toContain("E'forbid'");expect(Object.isFrozen(fold.ruleIds)).toBe(true);
 expect(lowerCandidateSecurityRuleFold({rules,target:ref('Resource'),action:'delete',scans:[]}).sql).toContain("E'deny'");
 expect(()=>lowerCandidateSecurityRuleFold({rules:[rules[0],rules[0]],target:ref('Resource'),action:'read',scans:[]})).toThrow();
 expect(()=>lowerCandidateSecurityRuleFold({rules:[{...rules[0],disclosure:[[ref('salary'),'withheld']]}],target:ref('Resource'),action:'read',scans:[]})).toThrow();
 expect(()=>lowerCandidateSecurityRuleFold({rules:[{...rules[0],effect:'unknown'}],target:ref('Resource'),action:'read',scans:[]})).toThrow();
 let calls=0;const bad:any={rules,target:ref('Resource'),action:'read',scans:[]};Object.defineProperty(bad,'rules',{enumerable:true,get(){calls++;return rules;}});expect(()=>lowerCandidateSecurityRuleFold(bad)).toThrow();expect(calls).toBe(0);
});
test('splitting a qualified-field domain contradiction across rules refuses',()=>{
 const field=ref('salary'),base={nullability:'required',cardinality:'one',facets:{},allowedValues:null},term=(scalarType:string,literal:any)=>({value:{constant:{field,domain:{...base,scalarType},literal}}});
 const rule=(id:string,t:any)=>({id,effect:'permit',actions:['read'],target:ref('Resource'),condition:{equal:[t,t]},disclosure:[]});
 expect(()=>lowerCandidateSecurityRuleFold({rules:[rule('i',term('integer',{integerToken:'1'})),rule('b',term('boolean',{boolean:true}))],target:ref('Resource'),action:'read',scans:[]})).toThrow();
});
test('disclosure SQL applies protected defaults and withhold before mask conflicts',()=>{
 const target=ref('Resource'),field=ref('salary'),domain={scalarType:'integer',nullability:'required',cardinality:'one',facets:{},allowedValues:null};
 const fields=[{owner:target,field,domain,protection:'protected' as const}],rule=(id:string,payload:any)=>({id,effect:'permit',actions:['read'],target,condition:{literal:true},disclosure:payload===undefined?[]:[[field,payload]]});
 const mask=(token:string)=>({transformed:{transform:'constant',version:'0.1.0',outputField:field,domain,literal:{integerToken:token}}});
 const lower=(rules:any[])=>lowerCandidateSecurityDisclosure({rules,target,action:'read',scans:[],fields,outputFields:[field]}).sql;
 expect(lower([rule('p',undefined)])).toContain("THEN E'indeterminate'");expect(lower([rule('a',mask('1')),rule('b',mask('2'))])).toContain("THEN E'conflict'");expect(lower([rule('a',mask('1')),rule('b',mask('1.0'))])).not.toContain("THEN E'conflict'");
 expect(lower([rule('a',mask('1')),rule('b',mask('2')),rule('w','withheld')])).toContain('WHEN (NOT (');
 expect(()=>lower([rule('a',{transformed:{...mask('1').transformed,version:'unknown'}})])).toThrow();
 expect(()=>lowerCandidateSecurityDisclosure({rules:[rule('a','original')],target,action:'read',scans:[],fields:[{...fields[0]!,owner:ref('Staff')}],outputFields:[field]})).toThrow();
 expect(()=>lowerCandidateSecurityDisclosure({rules:[rule('a',mask('1'))],target,action:'read',scans:[],fields:[{...fields[0]!,domain:{...domain,scalarType:'boolean'}}],outputFields:[field]})).toThrow();
});
test('disclosure SQL preserves ordered fields beyond the PostgreSQL function argument limit',()=>{
 const target=ref('Resource'),domain={scalarType:'integer',nullability:'required',cardinality:'one',facets:{},allowedValues:null};
 for(const count of [100,101]){
  const fields=Array.from({length:count},(_,i)=>({owner:target,field:ref('boundary'+i),domain,protection:'unprotected' as const}));
  const {sql}=lowerCandidateSecurityDisclosure({rules:[{id:'p',effect:'permit',actions:['read'],target,condition:{literal:true},disclosure:[]}],target,action:'read',scans:[],fields,outputFields:fields.map(f=>f.field)});
  expect(sql).toContain('pg_catalog.to_jsonb(ARRAY[');
  expect(sql).not.toContain('jsonb_build_array');
  expect(sql.indexOf('boundary0')).toBeLessThan(sql.indexOf('boundary'+(count-1)));
 }
});

test('issued opaque sources preserve local validity outside negation and successful siblings',async()=>{
 const {createCandidateGraphSource}=await import('../packages/postgresql/src/security-graph-source');
 const source=createCandidateGraphSource({kind:'edge',typeId:'2',propertyOwnerTypeId:null,fields:[]});
 const scan:CandidateConditionScan={association:graph,home:{source},endpoints:[]};
 const exists={exists:{slot:0,association:graph,witness:'opaqueExistential',condition:{literal:true}}};
 const sql=lowerCandidateSecurityCondition({condition:{or:[{literal:true},{not:exists}]},scans:[scan]});
 expect(sql).toStartWith('(CASE WHEN');expect(sql).toContain(source.validitySql);expect(sql).toContain('FROM ('+source.sql+') AS "candidate_0"');expect(sql).toEndWith('ELSE NULL::pg_catalog.bool END)');
 // Even an unused source must satisfy the declared complete scan cut.
 expect(lowerCandidateSecurityCondition({condition:{literal:true},scans:[scan]})).toContain(source.validitySql);
 const target=ref('Project'),rule={id:'opaque',effect:'permit',actions:['read'],target,condition:exists,disclosure:[]};
 expect(lowerCandidateSecurityRuleFold({rules:[rule],target,action:'read',scans:[scan]}).sql).toContain(source.validitySql);
 expect(lowerCandidateSecurityDisclosure({rules:[rule],target,action:'read',scans:[scan],fields:[],outputFields:[]}).sql).toContain(source.validitySql);
});
test('copied graph SQL and home accessors cannot enter candidate condition lowering',async()=>{
 const {createCandidateGraphSource}=await import('../packages/postgresql/src/security-graph-source');
 const source=createCandidateGraphSource({kind:'edge',typeId:'2',propertyOwnerTypeId:null,fields:[]});
 const request=(home:unknown)=>({condition:{literal:true},scans:[{association:graph,home,endpoints:[]}]});
 expect(()=>lowerCandidateSecurityCondition(request({source:{...source}}) as any)).toThrow();
 let calls=0;const home={};Object.defineProperty(home,'source',{enumerable:true,get(){calls++;return source;}});
 expect(()=>lowerCandidateSecurityCondition(request(home) as any)).toThrow();expect(calls).toBe(0);
 expect(()=>lowerCandidateSecurityCondition(request({source,schema:'raw',table:'edges'}) as any)).toThrow();
});

test('native population identity survives keyed and property projection wrappers',async()=>{
 const {createCandidateGraphSource,createCandidateGraphEndpointKeys}=await import('../packages/postgresql/src/security-graph-source');
 const base=createCandidateGraphSource({kind:'edge',typeId:'2',propertyOwnerTypeId:null,fields:[]});
 const keyed=createCandidateGraphEndpointKeys({source:base,sourceKey:{typeId:'3',keyNumber:'1',namespaceHex:'00'},targetKey:{typeId:'4',keyNumber:'1',namespaceHex:'00'}});
 const other={...graph,relationshipId:'Other'},packet=(a:typeof base,b:typeof base)=>({condition:{literal:true},scans:[{association:graph,home:{source:a},endpoints:[]},{association:other,home:{source:b},endpoints:[]}]});
 expect(()=>lowerCandidateSecurityCondition(packet(base,base))).toThrow();
 expect(()=>lowerCandidateSecurityCondition(packet(base,keyed))).toThrow();
 const project=(column:string)=>createCandidateGraphSource({kind:'edge',typeId:'5',propertyOwnerTypeId:'6',fields:[{propertyId:'7',column,scalar:'boolean'}]});
 expect(()=>lowerCandidateSecurityCondition(packet(project('a'),project('b')))).toThrow();
 const distinct=createCandidateGraphSource({kind:'edge',typeId:'8',propertyOwnerTypeId:null,fields:[]});
 expect(lowerCandidateSecurityCondition(packet(base,distinct))).toContain(distinct.validitySql);
});
