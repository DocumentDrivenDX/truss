import {createCandidateGraphSource} from '../../packages/postgresql/src/security-graph-source';
import {lowerCandidateSecurityRuleFold,lowerCandidateSecurityDisclosure,type CandidateConditionScan} from '../../packages/postgresql/src/security-candidate-condition';
const packet=await Bun.stdin.json();const ref=(elementId:string)=>({documentId:'adoc',moduleId:'m',elementId});
const objects:Record<string,ReturnType<typeof createCandidateGraphSource>>={};
for(const [name,raw] of Object.entries(packet.records) as [string,any][])objects[name]=createCandidateGraphSource({kind:'object',typeId:raw.typeId,propertyOwnerTypeId:raw.typeId,fields:Object.entries(raw.fields).map(([column,f]:[string,any])=>({propertyId:f.id,column,scalar:f.scalar}))});
const edges:Record<string,{sql:string;validitySql:string}>={};
for(const [name,r] of Object.entries(packet.links) as [string,any][]){
 const edge=createCandidateGraphSource({kind:'edge',typeId:r.id,propertyOwnerTypeId:null,fields:[]});
 const from=` FROM (${edge.sql}) e LEFT JOIN (${objects[r.source]!.sql}) s ON e.source_id=s.native_id AND e.source_type=s.native_type LEFT JOIN (${objects[r.target]!.sql}) t ON e.target_id=t.native_id AND e.target_type=t.native_type`;
 edges[name]={sql:'SELECT e.native_id AS occurrence_id,s.code AS source_code,t.code AS target_code'+from,validitySql:`SELECT (((SELECT valid FROM (${edge.validitySql}) v)::bool) AND NOT EXISTS(SELECT 1${from} WHERE s.native_id IS NULL OR t.native_id IS NULL))::text AS valid`};
}
const domain={scalarType:'boolean',nullability:'required',cardinality:'one',facets:{},allowedValues:null};
const association=(name:string)=>({documentId:'adoc',moduleId:'m',relationshipId:name});
const endpoint=(slot:number,name:string,side:'source'|'target',target:string)=>({endpoint:{binding:{variable:slot},association:association(name),role:side,target:ref(target),keyId:'pk',carrier:{incidence:{side}}}});
const identity=(binding:unknown,target:string)=>({value:{identity:{binding,target:ref(target),keyId:'pk'}}});
const eq=(a:unknown,b:unknown)=>({equal:[a,b]});
const opaque=(slot:number,name:string,condition:unknown)=>({exists:{slot,association:association(name),witness:'opaqueExistential',condition}});
const condition={exists:{slot:0,association:ref('Assignment'),witness:{recordKey:{owner:ref('Assignment'),keyId:'pk',key:{id:'pk',name:'primary',primary:true,fields:[{module:'m',element:'Assignment-code'}]}}},condition:{and:[
 eq({value:{field:{binding:{variable:0},field:ref('Assignment-active'),domain}}},{value:{constant:{field:ref('Assignment-active'),domain,literal:{boolean:true}}}}),
 opaque(1,'staff_assignment',{and:[eq(endpoint(1,'staff_assignment','source','Staff'),identity('subject','Staff')),eq(endpoint(1,'staff_assignment','target','Assignment'),identity({variable:0},'Assignment')),
 opaque(2,'assignment_project',{and:[eq(endpoint(2,'assignment_project','source','Assignment'),identity({variable:0},'Assignment')),
 opaque(3,'resource_project',{and:[eq(endpoint(3,'resource_project','source','Resource'),identity('resource','Resource')),eq(endpoint(3,'resource_project','target','Project'),endpoint(2,'assignment_project','target','Project'))]})]})]})]}}};
const scans:CandidateConditionScan[]=[{association:ref('Assignment'),home:{schema:'ontology_fixture',table:'assignment'},record:{owner:ref('Assignment'),keyId:'pk',keyFields:[ref('Assignment-code')],columns:['code']},endpoints:[],fields:[{owner:ref('Assignment'),field:ref('Assignment-active'),domain,column:'active'}]}];
for(const name of ['staff_assignment','assignment_project','resource_project']){
 const r=packet.links[name];scans.push({association:association(name),home:{schema:'ontology_fixture',table:name},endpoints:(['source','target'] as const).map(side=>({association:association(name),role:side,target:ref(r[side]),keyId:'pk',targetKeyFields:[ref(r[side]+'-code')],carrier:{incidence:{side}},columns:[side+'_code']}))});
}
const fold=lowerCandidateSecurityRuleFold({rules:[{id:'membership',effect:'permit',actions:['read'],target:ref('Resource'),disclosure:[],condition}],action:'read',target:ref('Resource'),scans,resource:{target:ref('Resource'),keyId:'pk',keyFields:[ref('Resource-code')],parameters:[1]},subject:{target:ref('Staff'),keyId:'pk',keyFields:[ref('Staff-code')],parameters:[2]}});
const predicateSql='('+fold.sql+') OPERATOR(pg_catalog.=) '+"E'permit'::pg_catalog.text";
const flatFold=lowerCandidateSecurityRuleFold({rules:[{id:'membership',effect:'permit',actions:['read'],target:ref('Resource'),disclosure:[],condition}],action:'read',target:ref('Resource'),scans:scans.map(scan=>({...scan,home:{schema:'relational_fixture',table:(scan.home as {table:string}).table}})),resource:{target:ref('Resource'),keyId:'pk',keyFields:[ref('Resource-code')],parameters:[1]},subject:{target:ref('Staff'),keyId:'pk',keyFields:[ref('Staff-code')],parameters:[2]}});
const stringDomain={scalarType:'string',nullability:'required',cardinality:'one',facets:{},allowedValues:null};
const mask={transformed:{transform:'constant',version:'0.1.0',outputField:ref('Resource-secret'),domain:stringDomain,literal:{string:'MASKED'}}};
const disclosureInput={rules:[{id:'membership',effect:'permit',actions:['read'],target:ref('Resource'),disclosure:[[ref('Resource-secret'),mask]],condition}],action:'read',target:ref('Resource'),scans,resource:{target:ref('Resource'),keyId:'pk',keyFields:[ref('Resource-code')],parameters:[1]},subject:{target:ref('Staff'),keyId:'pk',keyFields:[ref('Staff-code')],parameters:[2]},fields:[{owner:ref('Resource'),field:ref('Resource-code'),domain:stringDomain,protection:'unprotected' as const},{owner:ref('Resource'),field:ref('Resource-secret'),domain:stringDomain,protection:'protected' as const},{owner:ref('Assignment'),field:ref('Assignment-active'),domain,protection:'unprotected' as const}],outputFields:[ref('Resource-code'),ref('Resource-secret')]};
const graphDisclosure=lowerCandidateSecurityDisclosure(disclosureInput);
const flatDisclosure=lowerCandidateSecurityDisclosure({...disclosureInput,scans:scans.map(scan=>({...scan,home:{schema:'relational_fixture',table:(scan.home as {table:string}).table}}))});
console.log(JSON.stringify({objects,edges,predicateSql,condition,scans,fold,flatFold,graphDisclosure,flatDisclosure}));
