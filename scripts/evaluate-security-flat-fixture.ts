// SPDX-License-Identifier: MIT OR Apache-2.0
/** Owned flat conformance fixture only; trusted=true is not production authority. */
import {securityFixture,ref} from '/Users/erik/.codex/worktrees/security-main-integration/umf/tests/security/fixture';
import {evaluateSecurityAccess,type SecurityFact,type SecurityFactCut} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/extensions/security/evaluate';
import type {CoreLiteral} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/model/schema-literals';
const model=securityFixture();
for(const [name,value] of [['policy',model.policy],['resolution',model.resolution]] as const){
 if(await Bun.file('docs/helix/04-build/evidence/security-fact-requirements/'+name+'.json').text()!==JSON.stringify(value)+'\n')throw Error('Original fixture source correspondence required');
}
const raw=await Bun.stdin.text();if(raw.length>1048576)throw Error('Bounded fixture capture required');
const input=JSON.parse(raw);const names=['Staff','Project','Resource','Ownership','Assignment'];
if(!input||Array.isArray(input)||Object.keys(input).sort().join(',')!==names.slice().sort().join(','))throw Error('Exact fixture capture required');
const specs={Staff:['staffId'],Project:['projectId'],Resource:['resourceId','salary'],Ownership:['ownerId','ownerResource','ownerProject'],Assignment:['assignmentId','assignmentStaff','assignmentProject','active']};
const facts={} as Record<string,SecurityFact[]>;
for(const type of names){
 const fields=specs[type as keyof typeof specs],rows=input[type];
 if(!Array.isArray(rows)||rows.length>100)throw Error('Bounded native fixture rows required');
 facts[type]=rows.map((row:unknown)=>{
  if(!Array.isArray(row)||row.length!==fields.length||row.some(v=>typeof v!=='string'))throw Error('Exact native text fixture descriptor required');
  return {type:ref(type),key:[{string:row[0]}],absent:[],fields:fields.map((name,index)=>{
   const value=row[index];let literal:CoreLiteral;
   if(name==='active'){if(value!=='true'&&value!=='false')throw Error('Native boolean spelling required');literal={boolean:value==='true'};}
   else if(name==='salary'){if(!/^-?(0|[1-9][0-9]*)$/.test(value))throw Error('Native integer token required');literal={integerToken:value};}
   else literal={string:value};
   return {field:ref(name),value:literal};
  })};
 });
}
if(facts.Resource!.length!==1)throw Error('Selected fixture resource required');
const cut:SecurityFactCut={trusted:true,generation:'owned-fixture',expectedGeneration:'owned-fixture',policyId:model.policy.id,policyRevision:model.policy.revision,ontologyDocumentId:model.resolution.ontology.documentId,ontologyRevision:model.resolution.ontology.revision,subjects:facts.Staff!,facts:[...facts.Project!,...facts.Ownership!,...facts.Assignment!],coverage:[...model.resolution.ontology.entities,...model.resolution.ontology.associations].map(t=>({type:t.type,complete:true,fields:t.fields.map(f=>f.ref)})),context:[],maxFacts:100,maxSteps:10000};
console.log(JSON.stringify(evaluateSecurityAccess(model.policy,model.resolution,cut,{action:'read',output:[ref('salary')]},facts.Resource![0]!)));
