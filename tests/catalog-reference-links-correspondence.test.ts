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
import {loadUmfDeclarationProducer,loadUmfFieldAssertionProducer,loadUmfReferenceLinksProducer} from '../packages/umf-bun/src/index';
const preparation=await createCatalogInputPreparation(process.env.TRUSS_UMF_PRODUCER!,'/Users/erik/Projects/umf/package.json');
const declarations=await loadUmfDeclarationProducer(process.env.TRUSS_UMF_DECLARATION_PRODUCER!),fields=await loadUmfFieldAssertionProducer(process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER!),links=await loadUmfReferenceLinksProducer(process.env.TRUSS_UMF_REFERENCE_LINKS_PRODUCER!);
const fixture=(await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input;
const references=[{role:'record-type',module:'other',element:'R'},{role:'future-role',module:'m',element:'R','future/qualifier':{values:['b','a']}},{role:'record-type',module:'other',element:'R'}];
function prepare(properties:any={}){
 const model={umf:'0.7.0',id:'doc',vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[{id:'v',kind:'field',scalarType:'string',extensions:{},...properties},{id:'R',kind:'record',members:[],extensions:{}},{id:'w',kind:'field',extensions:{}}]},{id:'other',namespace:'other',elements:[{id:'R',kind:'record',members:[],extensions:{}}]}]};
 const input=structuredClone(fixture),bytes=Buffer.from(JSON.stringify(model));input.binding={state:'absent'};input.transforms=[];
 input.documents=[{documentId:'doc',documentRevision:'1',umfProfile:preparation.umfProfile,ingress:{kind:'native'},artifact:{identity:'doc',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')}}];
 return preparation.prepare(Buffer.from(JSON.stringify(input)));
}
function observations(p:ReturnType<typeof prepare>,owner=links){return collectCatalogAssertionObservations(p,declarations,fields,undefined,undefined,owner)}
test('ordered repeated cross-module generic links join original bytes separately from type assertions',()=>{
 const p=prepare({references}),c=observations(p),inventory=collectCatalogOriginalOccurrenceInventory(p,c),core=inventory.core;
 expect(core.referenceLinkDeclarations.length).toBe(1);expect(core.referenceLinks.length).toBe(3);
 expect(core.referenceLinks.map(l=>(l.originalMeaning as any).target)).toEqual([{identity:{module:'other',element:'R'},path:'/modules/1/elements/0',kind:'record'},{identity:{module:'m',element:'R'},path:'/modules/0/elements/1',kind:'record'},{identity:{module:'other',element:'R'},path:'/modules/1/elements/0',kind:'record'}]);
 expect(core.referenceLinks.map(l=>(l.originalMeaning as any).index)).toEqual([0,1,2]);expect(core.referenceLinks.map(l=>(l.originalMeaning as any).reference)).toEqual(references);
 for(const [index,link] of core.referenceLinks.entries()){
  expect(link.sourcePointer).toBe('/modules/0/elements/0/references/'+index);expect(link.ownerProfile).toBe(c.referenceLinksProfile!);expect(link.ownerProfile.version).toBe('9545b7119ceaa29ca7523e4722ec52412084d835');expect(link.source).toBe(p.original.input.documents[0]!.artifact);expect(link.typeAssertion).toBe('unverified');expect(link.interpretationQualified).toBe(false);
  const position=inventory.documents[0]!.occurrences.findIndex(r=>r.pointer===link.sourcePointer),row=inventory.documents[0]!.occurrences[position]!;
  expect(row.referenceLinks).toContain(link);expect(row.assertions).toEqual([]);expect(Buffer.from(originalCatalogOccurrenceBytes(p,inventory,0,position)).toString()).toBe(JSON.stringify(references[index]));expect(row.assertionMembershipComplete).toBe(false);
 }
 const declaration=core.referenceLinkDeclarations[0]!,position=inventory.documents[0]!.occurrences.findIndex(r=>r.pointer===declaration.sourcePointer);expect(inventory.documents[0]!.occurrences[position]!.referenceLinkDeclarations).toContain(declaration);expect(Buffer.from(originalCatalogOccurrenceBytes(p,inventory,0,position)).toString()).toBe(JSON.stringify(references));
 expect(core.entries.some(e=>e.assertion.sourcePointer.includes('/references'))).toBe(false);expect(core.complete).toBe(false);expect(inventory.complete).toBe(false);
 const opaque=core.referenceLinks[1]!.originalMeaning as any;expect(opaque.uninterpretedPaths).toEqual(['/modules/0/elements/0/references/1/future~1qualifier']);expect(Object.isFrozen(opaque.uninterpretedPaths)).toBe(true);expect(()=>opaque.uninterpretedPaths.push('/forged')).toThrow();expect(()=>opaque.reference['future/qualifier'].values.reverse()).toThrow();
});
test('empty absent and record-role-to-Field stay explicit generic link observations without type invention',()=>{
 for(const [properties,state,declarationCount,linkCount] of [[{},'missing',0,0],[{references:[]},'present',1,0],[{references:[{role:'record-type',module:'m',element:'w'}]},'present',1,1]] as const){
  const p=prepare(properties),c=observations(p),core=collectCatalogCoreAssertionIdentities(p,c),o=c.observations.find(o=>o.operation==='referenceLinks'&&(o.identity as any).element==='v')!;
  expect((o.result as any).observation.meaning.state).toBe(state);expect(core.referenceLinkDeclarations.length).toBe(declarationCount);expect(core.referenceLinks.length).toBe(linkCount);expect(core.entries.some(e=>e.ruleName.includes('record-type')||e.assertion.sourcePointer.includes('/references'))).toBe(false);
  if(state==='missing')expect(core.absent.includes(o)).toBe(true);if(linkCount)expect(core.referenceLinks[0]!.originalMeaning).toMatchObject({target:{kind:'field'},typeAssertion:'unverified'});
 }
 const p=prepare({references}),none=collectCatalogAssertionObservations(p,declarations,fields);expect(none.referenceLinksProfile).toBeNull();expect(none.observations.some(o=>o.operation==='referenceLinks')).toBe(false);
 expect(()=>observations(p,{...links})).toThrow('loaded assertion owner');expect(()=>collectCatalogCoreAssertionIdentities(p,{...observations(p)})).toThrow('collection custody');expect(()=>collectCatalogCoreAssertionIdentities(prepare({references}),observations(p))).toThrow('collection custody');
});
test('loaded reference owner substitutions refuse full context target role occurrence and authority changes',async()=>{
 const props={references},cases:[any,string][]=[...[
  "r.meaning.links.sort((a,b)=>a.reference.role.localeCompare(b.reference.role)||a.target.identity.module.localeCompare(b.target.identity.module));r.meaning.links.forEach((l,i)=>{const old=l.path;l.index=i;l.path=r.path+'/'+i;l.uninterpretedPaths=l.uninterpretedPaths.map(p=>l.path+p.slice(old.length))})","r.meaning.links.reverse()","r.meaning.links.pop()","r.meaning.links[2].index=0","r.meaning.links[2].path='/modules/0/elements/0/references/0'","r.meaning.links[0].reference.role='future-role'","r.meaning.links[0].reference.module='m'","r.meaning.links[0].reference.element='v'","r.meaning.links[0].target.identity.module='m'","r.meaning.links[0].target.identity.element='v'","r.meaning.links[0].target.path='/modules/0/elements/1'","r.meaning.links[0].target.kind='field'","delete r.meaning.links[0].target.kind","r.meaning.links[0].typeAssertion='verified'","r.meaning.links[0].enforcement='database'","delete r.meaning.links[1].reference['future/qualifier']","r.meaning.links[1].reference['future/qualifier'].values.reverse()","r.meaning.links[1].uninterpretedPaths=[]","r.meaning.links[1].uninterpretedPaths=['/foreign']","r.meaning={state:'missing'}","r.identity.element='w'","r.identity.module='other'","r.path='/modules/0/elements/2/references'","r.operation='inspect-core-record-type'","r.version='future'","r.provenance='authenticated'","r.enforcement='database'","delete r.source.modules[0].elements[0].references[1]['future/qualifier']","r.source.modules[0].elements[0].references.sort((a,b)=>a.role.localeCompare(b.role))"
 ].map(m=>[props,m] as [any,string]),[{},"r.meaning={state:'present',links:[]}"],[{references:[]},"r.meaning={state:'missing'}"],[props,"r.meaning=Object.fromEntries(Object.entries(r.meaning).reverse())"]];
 for(const [properties,mutation] of cases){const p=prepare(properties),directory=await mkdtemp(join(tmpdir(),'truss-reference-owner-control-'));
  try{const script=`import * as base from ${JSON.stringify(resolve(process.env.TRUSS_UMF_REFERENCE_LINKS_PRODUCER!,'producer.js'))};\nexport function inspectCoreReferenceLinks(...args){const r=base.inspectCoreReferenceLinks(...args);if(args[1].element==='v'){${mutation}}return r}\n`;
   await writeFile(join(directory,'producer.js'),script);await writeFile(join(directory,'producer-manifest.json'),JSON.stringify({revision:links.sourceRevision,producerMode:'reference-links',bundleSha256:new Bun.CryptoHasher('sha256').update(script).digest('hex')}));
   const c=observations(p,await loadUmfReferenceLinksProducer(directory));if(mutation.includes('Object.fromEntries'))expect(collectCatalogCoreAssertionIdentities(p,c).referenceLinks.length).toBe(3);else expect(()=>collectCatalogCoreAssertionIdentities(p,c)).toThrow('referenceLinks');
  }finally{await rm(directory,{recursive:true,force:true})}
 }
});
test('original0.8 is explicitly unavailable to original0.7 reference links owner',()=>{
 const p=prepare({references}),bytes=Buffer.from(JSON.stringify(p.documents[0]!.interpretation.target));const input={...p.original.input,documents:p.original.input.documents.map(d=>({...d,artifact:{identity:'doc',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')}}))};
 const modern=preparation.prepare(Buffer.from(JSON.stringify(input))),c=observations(modern),core=collectCatalogCoreAssertionIdentities(modern,c),coverage=assessCatalogObservationCoverage(modern,c);
 expect(coverage.unavailable.filter(o=>o.operation==='referenceLinks').length).toBe(4);expect(coverage.availability).toBe('incomplete');expect(core.referenceLinks).toEqual([]);expect(core.referenceLinkDeclarations).toEqual([]);
 for(const o of c.observations.filter(o=>o.operation==='referenceLinks')){expect(o.result).toMatchObject({state:'unavailable',code:'CORE_REFERENCE_LINKS_VERSION'});expect(core.deferred.includes(o)).toBe(true)}
});
test('private report forwards reference observations while synthetic native rows supply no type authority',async()=>{
 const p=prepare({references}),queries:string[]=[];const connection={unsafe:async(query:string)=>{queries.push(query);if(query.includes('runtime_collect_report_documents'))return [{doc_id:'doc',doc_revision:'1',content_sha256:p.original.input.documents[0]!.artifact.sha256,ord:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'}];if(query.includes('runtime_collect_new_catalog_counts'))return [{types_added:'0',properties_added:'0',keys_added:'0',relationships_added:'0',endpoints_added:'0',elements_retired:'0',provisional_count:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'}];return []}};
 const report=await collectCatalogReportPreparation(connection,p,'1',declarations,fields,undefined,undefined,links),baseline=assessCatalogObservationCoverage(p,collectCatalogAssertionObservations(p,declarations,fields));
 expect(report.ownerObservations.referenceLinksProfile?.version).toBe(links.sourceRevision);expect(Number(report.observationCoverage.observationsRequired)).toBe(Number(baseline.observationsRequired)+4);expect(report.observationCoverage.availability).toBe('available');expect(report.coreAssertionIdentities.referenceLinks.length).toBe(3);expect(report.coreAssertionIdentities.referenceLinks.every(l=>l.typeAssertion==='unverified'&&!l.interpretationQualified)).toBe(true);expect(report.coreAssertionIdentities.complete).toBe(false);expect(queries.at(-1)).toContain('runtime_require_catalog_observation');
});

test('loaded owner cannot mutate retained original request identity',async()=>{
 const p=prepare({references}),directory=await mkdtemp(join(tmpdir(),'truss-reference-request-control-'));
 try{
  const script=`import * as base from ${JSON.stringify(resolve(process.env.TRUSS_UMF_REFERENCE_LINKS_PRODUCER!,'producer.js'))};
export function inspectCoreReferenceLinks(...args){if(args[1].element==='v')args[1].element='w';return base.inspectCoreReferenceLinks(...args)}
`;
  await writeFile(join(directory,'producer.js'),script);await writeFile(join(directory,'producer-manifest.json'),JSON.stringify({revision:links.sourceRevision,producerMode:'reference-links',bundleSha256:new Bun.CryptoHasher('sha256').update(script).digest('hex')}));
  const c=observations(p,await loadUmfReferenceLinksProducer(directory)),o=c.observations.find(o=>o.operation==='referenceLinks'&&(o.identity as any).element==='v')!;
  expect(o.identity).toEqual({module:'m',element:'v'});expect(Object.isFrozen(o.identity)).toBe(true);expect(o.result).toMatchObject({state:'unavailable',name:'TypeError'});
  expect(collectCatalogCoreAssertionIdentities(p,c).referenceLinks).toEqual([]);expect(assessCatalogObservationCoverage(p,c).availability).toBe('incomplete');
 }finally{await rm(directory,{recursive:true,force:true})}
});
