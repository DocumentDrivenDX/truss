// SPDX-License-Identifier: MIT OR Apache-2.0
/** Conditional semantic oracle over actual captured fixture; no native authority. */
import {evaluateSecurityAccess,type SecurityFact,type SecurityFactCut} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/extensions/security/evaluate';
import {inspectSecurityPolicy} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/extensions/security/policy';
import {checkSchemaLiteral} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/model/schema-literals';
if(Bun.argv.length>3||(Bun.argv[2]!==undefined&&Bun.argv[2]!=='--evaluate'))throw Error('Exact oracle mode required');
const exercising=Bun.argv[2]!== '--evaluate';
const base='docs/helix/03-test/fixtures/security-public-relationship/';
const resolution=await Bun.file(base+'resolution.json').json();
const raw=await Bun.stdin.text();if(new TextEncoder().encode(raw).length>1048576)throw Error('Bounded original fixture required');
const input=JSON.parse(raw);if(!input||JSON.stringify(Object.keys(input).sort())!==JSON.stringify(['policyFacts','queryRelationshipOccurrences','queryResourceIdentities'].sort()))throw Error('Exact original projection frame required');
const groups=new Map<string,SecurityFact[]>(),coverage:any[]=[];
const declared=[...resolution.ontology.entities,...resolution.ontology.associations];
for(const g of input.policyFacts){
 const matches=Object.entries({Staff:'staffId',Project:'projectId',Resource:'resourceId',Assignment:'assignmentId',Ownership:'ownerId'}).filter(([,field])=>g.fields.some((e:any)=>JSON.stringify(e[0])===JSON.stringify(['domain','m',field])));
 if(matches.length!==1)throw Error('Unambiguous original group identity required');const name=matches[0]![0];
 const selected=declared.find((d:any)=>d.type.elementId===name);if(!selected||groups.has(name)||g.rows.length>100)throw Error('Complete original fixture binding required');
 const rows=g.rows.map((row:any)=>{
  if(row.length!==g.fields.length)throw Error('Original row width required');
  const fields=g.fields.map((entry:any,i:number)=>{
   const ref={documentId:entry[0][0],moduleId:entry[0][1],elementId:entry[0][2]};
   if(![16,25].includes(entry[2])||typeof row[i]!=='string')throw Error('Exact native scalar carrier required');
   const value=entry[2]===16?{boolean:row[i]==='true'}:{string:row[i]};
   if(entry[2]===16&&!['true','false'].includes(row[i]))throw Error('Original boolean spelling required');
   const doc=resolution.documents.find((d:any)=>d.document.id===ref.documentId).document;
   checkSchemaLiteral(doc,doc.modules.find((m:any)=>m.id===ref.moduleId).elements.find((e:any)=>e.id===ref.elementId),value);return {field:ref,value};
  });
  const keyField=selected.fields.find((f:any)=>f.ref.elementId===({Staff:'staffId',Project:'projectId',Resource:'resourceId',Assignment:'assignmentId',Ownership:'ownerId'} as any)[name]).ref;
  return {type:selected.type,key:[fields.find((f:any)=>f.field.elementId===keyField.elementId).value],fields,absent:[]};
 });
 groups.set(name,rows);coverage.push({type:selected.type,complete:true,fields:g.fields.map((e:any)=>({documentId:e[0][0],moduleId:e[0][1],elementId:e[0][2]}))});
}
if(groups.size!==declared.length)throw Error('Complete policy capture required');
const resources=groups.get('Resource')!,identities=new Map(input.queryResourceIdentities.map((r:any)=>[r[0],r[2]]));
if(identities.size!==input.queryResourceIdentities.length||new Set(input.queryResourceIdentities.map((r:any)=>r[2])).size!==identities.size||identities.size!==resources.length)throw Error('Exact unique native resource identities required');
const edgeIds=new Set();for(const edge of input.queryRelationshipOccurrences){if(!Array.isArray(edge)||edge.length!==6||edge.some((v:any)=>typeof v!=='string')||edgeIds.has(edge[0])||!identities.has(edge[2])||!identities.has(edge[4]))throw Error('Complete query occurrence endpoints required');edgeIds.add(edge[0]);}
const results:any[]=[];
for(const variant of ['policy','policy-observation-denied']){
 const policy=await Bun.file(base+variant+'.json').json(),checked=inspectSecurityPolicy(policy,resolution);if(!checked.valid||!checked.complete)throw Error('Original policy source required');
 for(const subject of ['Alice','Bob','Outsider']){
  const cut:SecurityFactCut={trusted:true,generation:'owned-traversal-oracle',expectedGeneration:'owned-traversal-oracle',policyId:policy.id,policyRevision:policy.revision,ontologyDocumentId:resolution.ontology.documentId,ontologyRevision:resolution.ontology.revision,subjects:groups.get('Staff')!.filter(f=>(f.key[0] as any).string===subject),facts:[...groups].filter(([n])=>!['Resource','Staff'].includes(n)).flatMap(([,r])=>r),coverage,context:[],maxFacts:100,maxSteps:10000};
  const decision=(resource:SecurityFact,action:string)=>{const r=evaluateSecurityAccess(policy,resolution,cut,{action,output:[]},resource);if(['indeterminate','conflict'].includes(r.decision))throw Error('Complete original decision required');return r.decision==='permit';};
  const eligible=new Set(resources.filter(r=>decision(r,'read')).map(r=>(r.key[0] as any).string));
  const observed=resources.filter(r=>{
   const key=(r.key[0] as any).string;
   return eligible.has(key)&&decision(r,'observeResourceRelations')&&input.queryRelationshipOccurrences.some((e:any)=>identities.get(e[2])===key&&identities.get(e[4])==='RB'&&eligible.has('RB'));
  }).map(r=>(r.key[0] as any).string);
  const expected=variant==='policy'&&subject==='Bob'?['RB']:[];
  if(exercising&&JSON.stringify(observed)!==JSON.stringify(expected))throw Error(JSON.stringify({variant,subject,observed,expected}));
  results.push({variant,subject,...(exercising?{expected}:{}),observed});
 }
}
console.log(JSON.stringify({status:exercising?'conditional-semantic-oracle-passed':'conditional-semantic-oracle-evaluated',results,securityReady:false,scope:'Original UMF policy read and observation actions; authored existential assembly over supplied captured edges. No native caller/cut/compiler/publication refinement.'}));
