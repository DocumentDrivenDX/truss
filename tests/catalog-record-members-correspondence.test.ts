// SPDX-License-Identifier: MIT OR Apache-2.0
import {stageNewCatalogCohort} from '../packages/umf-bun/src/catalog-new-stage';
import {prepareDefaultCatalogHomes} from '../packages/umf-bun/src/catalog-default-homes';
import {test,expect} from 'bun:test';
import {mkdtemp,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {collectCatalogAssertionObservations} from '../packages/umf-bun/src/catalog-assertion-observations';
import {collectCatalogCoreAssertionIdentities} from '../packages/umf-bun/src/catalog-core-assertion-identities';
import {collectCatalogOriginalOccurrenceInventory,originalCatalogOccurrenceBytes} from '../packages/umf-bun/src/catalog-original-occurrence-inventory';
import {assessCatalogObservationCoverage} from '../packages/umf-bun/src/catalog-observation-coverage';
import {collectCatalogReportPreparation} from '../packages/umf-bun/src/catalog-report-preparation';
import {loadUmfDeclarationProducer,loadUmfFieldAssertionProducer,loadUmfRecordMembersProducer} from '../packages/umf-bun/src/index';
const preparation=await createCatalogInputPreparation(process.env.TRUSS_UMF_PRODUCER!,'/Users/erik/Projects/umf/package.json');
const declarations=await loadUmfDeclarationProducer(process.env.TRUSS_UMF_DECLARATION_PRODUCER!),fields=await loadUmfFieldAssertionProducer(process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER!),members=await loadUmfRecordMembersProducer(process.env.TRUSS_UMF_RECORD_MEMBERS_PRODUCER!);
const fixture=(await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input;
function prepare(properties:any={}){
 const model={umf:'0.7.0',id:'doc',vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[{id:'r',kind:'record',extensions:{},...properties},{id:'v',kind:'field',scalarType:'string',extensions:{}},{id:'w',kind:'field',scalarType:'string',extensions:{}}]}]};
 const input=structuredClone(fixture),bytes=Buffer.from(JSON.stringify(model));input.binding={state:'absent'};input.transforms=[];
 input.documents=[{documentId:'doc',documentRevision:'1',umfProfile:preparation.umfProfile,ingress:{kind:'native'},artifact:{identity:'doc',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')}}];
 return preparation.prepare(Buffer.from(JSON.stringify(input)));
}
function observations(p:ReturnType<typeof prepare>,owner=members){return collectCatalogAssertionObservations(p,declarations,fields,undefined,owner)}
test('original ordered qualified membership joins declaration and each exact byte occurrence',()=>{
 const refs=[{module:'m',element:'w',future:{values:['b','a']}},{module:'m',element:'v'}],p=prepare({members:refs}),collection=observations(p),inventory=collectCatalogOriginalOccurrenceInventory(p,collection);
 const meanings=inventory.core.membershipMeanings;
 expect(meanings.length).toBe(3);expect(meanings[0]!.originalMeaning).toEqual({state:'partial',members:refs,uninterpretedPaths:['/modules/0/elements/0/members/0/future']});
 expect(meanings.map(m=>m.assertion.ruleName)).toEqual(['core.members','core.members.member','core.members.member']);
 for(let i=0;i<meanings.length;i++){
  const m=meanings[i]!,pointer='/modules/0/elements/0/members'+(i?'/'+(i-1):'');
  expect(m.assertion.assertion.sourcePointer).toBe(pointer);expect(m.ownerProfile).toBe(collection.membersProfile!);expect(m.ownerProfile.version).toBe('5ddc656273e1965efa0187f3090d165d45225dcd');expect(m.ownerProfile.version).not.toBe(p.umfProfile.version);
  expect(m.assertion.source).toBe(p.original.input.documents[0]!.artifact);expect(m.assertion.enforcement).toBe('none');expect(m.interpretationQualified).toBe(false);
  const index=inventory.documents[0]!.occurrences.findIndex(r=>r.pointer===pointer),row=inventory.documents[0]!.occurrences[index]!;
  expect(row.assertions).toContain(m.assertion);expect(Buffer.from(originalCatalogOccurrenceBytes(p,inventory,0,index)).toString()).toBe(JSON.stringify(i?refs[i-1]:refs));expect(row.assertionMembershipComplete).toBe(false);
 }
 expect(Object.isFrozen(meanings[0]!.uninterpretedPaths)).toBe(true);
 expect(()=>{(meanings[0]!.uninterpretedPaths as string[]).push('/forged')}).toThrow();
 expect(()=>{(meanings[0]!.uninterpretedPaths as string[])[0]='/changed'}).toThrow();
 expect(meanings.every(m=>JSON.stringify(m.uninterpretedPaths)==='["/modules/0/elements/0/members/0/future"]')).toBe(true);
 expect((collection.observations.find(o=>o.operation==='members'&&(o.identity as any).element==='r')!.result as any).observation.meaning.uninterpretedPaths).toEqual(['/modules/0/elements/0/members/0/future']);
 expect(inventory.complete).toBe(false);expect(inventory.sourceCoverageComplete).toBe(true);
});
test('explicit empty membership stays an assertion while absence and nonrecord stay separate',()=>{
 for(const [properties,state,count] of [[{members:[]},'known',1],[{},'missing',0],[{kind:'future-role'},'inapplicable',0]] as const){
  const p=prepare(properties),c=observations(p),core=collectCatalogCoreAssertionIdentities(p,c),o=c.observations.find(o=>o.operation==='members'&&(o.identity as any).element==='r')!;
  expect((o.result as any).observation.meaning.state).toBe(state);expect(core.membershipMeanings.length).toBe(count);
  if(state==='known')expect(core.membershipMeanings[0]!.originalMeaning).toEqual({state:'known',members:[],uninterpretedPaths:[]});
  else expect((state==='missing'?core.absent:core.deferred).includes(o)).toBe(true);
 }
 const p=prepare({members:[]}),none=collectCatalogAssertionObservations(p,declarations,fields);expect(none.membersProfile).toBeNull();expect(none.observations.some(o=>o.operation==='members')).toBe(false);
 expect(()=>observations(p,{...members})).toThrow('loaded assertion owner');expect(()=>collectCatalogCoreAssertionIdentities(p,{...observations(p)})).toThrow('collection custody');expect(()=>collectCatalogCoreAssertionIdentities(prepare({members:[]}),observations(p))).toThrow('collection custody');
});
test('controlled loaded membership substitutions refuse before filtering, object key order remains valid',async()=>{
 const properties={members:[{module:'m',element:'w',future:{values:['b','a']}},{module:'m',element:'v'}]},cases:[any,string][]=[...[
  "r.meaning.members.reverse()","r.meaning.members.pop()","r.meaning.members[0].element='v'","delete r.meaning.members[0].future","r.meaning.members[0].future.values.reverse()","r.meaning.uninterpretedPaths=[]","r.meaning.uninterpretedPaths=['/foreign']","r.meaning.state='known'","r.meaning={state:'missing'}","r.meaning={state:'inapplicable'}","r.path='/modules/0/elements/1/members'","r.identity.element='v'","r.identity.module='foreign'","r.operation='inspect-core-keys'","r.version='future'","r.provenance='authenticated'","r.enforcement='database'","delete r.source.modules[0].elements[0].members[0].future","r.source.modules[0].elements[0].members.reverse()"
 ].map(m=>[properties,m] as [any,string]),[{},"r.meaning={state:'known',members:[],uninterpretedPaths:[]}"],[{members:[]},"r.meaning={state:'missing'}"],[{kind:'future-role'},"r.meaning={state:'known',members:[],uninterpretedPaths:[]}"],[properties,"r.meaning=Object.fromEntries(Object.entries(r.meaning).reverse())"]];
 for(const [properties,mutation] of cases){const p=prepare(properties),directory=await mkdtemp(join(tmpdir(),'truss-members-owner-control-'));
  try{const script=`import * as base from ${JSON.stringify(resolve(process.env.TRUSS_UMF_RECORD_MEMBERS_PRODUCER!,'producer.js'))};\nexport function inspectCoreRecordMembers(...args){const r=base.inspectCoreRecordMembers(...args);if(args[1].element==='r'){${mutation}}return r}\n`;
   await writeFile(join(directory,'producer.js'),script);await writeFile(join(directory,'producer-manifest.json'),JSON.stringify({revision:members.sourceRevision,producerMode:'record-members',bundleSha256:new Bun.CryptoHasher('sha256').update(script).digest('hex')}));
   const collection=observations(p,await loadUmfRecordMembersProducer(directory));
   if(mutation.includes('Object.fromEntries'))expect(collectCatalogCoreAssertionIdentities(p,collection).membershipMeanings.length).toBe(3);else expect(()=>collectCatalogCoreAssertionIdentities(p,collection)).toThrow('members');
  }finally{await rm(directory,{recursive:true,force:true})}
 }
});
test('original0.8 membership unavailable observations prevent configured call availability',()=>{
 const p=prepare({members:[]}),bytes=Buffer.from(JSON.stringify(p.documents[0]!.interpretation.target));
 const input={...p.original.input,documents:p.original.input.documents.map(d=>({...d,artifact:{identity:'doc',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')}}))};
 const modern=preparation.prepare(Buffer.from(JSON.stringify(input))),c=observations(modern),core=collectCatalogCoreAssertionIdentities(modern,c),coverage=assessCatalogObservationCoverage(modern,c);
 expect(c.observations.filter(o=>o.operation==='members').length).toBe(3);expect(coverage.unavailable.filter(o=>o.operation==='members').length).toBe(3);expect(coverage.availability).toBe('incomplete');expect(core.membershipMeanings).toEqual([]);
 for(const o of c.observations.filter(o=>o.operation==='members')){expect(o.result).toMatchObject({state:'unavailable',code:'CORE_RECORD_MEMBERS_VERSION'});expect(core.deferred.includes(o)).toBe(true)}
});
test('private report composition forwards actual membership owner with exact configured coverage',async()=>{
 const p=prepare({members:[{module:'m',element:'w'},{module:'m',element:'v'}]}),queries:string[]=[];
 const connection={unsafe:async(query:string)=>{queries.push(query);if(query.includes('runtime_collect_report_documents'))return [{doc_id:'doc',doc_revision:'1',content_sha256:p.original.input.documents[0]!.artifact.sha256,ord:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'}];if(query.includes('runtime_collect_new_catalog_counts'))return [{types_added:'0',properties_added:'0',keys_added:'0',relationships_added:'0',endpoints_added:'0',elements_retired:'0',provisional_count:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'}];return []}};
 // Synthetic native rows qualify host report composition only.
 const report=await collectCatalogReportPreparation(connection,p,'1',declarations,fields,undefined,members),baseline=assessCatalogObservationCoverage(p,collectCatalogAssertionObservations(p,declarations,fields));
 expect(report.ownerObservations.membersProfile?.version).toBe(members.sourceRevision);expect(Number(report.observationCoverage.observationsRequired)).toBe(Number(baseline.observationsRequired)+3);expect(report.observationCoverage.availability).toBe('available');expect(report.coreAssertionIdentities.membershipMeanings.length).toBe(3);expect(report.coreAssertionIdentities.complete).toBe(false);expect(queries.at(-1)).toContain('runtime_require_catalog_observation');
});

test('missing membership can be inspected but cannot become empty native staging or home inventory',async()=>{
 const p=prepare(),c=observations(p),core=collectCatalogCoreAssertionIdentities(p,c);expect(p.declarations[0]!.records[0]!.membership).toBe('missing');expect(core.membershipMeanings).toEqual([]);
 expect(()=>prepareDefaultCatalogHomes(p)).toThrow('Explicit original Record membership');let calls=0;
 await expect(stageNewCatalogCohort({unsafe:async()=>{calls++;return []}},p,[],{})).rejects.toThrow('Explicit original Record membership');expect(calls).toBe(0);
 const empty=prepare({members:[]});expect(empty.declarations[0]!.records[0]!.membership).toBe('declared');expect(prepareDefaultCatalogHomes(empty).homes).toEqual([]);
});
