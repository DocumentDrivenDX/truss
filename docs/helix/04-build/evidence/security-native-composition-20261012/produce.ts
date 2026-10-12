import {lowerSecurityRowPredicate} from '../../../../../packages/postgresql/src/security-predicate';
import {composeSecurityRules} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/extensions/security/logic';
const ref=(elementId:string)=>({documentId:'domain',moduleId:'m',elementId});
const domain={scalarType:'boolean',nullability:'required',cardinality:'one',facets:{},allowedValues:null};
const effects=['permit','permit','require','forbid'] as const;
const names=['p1','p2','required','forbidden'];const target=ref('Resource'),subject=ref('Staff');
const sql=lowerSecurityRowPredicate({action:'read',target,subject,subjectLoginColumn:'native_login',
 types:[{type:target,keyId:'pk',keyFields:[{ref:ref('resourceId'),column:'id'}],fields:[{ref:ref('resourceId'),column:'id'}],home:{schema:'fixture',table:'resource'}},
 {type:subject,keyId:'pk',keyFields:[{ref:ref('staffId'),column:'id'}],fields:names.map(name=>({ref:ref(name),column:name})),home:{schema:'fixture',table:'staff'}}],
 logicalPlan:{version:'weft.security.logical-ir/0.1.0',rules:effects.map((effect,i)=>({id:'r'+i,effect,actions:['read'],target,disclosure:[],condition:{equal:[{field:{binding:'subject',field:ref(names[i]!),domain}},{constant:{field:ref(names[i]!),domain,literal:{boolean:true}}}]}}))}});
const truths=['T','F','U'] as const;const cases=[];
for(const a of truths)for(const b of truths)for(const c of truths)for(const d of truths){
 const values=[a,b,c,d];
 // Independent expected admission follows the governing truth table, not SQL.
 const expected=!values.includes('U')&&(a==='T'||b==='T')&&c==='T'&&d==='F';
 const decision=composeSecurityRules(values.map((truth,i)=>({effect:effects[i]!,truth}))).decision;
 if((decision==='permit')!==expected)throw Error('Original semantic oracle differs');
 cases.push({truths:values,expected,semanticDecision:decision});
}
console.log(JSON.stringify({sql,cases}));
