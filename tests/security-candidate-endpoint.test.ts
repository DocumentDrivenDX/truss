import {test,expect} from 'bun:test';
import {bindCandidateSecurityEndpoint,type CandidateEndpointColumns} from '../packages/postgresql/src/security-candidate-endpoint';
import evidence from './fixtures/security-original-graph-ir-formal.json';
const ref=(elementId:string)=>({documentId:'domain',moduleId:'m',elementId});
const artifact=evidence.artifacts.find(a=>a.id==='mixed')!;
const terms:unknown[]=[];
function walk(v:unknown){if(v&&typeof v==='object'){if(Object.hasOwn(v,'endpoint'))terms.push(v);else for(const child of Object.values(v))walk(child);}}
walk(artifact.rules[0]!.condition);
for(const term of terms){
 const endpoint=(term as any).endpoint;
 const mapping:CandidateEndpointColumns={association:endpoint.association,role:endpoint.role,target:endpoint.target,keyId:endpoint.keyId,targetKeyFields:[ref(endpoint.target.elementId.toLowerCase()+'Id')],carrier:endpoint.carrier,columns:['key_column']};
 test('actual original mixed endpoint '+JSON.stringify([endpoint.association,endpoint.role]),()=>{
  const bound=bindCandidateSecurityEndpoint(term,mapping);expect(bound.carrier).toEqual(endpoint.carrier);expect(bound.association).toEqual(endpoint.association);expect(Object.isFrozen(bound.columns)).toBe(true);
  const changed={...mapping,columns:['other']};expect(bound.columns).toEqual(['key_column']);expect(bound.binding).toEqual(endpoint.binding);expect(bindCandidateSecurityEndpoint(term,changed).columns).toEqual(['other']);
  for(const patch of [{keyId:'other'},{target:ref('Other')},{role:'other'},{columns:['a','b']},{association:{documentId:'domain',moduleId:'m',relationshipId:'Ownership'}}])expect(()=>bindCandidateSecurityEndpoint(term,{...mapping,...patch} as CandidateEndpointColumns)).toThrow();
  if('incidence' in mapping.carrier){const side=mapping.carrier.incidence.side==='source'?'target':'source';expect(()=>bindCandidateSecurityEndpoint(term,{...mapping,carrier:{incidence:{side}}})).toThrow();}
  else expect(()=>bindCandidateSecurityEndpoint(term,{...mapping,carrier:{members:{fields:[ref('other')]}}})).toThrow();
 });
}
test('ordered compound member and column carriers stay ordered',()=>{
 const term={endpoint:{binding:{variable:0},association:ref('Ownership'),role:'resource',target:ref('Resource'),keyId:'compound',carrier:{members:{fields:[ref('ownerResource'),ref('ownerSalary')]}}}};
 const mapping:CandidateEndpointColumns={association:ref('Ownership'),role:'resource',target:ref('Resource'),keyId:'compound',targetKeyFields:[ref('resourceId'),ref('salary')],carrier:term.endpoint.carrier,columns:['resource_id','salary']};
 expect(bindCandidateSecurityEndpoint(term,mapping).columns).toEqual(['resource_id','salary']);
 const reversed={...mapping,carrier:{members:{fields:[ref('ownerSalary'),ref('ownerResource')]}}};expect(()=>bindCandidateSecurityEndpoint(term,reversed)).toThrow();
 expect(()=>bindCandidateSecurityEndpoint(term,{...mapping,columns:['same','same']})).toThrow();
 expect(()=>bindCandidateSecurityEndpoint(term,{...mapping,targetKeyFields:[ref('salary'),ref('salary')]})).toThrow();
});
test('reflection refuses accessors without invoking them',()=>{
 let called=false;const term={get endpoint(){called=true;return {};}};expect(()=>bindCandidateSecurityEndpoint(term,{} as CandidateEndpointColumns)).toThrow();expect(called).toBe(false);
});

const graphTerm=terms.find(t=>'relationshipId' in (t as any).endpoint.association) as any;
function graphFixture(){const term=structuredClone(graphTerm);return {term,mapping:{association:structuredClone(term.endpoint.association),role:term.endpoint.role,target:structuredClone(term.endpoint.target),keyId:term.endpoint.keyId,targetKeyFields:[ref('staffId')],carrier:structuredClone(term.endpoint.carrier),columns:['key_column']} as CandidateEndpointColumns};}
test('Unicode scalar limits preserve supplementary characters',()=>{
 for(const channel of ['role','keyId','target'] as const){for(const length of [4096,4097]){
  const {term,mapping}=graphFixture(),value='😀'.repeat(length);
  if(channel==='target'){term.endpoint.target.elementId=value;mapping.target.elementId=value;}else{term.endpoint[channel]=value;mapping[channel]=value;}
  if(length===4096)expect(()=>bindCandidateSecurityEndpoint(term,mapping)).not.toThrow();else expect(()=>bindCandidateSecurityEndpoint(term,mapping)).toThrow();
 }
 const {term,mapping}=graphFixture();term.endpoint.role='\ud800';mapping.role='\ud800';expect(()=>bindCandidateSecurityEndpoint(term,mapping)).toThrow();}
});
test('deep copied snapshots survive mutations of original inputs',()=>{
 const {term,mapping}=graphFixture(),bound=bindCandidateSecurityEndpoint(term,mapping),before=JSON.stringify(bound);
 term.endpoint.binding.variable=99;term.endpoint.target.elementId='mutated';
 mapping.target.elementId='mutated';(mapping.targetKeyFields as any[])[0].elementId='mutated';(mapping.columns as string[])[0]='mutated';
 if('incidence' in mapping.carrier)mapping.carrier.incidence.side='target';
 expect(JSON.stringify(bound)).toBe(before);expect(Object.isFrozen(bound.target)).toBe(true);expect(Object.isFrozen(bound.targetKeyFields[0])).toBe(true);expect(Object.isFrozen(bound.carrier)).toBe(true);
});
test('dense array and native UTF8 column boundaries',()=>{
 for(const length of [256,257]){const {term,mapping}=graphFixture();mapping.targetKeyFields=Array.from({length},(_,i)=>ref('k'+i));mapping.columns=Array.from({length},(_,i)=>'c'+i);if(length===256)expect(()=>bindCandidateSecurityEndpoint(term,mapping)).not.toThrow();else expect(()=>bindCandidateSecurityEndpoint(term,mapping)).toThrow();}
 for(const [column,valid] of [['a'.repeat(63),true],['a'.repeat(64),false],['😀'.repeat(15)+'abc',true],['😀'.repeat(16),false]] as const){const {term,mapping}=graphFixture();mapping.columns=[column];if(valid)expect(()=>bindCandidateSecurityEndpoint(term,mapping)).not.toThrow();else expect(()=>bindCandidateSecurityEndpoint(term,mapping)).toThrow();}
});
test('nested data and array accessors refuse without invocation',()=>{
 for(const where of ['reference','carrier','array'] as const){let invoked=0;const {term,mapping}=graphFixture();
  if(where==='reference')Object.defineProperty(mapping.target,'elementId',{enumerable:true,get(){invoked++;return 'Staff';}});
  if(where==='carrier')Object.defineProperty(mapping.carrier,'incidence',{enumerable:true,get(){invoked++;return {side:'source'};}});
  if(where==='array')Object.defineProperty(mapping.columns,0,{enumerable:true,get(){invoked++;return 'column';}});
  expect(()=>bindCandidateSecurityEndpoint(term,mapping)).toThrow();expect(invoked).toBe(0);
 }
});
