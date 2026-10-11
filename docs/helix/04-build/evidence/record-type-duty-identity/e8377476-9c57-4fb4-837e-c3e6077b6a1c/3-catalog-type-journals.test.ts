import {createTypeJournalEvidenceBudget} from '../packages/umf-bun/src/catalog-type-journal-evidence-budget';
import {test,expect} from 'bun:test';
import {mkdtemp,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {collectCatalogTypeJournals,requireOriginalCatalogTypeJournals} from '../packages/umf-bun/src/catalog-type-journals';
import {collectCatalogTypeReceipts} from '../packages/umf-bun/src/catalog-type-receipts';
import {collectCatalogReportPreparation} from '../packages/umf-bun/src/catalog-report-preparation';
import {loadUmfDeclarationProducer,loadUmfFieldAssertionProducer,loadUmfRecordTypeJournalProducer,loadUmfRecordTypeReceiptProducer} from '../packages/umf-bun/src/index';
const preparation=await createCatalogInputPreparation(process.env.TRUSS_UMF_PRODUCER!,'/Users/erik/Projects/umf/package.json'),directory=process.env.TRUSS_UMF_RECORD_TYPE_JOURNAL_PRODUCER!;
const owner=await loadUmfRecordTypeJournalProducer(directory),author=await import(resolve(directory,'producer.js')),exactOwner=await loadUmfRecordTypeReceiptProducer(process.env.TRUSS_UMF_RECORD_TYPE_RECEIPT_PRODUCER!);
const declarations=await loadUmfDeclarationProducer(process.env.TRUSS_UMF_DECLARATION_PRODUCER!),fields=await loadUmfFieldAssertionProducer(process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER!);
const fixture=(await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input;
const hash=(b:Uint8Array|string)=>new Bun.CryptoHasher('sha256').update(b).digest('hex'),packet=(v:unknown)=>Buffer.from(JSON.stringify(v));
const artifact=(identity:string,b:Uint8Array)=>({identity,bytesBase64:Buffer.from(b).toString('base64'),sha256:hash(b)});
function setup(padding=0){
 const base={umf:'0.7.0',id:'journal-doc',...(padding?{'future/padding':'x'.repeat(padding)}:{}),vocabularies:{},modules:[{id:'m',namespace:'m',elements:[{id:'v',name:'v',kind:'field',nullability:'required',cardinality:'one',extensions:{},'future/value':{values:['b','a'],decimal:0.1},references:[{role:'future-role',module:'m',element:'R','future/qualifier':{values:['b','a']}}]},{id:'w',name:'w',kind:'field',nullability:'required',cardinality:'one',extensions:{}},{id:'R',kind:'record',members:[],extensions:{}},{id:'Owner',kind:'record',members:[{module:'m',element:'v'},{module:'m',element:'w'}],extensions:{}}]},{id:'other',namespace:'other',elements:[{id:'R',kind:'record',members:[],extensions:{}}]}]};
 const first=author.declareCoreRecordType(author.declareCoreElementKind(base,{module:'m',element:'v'},'field'),author.declareCoreElementKind(base,{module:'other',element:'R'},'record'));
 const second=author.declareCoreRecordType(author.declareCoreElementKind(first.target,{module:'m',element:'w'},'field'),author.declareCoreElementKind(first.target,{module:'m',element:'R'},'record'));
 const sourceBytes=Buffer.from(' \n'+JSON.stringify(second.target)+'\n'),input=structuredClone(fixture);input.binding={state:'absent'};input.transforms=[];input.documents=[{documentId:'journal-doc',documentRevision:'r1',umfProfile:preparation.umfProfile,ingress:{kind:'native'},artifact:artifact('original-journal-doc',sourceBytes)}];
 const prepared=preparation.prepare(packet(input)),journal={version:'0.1.0',base,events:[first,second]},bytes=Buffer.from(' \n'+JSON.stringify(journal)+'\n'),requests={version:'0.1.0',journals:[{documentId:'journal-doc',documentRevision:'r1',artifact:artifact('original-journal',bytes)}]};
 return {base,first,second,prepared,input,journal,requests,bytes,wire:Buffer.from(' \n'+JSON.stringify(requests)+'\n')};
}
function changedArtifact(s:ReturnType<typeof setup>,journal:unknown){const requests=structuredClone(s.requests);requests.journals[0]!.artifact=artifact('changed-journal',packet(journal));return packet(requests)}
test('original whole journal reconciles multiple typed Fields and exact source occurrences',()=>{
 const s=setup(),c=collectCatalogTypeJournals(s.prepared,owner,s.wire);
 expect(c.entries.length).toBe(2);expect(c.journals.length).toBe(1);expect(c.ownerProfile.version).toBe('e71613d9c76bf7a4bf5476bf72ab4fd99059ff17');expect(c.ownerProfile.sha256).toBe(owner.bundleSha256);expect(c.requestArtifact).toEqual({...artifact('truss.original-type-journal-requests',s.wire),identity:'truss.original-type-journal-requests' as const});
 expect(c.entries.map(e=>e.eventIndex)).toEqual([0,1]);expect(c.entries.map(e=>e.eventPointer)).toEqual(['/events/0','/events/1']);expect(c.entries.map(e=>e.sourcePointer)).toEqual(['/modules/0/elements/0/references/1','/modules/0/elements/1/references/0']);
 for(const [i,e] of c.entries.entries()){expect(e.source).toBe(s.prepared.original.input.documents[0]!.artifact);expect(e.ownerProfile).toBe(c.ownerProfile);expect(e.journalArtifact).toEqual(s.requests.journals[0]!.artifact);expect(e.journalArtifact.bytesBase64).toBe(s.bytes.toString('base64'));expect(Buffer.from(e.originalReferenceBytesBase64,'base64').toString()).toBe(JSON.stringify(s.journal.events[i]!.reference));expect(e.originalMeaning).toMatchObject({eventIndex:i,receipt:s.journal.events[i],link:{typeAssertion:'unverified',target:{identity:{module:i===0?'other':'m',element:'R'},kind:'record'}}});expect(e.issuerAuthority).toBe('unverified');expect(e.enforcement).toBe('none');expect(e.interpretationQualified).toBe(false)}
 const meaning=c.journals[0]!.ownerMeaning as any;expect(meaning).toMatchObject({base:s.base,events:s.journal.events,source:s.second.target,receiptConsistency:'verified',issuerAuthority:'unverified',enforcement:'none'});expect(c.complete).toBe(false);
 const evidence=JSON.parse(Buffer.from(c.journals[0]!.ownerEvidence.bytesBase64,'base64').toString());expect(evidence.result).toEqual(meaning);expect(evidence.originalSourceSha256).toBe(c.entries[0]!.source.sha256);expect(c.journals[0]!.ownerEvidence.sha256).toBe(hash(Buffer.from(c.journals[0]!.ownerEvidence.bytesBase64,'base64')));
 const oldWire=packet({version:'0.1.0',receipts:[{documentId:'journal-doc',documentRevision:'r1',field:{module:'m',element:'v'},artifact:artifact('old-receipt',packet(s.first))}]});expect(()=>collectCatalogTypeReceipts(s.prepared,exactOwner,oldWire)).toThrow('current/Field');
 s.wire.fill(0);s.bytes.fill(0);s.journal.events.reverse();expect(c.journals[0]!.journalArtifact.identity).toBe('original-journal');expect(()=>meaning.events.reverse()).toThrow();expect(()=>((c.entries[0]!.originalMeaning as any).link.reference.module='changed')).toThrow();
});
test('whole journal packet refuses gaps crossed contexts mutations duplicates and unsupported profiles',()=>{
 const s=setup();expect(()=>collectCatalogTypeJournals(s.prepared,{...owner},s.wire)).toThrow('loaded assertion owner');
 const empty=collectCatalogTypeJournals(s.prepared,owner,packet({version:'0.1.0',journals:[]}));expect(empty.entries).toEqual([]);expect(empty.complete).toBe(false);
 for(const mutate of [(r:any)=>{r.extra=true},(r:any)=>{r.version='future'},(r:any)=>{r.journals[0].documentId='other'},(r:any)=>{r.journals[0].documentRevision='r2'},(r:any)=>{r.journals[0].artifact.sha256='0'.repeat(64)},(r:any)=>{r.journals[0].artifact.bytesBase64+='='},(r:any)=>{r.journals.push(structuredClone(r.journals[0]))},(r:any)=>{r.journals=Array(65).fill(r.journals[0])}]){const requests=structuredClone(s.requests);mutate(requests);expect(()=>collectCatalogTypeJournals(s.prepared,owner,packet(requests))).toThrow()}
 for(const mutate of [(j:any)=>{j.base.id='changed'},(j:any)=>{j.events.reverse()},(j:any)=>{j.events.pop()},(j:any)=>{j.events.shift()},(j:any)=>{j.events.push(j.events[1])},(j:any)=>{j.events[0].source.id='changed'},(j:any)=>{j.events[0].fieldAuthor.source.id='changed'},(j:any)=>{j.events[0].reference.module='m'},(j:any)=>{j.events[0].provenance.idealPath='/modules/0/elements/0/references/0'},(j:any)=>{j.events[0].version='5.0.0'},(j:any)=>{j.version='future'},(j:any)=>{j.extra=true},(j:any)=>{j.events=[]},(j:any)=>{j.events=Array(33).fill(j.events[0])},(j:any)=>{j.base.modules[0].elements[0]['future/value'].values.reverse()}]){const journal=structuredClone(s.journal);mutate(journal);expect(()=>collectCatalogTypeJournals(s.prepared,owner,changedArtifact(s,journal))).toThrow()}
 const foreign=structuredClone(s.second.target);foreign.id='foreign-context';const event=author.declareCoreElementKind(foreign,{module:'m',element:'w'},'field');expect(()=>collectCatalogTypeJournals(s.prepared,owner,changedArtifact(s,{...s.journal,events:[...s.journal.events,event]}))).toThrow('Full event source');
 const input=structuredClone(s.input),source=structuredClone(s.second.target);source.modules[0].elements[0]['future/value'].values.reverse();input.documents[0]!.artifact=artifact('changed-current',packet(source));const changed=preparation.prepare(packet(input));expect(()=>collectCatalogTypeJournals(changed,owner,s.wire)).toThrow('Full final target');
 const upgraded=structuredClone(s.input);upgraded.documents[0]!.artifact=artifact('original08',packet(s.prepared.documents[0]!.interpretation.target));expect(()=>collectCatalogTypeJournals(preparation.prepare(packet(upgraded)),owner,s.wire)).toThrow('document/revision/profile');
 expect(()=>collectCatalogTypeJournals(s.prepared,owner,new Uint8Array(new SharedArrayBuffer(s.wire.length)))).toThrow('carrier');expect(()=>collectCatalogTypeJournals(s.prepared,owner,new Uint8Array(1048577))).toThrow('resource');
});
test('journal original bytes reject duplicate members and numeric meaning loss',()=>{
 const s=setup();for(const raw of [s.bytes.toString().replace('"version":','"version":"forged","version":'),s.bytes.toString().replace('"decimal":0.1','"decimal":0.10000000000000001')]){const requests=structuredClone(s.requests);requests.journals[0]!.artifact=artifact('invalid-byte-journal',Buffer.from(raw));expect(()=>collectCatalogTypeJournals(s.prepared,owner,packet(requests))).toThrow()}
});
test('kind-only history retains imported bare type links without inventing duties',()=>{
 const s=setup(),current=s.second.target,event=author.declareCoreElementKind(current,{module:'m',element:'w'},'field'),wire=changedArtifact(s,{version:'0.1.0',base:current,events:[event]});const c=collectCatalogTypeJournals(s.prepared,owner,wire);expect(c.entries).toEqual([]);expect(c.journals.length).toBe(1);expect((c.journals[0]!.ownerMeaning as any).source).toEqual(current);expect(c.complete).toBe(false);
});
test('mixed kind events retain original type event indices and independent scanner bounds remain active',()=>{
 const s=setup(),start=author.declareCoreElementKind(s.base,{module:'m',element:'v'},'field'),between=author.declareCoreElementKind(s.first.target,{module:'m',element:'w'},'field');
 const c=collectCatalogTypeJournals(s.prepared,owner,changedArtifact(s,{...s.journal,events:[start,s.first,between,s.second]}));expect(c.entries.map(e=>e.eventIndex)).toEqual([1,3]);expect(c.entries.map(e=>e.eventPointer)).toEqual(['/events/1','/events/3']);expect(c.entries.map(e=>e.sourcePointer)).toEqual(['/modules/0/elements/0/references/1','/modules/0/elements/1/references/0']);
 const large=setup(57500);expect(large.wire.length).toBeLessThanOrEqual(1048576);expect(large.bytes.length).toBeLessThanOrEqual(1048576);expect(owner.inspectRecordTypeJournal(large.base,large.second.target,large.journal.events).types.length).toBe(2);expect(()=>collectCatalogTypeJournals(large.prepared,owner,large.wire)).toThrow('resource');
});
test('retained-evidence ledger enforces its independent exact byte bound',()=>{
 const s=setup(),c=collectCatalogTypeJournals(s.prepared,owner,s.wire),budget=createTypeJournalEvidenceBudget();
 budget.charge(s.wire.length);budget.charge(s.bytes.length);budget.charge(Buffer.from(c.journals[0]!.ownerEvidence.bytesBase64,'base64').length);
 expect(budget.total()).toBe(s.wire.length+s.bytes.length+Buffer.from(c.journals[0]!.ownerEvidence.bytesBase64,'base64').length);
 budget.charge(4194304-budget.total());expect(budget.total()).toBe(4194304);expect(()=>budget.charge(1)).toThrow('evidence capacity');expect(budget.total()).toBe(4194304);
 for(const invalid of [-1,0.5,Infinity,NaN,Number.MAX_SAFE_INTEGER])expect(()=>budget.charge(invalid)).toThrow('evidence capacity');expect(budget.total()).toBe(4194304);
});
test('loaded journal output substitutions and argument mutation cannot change original meaning',async()=>{
 const mutations=["r.base.id='changed'","r.source.id='changed'","r.events.reverse()","r.types.reverse()","r.types.pop()","r.types.push(structuredClone(r.types[0]))","r.types[0].eventIndex=1","r.types[0].identity.module='other'","r.types[0].path='/modules/0/elements/0/references/0'","r.types[0].recordPath='/modules/0/elements/2'","r.types[0].link.index=0","r.types[0].link.reference.role='future-role'","r.types[0].link.target.identity.module='m'","r.types[0].link.target.kind='field'","r.types[0].receipt.source.id='changed'","r.receiptConsistency='unverified'","r.issuerAuthority='authenticated'","r.enforcement='rls'","r.types[0].link.typeAssertion='verified'","r.extraAuthority=true","r.base.modules[0].elements[0]['future/value'].values.reverse()","Object.defineProperty(r,'source',{enumerable:true,get(){throw Error('getter invoked')}})","r=Object.fromEntries(Object.entries(r).reverse())"];
 for(const mutation of mutations){const s=setup(),temp=await mkdtemp(join(tmpdir(),'truss-journal-owner-control-'));try{const script=`import * as base from ${JSON.stringify(resolve(directory,'producer.js'))};\nexport function inspectCoreRecordTypeJournal(...args){let r=base.inspectCoreRecordTypeJournal(...args);${mutation};return r}\n`;await writeFile(join(temp,'producer.js'),script);await writeFile(join(temp,'producer-manifest.json'),JSON.stringify({revision:owner.sourceRevision,producerMode:'record-type-journals',bundleSha256:hash(script)}));const loaded=await loadUmfRecordTypeJournalProducer(temp);if(mutation.includes('Object.fromEntries'))expect(collectCatalogTypeJournals(s.prepared,loaded,s.wire).entries.length).toBe(2);else expect(()=>collectCatalogTypeJournals(s.prepared,loaded,s.wire)).toThrow(mutation.includes('defineProperty')?'Inert receipt JSON':'full owner result')}finally{await rm(temp,{recursive:true,force:true})}}
 const s=setup(),temp=await mkdtemp(join(tmpdir(),'truss-journal-argument-control-'));try{const script=`import * as base from ${JSON.stringify(resolve(directory,'producer.js'))}; export function inspectCoreRecordTypeJournal(...args){args[2].reverse();return base.inspectCoreRecordTypeJournal(...args)}`;await writeFile(join(temp,'producer.js'),script);await writeFile(join(temp,'producer-manifest.json'),JSON.stringify({revision:owner.sourceRevision,producerMode:'record-type-journals',bundleSha256:hash(script)}));const loaded=await loadUmfRecordTypeJournalProducer(temp);expect(()=>collectCatalogTypeJournals(s.prepared,loaded,s.wire)).toThrow();expect(s.journal.events[0]).toEqual(s.first)}finally{await rm(temp,{recursive:true,force:true})}
});
test('journal issuance binds exact original preparation before private report SQL',async()=>{
 const s=setup(),c=collectCatalogTypeJournals(s.prepared,owner,s.wire),other=preparation.prepare(packet(s.input));expect(()=>requireOriginalCatalogTypeJournals(s.prepared,{...c})).toThrow('collection custody');expect(()=>requireOriginalCatalogTypeJournals(other,c)).toThrow('collection custody');
 let calls=0;const connection={unsafe:async(query:string)=>{calls++;if(query.includes('runtime_collect_report_documents'))return [{doc_id:'journal-doc',doc_revision:'r1',content_sha256:s.prepared.original.input.documents[0]!.artifact.sha256,ord:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'}];if(query.includes('runtime_collect_new_catalog_counts'))return [{types_added:'0',properties_added:'0',keys_added:'0',relationships_added:'0',endpoints_added:'0',elements_retired:'0',provisional_count:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'}];return []}};
 for(const invalid of [{...c},false,0,'',null])await expect(collectCatalogReportPreparation(connection,s.prepared,'1',declarations,fields,undefined,undefined,undefined,undefined,invalid as any)).rejects.toThrow('collection custody');await expect(collectCatalogReportPreparation(connection,other,'1',declarations,fields,undefined,undefined,undefined,undefined,c)).rejects.toThrow('collection custody');expect(calls).toBe(0);
 const report=await collectCatalogReportPreparation(connection,s.prepared,'1',declarations,fields,undefined,undefined,undefined,undefined,c);expect(report.typeJournals).toBe(c);expect(report.typeReceipts).toBeNull();const noRecordType=(entries:readonly {ruleName:string}[])=>entries.every(e=>e.ruleName!=='core.recordType');expect(noRecordType(report.coreAssertionIdentities.entries)).toBe(true);expect(noRecordType([...report.coreAssertionIdentities.entries,{ruleName:'core.recordType'}])).toBe(false);expect(report.coreAssertionIdentities.complete).toBe(false);expect(calls).toBeGreaterThan(0);
});

import {collectCatalogAssertionObservations} from '../packages/umf-bun/src/catalog-assertion-observations';
import {collectCatalogRecordTypeRuleFamilies,requireOriginalCatalogRecordTypeRuleFamilies} from '../packages/umf-bun/src/catalog-record-type-rule-families';
import {loadUmfReferenceLinksProducer} from '../packages/umf-bun/src/index';
const linksOwner=await loadUmfReferenceLinksProducer(process.env.TRUSS_UMF_REFERENCE_LINKS_PRODUCER!);
function observations(s:ReturnType<typeof setup>,withLinks=true){return collectCatalogAssertionObservations(s.prepared,declarations,fields,undefined,undefined,withLinks?linksOwner:undefined)}
test('record-type duties conserve exact qualified occurrences without value or enforcement promotion',()=>{
 const s=setup(),start=author.declareCoreElementKind(s.base,{module:'m',element:'v'},'field'),between=author.declareCoreElementKind(s.first.target,{module:'m',element:'w'},'field');
 const journal=collectCatalogTypeJournals(s.prepared,owner,changedArtifact(s,{...s.journal,events:[start,s.first,between,s.second]}));
 const candidate=collectCatalogRecordTypeRuleFamilies(s.prepared,observations(s),undefined,journal);
 expect(candidate.rules.length).toBe(2);expect(candidate.rules.map(r=>r.parameters.record)).toEqual([{module:'other',element:'R'},{module:'m',element:'R'}]);
 expect(candidate.rules.map(r=>(r.carrier as any).eventIndex)).toEqual([1,3]);expect(candidate.linksWithoutReceipt).toEqual([]);
 for(const [i,r] of candidate.rules.entries()){
  expect(r.identity.family).toBe('record_type_declaration');expect(r.identity.occurrence.owner).toEqual(journal.entries[i]!.identity);expect(r.identity.occurrence.definitionPin).toBe(s.prepared.original.input.documents[0]!.artifact.sha256);
  expect(r.identity.occurrence.sourcePointer).toBe(journal.entries[i]!.sourcePointer);expect(r.originalReferenceBytesBase64).toBe(journal.entries[i]!.originalReferenceBytesBase64);expect(r.ownerEvidence).toBe(journal.entries[i]!.ownerEvidence);
  expect(r).toMatchObject({protocol:'transition_journal',receiptConsistency:'verified',valueSemantics:'unavailable',issuerAuthority:'unverified',enforcement:'none',interpretationQualified:false});
 }
 expect(candidate.complete).toBe(false);expect(candidate.genericLinkOwnerAvailability).toBe('configured');expect(()=>(candidate.rules as any).reverse()).toThrow();
 requireOriginalCatalogRecordTypeRuleFamilies(s.prepared,candidate);expect(()=>requireOriginalCatalogRecordTypeRuleFamilies(s.prepared,{...candidate})).toThrow('custody');expect(()=>requireOriginalCatalogRecordTypeRuleFamilies(preparation.prepare(packet(s.input)),candidate)).toThrow('custody');
 const unavailable=collectCatalogRecordTypeRuleFamilies(s.prepared,observations(s,false),undefined,journal);expect(unavailable.rules.length).toBe(2);expect(unavailable.genericLinkOwnerAvailability).toBe('unavailable');expect(unavailable.complete).toBe(false);
});
test('receipt protocol is evidence: equal declaration identity and duplicate occurrence refusal',async()=>{
 const s=setup(),receipt=collectCatalogTypeReceipts(s.prepared,exactOwner,packet({version:'0.1.0',receipts:[{documentId:'journal-doc',documentRevision:'r1',field:{module:'m',element:'w'},artifact:artifact('last-receipt',packet(s.second))}]}));
 const journal=collectCatalogTypeJournals(s.prepared,owner,s.wire),observed=observations(s);
 const exact=collectCatalogRecordTypeRuleFamilies(s.prepared,observed,receipt),history=collectCatalogRecordTypeRuleFamilies(s.prepared,observed,undefined,journal);
 expect(exact.rules[0]!.identity).toEqual(history.rules[1]!.identity);expect(exact.rules[0]!.protocol).toBe('exact_current_receipt');expect(history.rules[1]!.protocol).toBe('transition_journal');
 expect(()=>collectCatalogRecordTypeRuleFamilies(s.prepared,observed,receipt,journal)).toThrow('Duplicate original');
 let sqlCalls=0;const noSql={unsafe:async()=>{sqlCalls++;throw Error('SQL must not run')}};await expect(collectCatalogReportPreparation(noSql,s.prepared,'1',declarations,fields,undefined,undefined,linksOwner,receipt,journal)).rejects.toThrow('Duplicate original');expect(sqlCalls).toBe(0);
 for(const invalid of [null,false,0,'',{...receipt}])expect(()=>collectCatalogRecordTypeRuleFamilies(s.prepared,observed,invalid as any)).toThrow('custody');
 for(const invalid of [null,false,0,'',{...journal}])expect(()=>collectCatalogRecordTypeRuleFamilies(s.prepared,observed,undefined,invalid as any)).toThrow('custody');
 const bare=collectCatalogRecordTypeRuleFamilies(s.prepared,observed);expect(bare.rules).toEqual([]);expect(bare.linksWithoutReceipt.length).toBe(2);expect(bare.linksWithoutReceipt.map(e=>(e.originalMeaning as any).typeAssertion)).toEqual(['unverified','unverified']);
 const event=author.declareCoreElementKind(s.second.target,{module:'m',element:'w'},'field');const imported=collectCatalogTypeJournals(s.prepared,owner,changedArtifact(s,{version:'0.1.0',base:s.second.target,events:[event]}));
 const noAuthorship=collectCatalogRecordTypeRuleFamilies(s.prepared,observed,undefined,imported);expect(noAuthorship.rules).toEqual([]);expect(noAuthorship.linksWithoutReceipt.length).toBe(2);
});

 test('configured generic owner must observe every receipt-backed declaration before SQL',async()=>{
 const s=setup(),journal=collectCatalogTypeJournals(s.prepared,owner,s.wire),temp=await mkdtemp(join(tmpdir(),'truss-record-type-links-refusal-'));
 try{
  const script=`import * as base from ${JSON.stringify(resolve(process.env.TRUSS_UMF_REFERENCE_LINKS_PRODUCER!,'producer.js'))}; export function inspectCoreReferenceLinks(model,identity){if(identity.element==='v')throw Error('unavailable typed Field');return base.inspectCoreReferenceLinks(model,identity)}`;
  await writeFile(join(temp,'producer.js'),script);await writeFile(join(temp,'producer-manifest.json'),JSON.stringify({revision:linksOwner.sourceRevision,producerMode:'reference-links',bundleSha256:hash(script)}));
  const unavailable=await loadUmfReferenceLinksProducer(temp),observed=collectCatalogAssertionObservations(s.prepared,declarations,fields,undefined,undefined,unavailable);
  expect(()=>collectCatalogRecordTypeRuleFamilies(s.prepared,observed,undefined,journal)).toThrow('correspondence required');
  let calls=0;await expect(collectCatalogReportPreparation({unsafe:async()=>{calls++;throw Error('SQL must not run')}},s.prepared,'1',declarations,fields,undefined,undefined,unavailable,undefined,journal)).rejects.toThrow('correspondence required');expect(calls).toBe(0);
 }finally{await rm(temp,{recursive:true,force:true})}
});
