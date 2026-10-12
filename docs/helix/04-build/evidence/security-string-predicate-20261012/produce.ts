import {lowerSecurityRowPredicate} from '../../../../../packages/postgresql/src/security-predicate';
const ref=(elementId:string)=>({documentId:'domain',moduleId:'m',elementId});
const domain={scalarType:'string',nullability:'required',cardinality:'one',facets:{},allowedValues:null};
const target=ref('Resource'),subject=ref('Staff'),field=ref('staffId');
const input=(value:string)=>({action:'read',target,subject,subjectLoginColumn:'native_login',
 types:[{type:target,keyId:'pk',keyFields:[{ref:ref('resourceId'),column:'id'}],fields:[{ref:ref('resourceId'),column:'id'}],home:{schema:'fixture',table:'resource'}},
 {type:subject,keyId:'pk',keyFields:[{ref:field,column:'id'}],fields:[{ref:field,column:'id'}],home:{schema:'fixture',table:'staff'}}],
 logicalPlan:{version:'weft.security.logical-ir/0.1.0',rules:[{id:'allow',effect:'permit',actions:['read'],target,disclosure:[],condition:{equal:[{field:{binding:'subject',field,domain}},{constant:{field,domain,literal:{string:value}}}]}}]}});
const values=['','λ','😀',"quote'\\slash"];
const results=values.map(value=>{try{return {value,sql:lowerSecurityRowPredicate(input(value))};}catch{return {value,refused:true};}});
for(const value of ['\uD800','\uDC00','a\0b']){let refused=false;try{lowerSecurityRowPredicate(input(value));}catch{refused=true;}if(!refused)throw Error('Invalid native UTF8/text admitted');}
console.log(JSON.stringify(results));
