/** Flat table-per-record fixture reconstruction from fixed captured identity cells.
 * No authority is issued; trusted=true is an owned administrative fixture premise.
 */
import {securityFixture,ref} from '/Users/erik/.codex/worktrees/security-main-integration/umf/tests/security/fixture';
import {securityIdentityTransportDependencies} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/extensions/security/dependencies';
import {evaluateSecurityAccess,type SecurityFact,type SecurityFactCut} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/extensions/security/evaluate';
import {checkSchemaLiteral,type CoreLiteral} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/model/schema-literals';
import {encodeCoreKeyTuple,type CoreKeyTupleValue} from '/Users/erik/.codex/worktrees/security-main-integration/umf/src/model/key-tuple';
const model=securityFixture(),transport=securityIdentityTransportDependencies(model.policy,model.resolution);
const base='docs/helix/04-build/evidence/security-identity-requirements';
for(const [name,value] of [['policy',model.policy],['resolution',model.resolution],['transport',transport]] as const)
 if(await Bun.file(base+'/'+name+'.json').text()!==JSON.stringify(value)+'\n')throw Error('Original identity source correspondence required');
const raw=await Bun.stdin.text();if(raw.length>1048576)throw Error('Bounded original captured fixture required');const input=JSON.parse(raw);const bound=typeof input==='object'&&input!==null&&!Array.isArray(input);
if(bound&&(JSON.stringify(Object.keys(input).sort())!==JSON.stringify(['cells','subjectKey'])||!Array.isArray(input.subjectKey)))throw Error('Closed original caller fixture input required');
const cells=bound?input.cells:input;
if(!Array.isArray(cells)||cells.length!==transport.records.length)throw Error('Complete selected record captures required');
const id=(r:{documentId:string;moduleId:string;elementId:string})=>JSON.stringify([r.documentId,r.moduleId,r.elementId]);
const required=new Set(transport.fields.map(id));const types=[...model.resolution.ontology.entities,...model.resolution.ontology.associations];
const groups=new Map<string,SecurityFact[]>();const coverage:SecurityFactCut['coverage']=[];const used=new Set<number>();
for(const record of transport.records){
 const type=types.find(t=>id(t.type)===id(record.type))!;const owned=type.fields.map(f=>f.ref).filter(r=>required.has(id(r)));
 const candidates=cells.map((g:any,index:number)=>({g,index})).filter(({g}:any)=>Array.isArray(g.fields)&&g.fields.length===owned.length&&owned.every(r=>g.fields.some((c:any)=>JSON.stringify(c[0])===id(r))));
 if(candidates.length!==1||used.has(candidates[0]!.index))throw Error('Unambiguous explicit single-table record binding required');
 const {g,index}=candidates[0]!;used.add(index);
 if(!Array.isArray(g.rows)||g.rows.length>100||!Array.isArray(g.associations))throw Error('Bounded complete captured rows required');
 const associated=model.resolution.ontology.associations.some(a=>id(a.type)===id(record.type));
 if(JSON.stringify(g.associations)!==JSON.stringify(associated?[[record.type.documentId,record.type.moduleId,record.type.elementId]]:[]))throw Error('Original association presence binding required');
 const names=g.fields.map((c:any)=>JSON.stringify(c[0]));if(new Set(names).size!==names.length)throw Error('Repeated original field capture');
 const facts:SecurityFact[]=g.rows.map((row:any)=>{
  if(!Array.isArray(row)||row.length!==g.fields.length)throw Error('Original captured row width required');
  const fields=owned.map(field=>{
   const position=names.indexOf(id(field)),value=row[position],oid=g.fields[position][2];let literal:CoreLiteral;
   if(value===null)literal=null;
   else if(typeof value!=='string')throw Error('Original text/NULL capture required');
   else if(oid===25)literal={string:value};
   else if(oid===16&&(value==='true'||value==='false'))literal={boolean:value==='true'};
   else if(oid===20&&/^-?(0|[1-9][0-9]*)$/.test(value))literal={integerToken:value};
   else throw Error('Supported exact native literal required');
   const doc=model.resolution.documents.find(d=>d.document.id===field.documentId)!.document;
   const definition=doc.modules.find(m=>m.id===field.moduleId)!.elements.find(e=>e.id===field.elementId)!;
   checkSchemaLiteral(doc,definition,literal);return {field,value:literal};
  });
  const key=record.keyFields.map(ref=>fields.find(f=>id(f.field)===id(ref))!.value);
  const doc=model.resolution.documents.find(d=>d.document.id===record.type.documentId)!.document;
  const originalKey=encodeCoreKeyTuple(doc,{module:record.type.moduleId,element:record.type.elementId,key:record.keyId},key as CoreKeyTupleValue[]);
  return {type:record.type,key:originalKey.values,fields,absent:[]};
 });
 groups.set(id(record.type),facts);coverage.push({type:record.type,complete:true,fields:owned});
}
if(used.size!==cells.length)throw Error('Foreign captured record group');
let subject=groups.get(id(model.resolution.ontology.subject))!;
if(bound){
 const record=transport.records.find(r=>id(r.type)===id(model.resolution.ontology.subject))!;
 const doc=model.resolution.documents.find(d=>d.document.id===record.type.documentId)!.document;
 const key=encodeCoreKeyTuple(doc,{module:record.type.moduleId,element:record.type.elementId,key:record.keyId},input.subjectKey).values;
 subject=subject.filter(f=>JSON.stringify(f.key)===JSON.stringify(key));
 if(subject.length!==1)throw Error('Unique original mapped subject required');
}
const resources=groups.get(id(ref('Resource')))!;
if(resources.length!==1)throw Error('Selected fixture resource required');
const cut:SecurityFactCut={trusted:true,generation:'owned-identity-fixture',expectedGeneration:'owned-identity-fixture',policyId:model.policy.id,policyRevision:model.policy.revision,ontologyDocumentId:model.resolution.ontology.documentId,ontologyRevision:model.resolution.ontology.revision,subjects:subject,facts:[...groups].filter(([key])=>key!==id(model.resolution.ontology.subject)&&key!==id(ref('Resource'))).flatMap(([,rows])=>rows),coverage,context:[],maxFacts:100,maxSteps:10000};
const decision=evaluateSecurityAccess(model.policy,model.resolution,cut,{action:'read',output:[ref('salary')]},resources[0]!);
console.log(JSON.stringify({decision,identities:[...groups.values()].flat().map(f=>({type:f.type,key:f.key}))}));
