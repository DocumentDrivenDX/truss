import {test,expect} from 'bun:test';
import {createCandidateGraphSource} from '../packages/postgresql/src/security-graph-source';
import {lowerSecurityRowPredicate,type SecurityPredicateType} from '../packages/postgresql/src/security-predicate';
const ref=(elementId:string)=>({documentId:'domain',moduleId:'m',elementId});
const source=createCandidateGraphSource({kind:'edge',typeId:'2',propertyOwnerTypeId:'1',fields:[{propertyId:'3',column:'active',scalar:'boolean'}]});
const domain={scalarType:'boolean',nullability:'required',cardinality:'one',facets:{},allowedValues:null};
const request=()=>({logicalPlan:{version:'weft.security.logical-ir/0.1.0',rules:[{id:'active',effect:'permit',actions:['read'],target:ref('Project'),disclosure:[],condition:{exists:{slot:0,association:ref('Assignment'),condition:{equal:[{field:{binding:{variable:0},field:ref('active'),domain}},{constant:{field:ref('active'),domain,literal:{boolean:true}}}]}}}}]},action:'read',target:ref('Project'),subject:ref('Employee'),subjectLoginColumn:'login',types:[{type:ref('Project'),keyId:'code',keyFields:[{ref:ref('code'),column:'code'}],fields:[],home:{schema:'raw',table:'project'}},{type:ref('Employee'),keyId:'code',keyFields:[],fields:[],home:{schema:'raw',table:'employee'}},{type:ref('Assignment'),keyId:'code',keyFields:[],fields:[{ref:ref('active'),column:'active'}],home:{source}}] as SecurityPredicateType[]});
test('candidate association lowering carries local source validity and same-row field test',()=>{
 const sql=lowerSecurityRowPredicate(request());
 expect(sql).toContain(source.sql);expect(sql).toContain(source.validitySql);
 expect(sql).toContain('"association_0"."active" OPERATOR(pg_catalog.=) TRUE');
 expect(sql).toContain('IS TRUE AND');
});
test('copied source or source metadata accessor cannot enter lowering',()=>{
 const copied=request();copied.types[2]!.home={source:{...source}};
 expect(()=>lowerSecurityRowPredicate(copied)).toThrow();
 let calls=0;const accessor=request();Object.defineProperty(accessor.types[2]!.home,'source',{enumerable:true,get(){calls++;return source;}});
 expect(()=>lowerSecurityRowPredicate(accessor)).toThrow();expect(calls).toBe(0);
});
