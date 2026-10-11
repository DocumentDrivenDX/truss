import {test,expect} from 'bun:test';
import {mkdtemp,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {collectCatalogAssertionObservations} from '../packages/umf-bun/src/catalog-assertion-observations';
import {collectCatalogCoreAssertionIdentities} from '../packages/umf-bun/src/catalog-core-assertion-identities';
import {loadUmfProducer,loadUmfDeclarationProducer,loadUmfFieldAssertionProducer,loadUmfScalarTypeProducer} from '../packages/umf-bun/src/index';
const preparation=await createCatalogInputPreparation(process.env.TRUSS_UMF_PRODUCER!,'/Users/erik/Projects/umf/package.json');
const record=await loadUmfProducer(process.env.TRUSS_UMF_PRODUCER!),ownerDeclarations=await loadUmfDeclarationProducer(process.env.TRUSS_UMF_DECLARATION_PRODUCER!),fields=await loadUmfFieldAssertionProducer(process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER!);
const fixture=(await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input;
function prepare(element:any){
 const model={umf:'0.7.0',id:'doc',vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[{id:'v',extensions:{},...(element.kind==='record'?{members:[]}:{}),...element},{id:'leaf',kind:'field',scalarType:'string',nullability:'required',cardinality:'one',extensions:{}},{id:'leaf2',kind:'field',scalarType:'string',nullability:'required',cardinality:'one',extensions:{}},{id:'R',kind:'record',members:[{module:'m',element:element.kind==='field'?'v':'leaf'}],extensions:{}}]}]};
 const input=structuredClone(fixture),bytes=Buffer.from(JSON.stringify(model));input.binding={state:'absent'};input.transforms=[];
 input.documents=[{documentId:'doc',documentRevision:'1',umfProfile:preparation.umfProfile,ingress:{kind:'native'},artifact:{identity:'doc',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')}}];
 return preparation.prepare(new TextEncoder().encode(JSON.stringify(input)));
}
const scalars=await loadUmfScalarTypeProducer(process.env.TRUSS_UMF_SCALAR_TYPE_PRODUCER!);
import {collectCatalogReportPreparation} from '../packages/umf-bun/src/catalog-report-preparation';
import {assessCatalogObservationCoverage} from '../packages/umf-bun/src/catalog-observation-coverage';
import {collectCatalogOriginalOccurrenceInventory,originalCatalogOccurrenceBytes} from '../packages/umf-bun/src/catalog-original-occurrence-inventory';
function observations(p:ReturnType<typeof prepare>,owner=scalars){return collectCatalogAssertionObservations(p,ownerDeclarations,fields,owner)}
test('nine original scalar families join exact byte occurrences with independent semantic owner pins',()=>{
 for(const scalarType of ['boolean','integer','decimal','float','string','binary','date','time','timestamp']){
  const p=prepare({kind:'field',scalarType,nullability:'required',cardinality:'one',future:{tuple:['a','b']}}),collection=observations(p),inventory=collectCatalogOriginalOccurrenceInventory(p,collection);
  const retained=inventory.core.fieldMeanings.find(m=>m.assertion.ruleName==='core.scalarType'&&m.assertion.assertion.sourcePointer==='/modules/0/elements/0/scalarType')!;
  expect(retained.originalMeaning).toEqual({state:'known',scalarType});expect(retained.ownerProfile).toBe(collection.scalarProfile!);
  expect(retained.ownerProfile.version).toBe('94d0a99e4d1e9eb39278f38d6cd6bcba51e46db8');expect(retained.ownerProfile.version).not.toBe(p.umfProfile.version);
  expect(retained.assertion.source).toBe(p.original.input.documents[0]!.artifact);expect(retained.assertion.enforcement).toBe('none');expect(retained.interpretationQualified).toBe(false);
  const position=inventory.documents[0]!.occurrences.findIndex(r=>r.pointer==='/modules/0/elements/0/scalarType'),row=inventory.documents[0]!.occurrences[position]!;
  expect(row.assertions).toContain(retained.assertion);expect(new TextDecoder().decode(originalCatalogOccurrenceBytes(p,inventory,0,position))).toBe(JSON.stringify(scalarType));
  expect(row.assertionMembershipComplete).toBe(false);expect(inventory.sourceCoverageComplete).toBe(true);expect(inventory.complete).toBe(false);
  const original=collection.observations.find(o=>o.operation==='scalarType'&&(o.identity as any).element==='v')!;
  expect((original.result as any).observation.source.modules[0].elements[0].future).toEqual({tuple:['a','b']});
 }
});
test('unknown absent non-Field and container scalar meanings stay distinct without invented entries',()=>{
 for(const [element,meaning] of [[{kind:'field',scalarType:'future-scalar'},{state:'unknown',value:'future-scalar'}],[{kind:'field'},{state:'missing'}],[{scalarType:'string'},{state:'inapplicable',authoredScalarType:'string'}],[{kind:'future-role',scalarType:'future-scalar'},{state:'inapplicable',authoredScalarType:'future-scalar'}],[{kind:'record'},{state:'inapplicable'}],[{kind:'field',cardinality:'array',itemType:{module:'m',element:'leaf'}},{state:'missing'}],[{kind:'field',cardinality:'map',itemType:{module:'m',element:'leaf'}},{state:'missing'}]] as const){
  const p=prepare(element),collection=observations(p),core=collectCatalogCoreAssertionIdentities(p,collection),o=collection.observations.find(o=>o.operation==='scalarType'&&(o.identity as any).element==='v')!;
  expect((o.result as any).observation.meaning).toEqual(meaning);expect(core.entries.filter(e=>e.ruleName==='core.scalarType'&&e.assertion.sourcePointer==='/modules/0/elements/0/scalarType')).toEqual([]);
  expect((meaning.state==='missing'?core.absent:core.deferred).includes(o)).toBe(true);expect(core.complete).toBe(false);
 }
 const p=prepare({kind:'field',scalarType:'string'}),none=collectCatalogAssertionObservations(p,ownerDeclarations,fields);
 expect(none.scalarProfile).toBeNull();expect(none.observations.some(o=>o.operation==='scalarType')).toBe(false);
 expect(()=>observations(p,{...scalars})).toThrow('loaded assertion owner');
 expect(()=>collectCatalogCoreAssertionIdentities(p,{...observations(p)})).toThrow('collection custody');
 const other=prepare({kind:'field',scalarType:'string'});expect(()=>collectCatalogCoreAssertionIdentities(other,observations(p))).toThrow('collection custody');
});
test('loaded scalar owners cannot alter any original result before classification filtering',async()=>{
 const field={kind:'field',scalarType:'string',nullability:'required',cardinality:'one',future:{tuple:['a','b']}};
 const cases:[any,string][]=[...[
  "r.meaning.scalarType='integer'","r.meaning={state:'missing'}","r.meaning={state:'unknown',value:'string'}","r.meaning={state:'inapplicable',authoredScalarType:'string'}","r.identity.element='leaf'","r.identity.module='foreign'","r.path='/modules/0/elements/1/scalarType'","r.version='future'","r.operation='inspect-core-kind'","r.provenance='authenticated'","r.enforcement='database'","delete r.source.modules[0].elements[0].future","r.source.modules[0].elements[0].future.tuple.reverse()","r.source.modules[0].elements[0].scalarType='integer'"
 ].map(m=>[field,m] as [any,string]),
 [{kind:'field',scalarType:'future-scalar'},"r.meaning.value='other-future'"],[{kind:'field',scalarType:'future-scalar'},"r.meaning={state:'known',scalarType:'string'}"],
 [{kind:'field'},"r.meaning={state:'known',scalarType:'string'}"],[{scalarType:'string'},"r.meaning={state:'known',scalarType:'string'}"],
 [{scalarType:'future-scalar'},"r.meaning.authoredScalarType='other-future'"],[{kind:'field'},"r.meaning={state:'inapplicable'}"],
 [field,"r.meaning=Object.fromEntries(Object.entries(r.meaning).reverse())"]];
 for(const [element,mutation] of cases){const p=prepare(element),directory=await mkdtemp(join(tmpdir(),'truss-scalar-owner-control-'));
  try{
   const script=`import * as base from ${JSON.stringify(resolve(process.env.TRUSS_UMF_SCALAR_TYPE_PRODUCER!,'producer.js'))};\nexport function inspectCoreScalarType(...args){const r=base.inspectCoreScalarType(...args);if(args[1].element==='v'){${mutation}}return r}\n`;
   await writeFile(join(directory,'producer.js'),script);await writeFile(join(directory,'producer-manifest.json'),JSON.stringify({revision:scalars.sourceRevision,producerMode:'scalar-types',bundleSha256:new Bun.CryptoHasher('sha256').update(script).digest('hex')}));
   const loaded=await loadUmfScalarTypeProducer(directory),collection=observations(p,loaded);
   if(mutation.includes('Object.fromEntries'))expect(collectCatalogCoreAssertionIdentities(p,collection).entries.some(e=>e.ruleName==='core.scalarType')).toBe(true);
   else expect(()=>collectCatalogCoreAssertionIdentities(p,collection)).toThrow('scalarType');
  }finally{await rm(directory,{recursive:true,force:true})}
 }
});

test('original 0.8 remains explicitly unavailable to the pinned original 0.7 scalar owner',()=>{
 const p=prepare({kind:'field',scalarType:'string',nullability:'required',cardinality:'one'}),bytes=Buffer.from(JSON.stringify(p.documents[0]!.interpretation.target));
 const input={...p.original.input,documents:p.original.input.documents.map(d=>({...d,artifact:{identity:'doc',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')}}))};
 const modern=preparation.prepare(Buffer.from(JSON.stringify(input))),collection=observations(modern),core=collectCatalogCoreAssertionIdentities(modern,collection),scalarObservations=collection.observations.filter(o=>o.operation==='scalarType');
 expect(modern.documents[0]!.umfVersion).toBe('0.8.0');expect(scalarObservations.length).toBe(4);
 for(const observation of scalarObservations){expect(observation.result).toMatchObject({state:'unavailable',code:'CORE_SCALAR_TYPE_VERSION'});expect(core.deferred.includes(observation)).toBe(true)}
 expect(core.entries.some(e=>e.ruleName==='core.scalarType')).toBe(false);expect(core.complete).toBe(false);
 const coverage=assessCatalogObservationCoverage(modern,collection);expect(coverage.unavailable.filter(o=>o.operation==='scalarType').length).toBe(4);expect(coverage.availability).toBe('incomplete');
});

test('composed private report carries genuine scalar observations and exact ordered coverage',async()=>{
 const p=prepare({kind:'field',scalarType:'string',nullability:'required',cardinality:'one'}),queries:string[]=[];
 const connection={unsafe:async(query:string)=>{queries.push(query);
  if(query.includes('runtime_collect_report_documents'))return [{doc_id:'doc',doc_revision:'1',content_sha256:p.original.input.documents[0]!.artifact.sha256,ord:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'}];
  if(query.includes('runtime_collect_new_catalog_counts'))return [{types_added:'0',properties_added:'0',keys_added:'0',relationships_added:'0',endpoints_added:'0',elements_retired:'0',provisional_count:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'}];
  return []}};
 // Synthetic native rows qualify host composition only, never actual installation/count enforcement.
 const report=await collectCatalogReportPreparation(connection,p,'1',ownerDeclarations,fields,scalars),baseline=assessCatalogObservationCoverage(p,collectCatalogAssertionObservations(p,ownerDeclarations,fields));
 expect(report.ownerObservations.scalarProfile?.version).toBe(scalars.sourceRevision);
 expect(Number(report.observationCoverage.observationsRequired)).toBe(Number(baseline.observationsRequired)+4);
 expect(report.observationCoverage.availability).toBe('available');expect(report.coreAssertionIdentities.entries.filter(e=>e.ruleName==='core.scalarType').length).toBe(3);
 expect(report.coreAssertionIdentities.fieldMeanings.filter(e=>e.assertion.ruleName==='core.scalarType').every(e=>e.ownerProfile===report.ownerObservations.scalarProfile)).toBe(true);
 expect(report.coreAssertionIdentities.complete).toBe(false);expect(report.scope).toBe('original_new_catalog_report_preparation_only');expect(queries.at(-1)).toContain('runtime_require_catalog_observation');
});
