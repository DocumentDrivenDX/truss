import {test,expect} from 'bun:test';
import {mkdtemp,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {collectCatalogAssertionObservations} from '../packages/umf-bun/src/catalog-assertion-observations';
import {collectCatalogCoreAssertionIdentities} from '../packages/umf-bun/src/catalog-core-assertion-identities';
import {loadUmfProducer,loadUmfDeclarationProducer,loadUmfFieldAssertionProducer} from '../packages/umf-bun/src/index';
const preparation=await createCatalogInputPreparation(process.env.TRUSS_UMF_PRODUCER!,'/Users/erik/Projects/umf/package.json');
const record=await loadUmfProducer(process.env.TRUSS_UMF_PRODUCER!),owner=await loadUmfDeclarationProducer(process.env.TRUSS_UMF_DECLARATION_PRODUCER!),fields=await loadUmfFieldAssertionProducer(process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER!);
const fixture=(await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input;
function prepare(nullability?:string){
 const model={umf:'0.7.0',id:'doc',vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[{id:'v',kind:'field',scalarType:'string',...(nullability===undefined?{}:{nullability}),cardinality:'one',extensions:{}},{id:'R',kind:'record',members:[{module:'m',element:'v'}],extensions:{}}]}]};
 const input=structuredClone(fixture),bytes=Buffer.from(JSON.stringify(model));input.binding={state:'absent'};input.transforms=[];
 input.documents=[{documentId:'doc',documentRevision:'1',umfProfile:preparation.umfProfile,ingress:{kind:'native'},artifact:{identity:'doc',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')}}];
 return preparation.prepare(new TextEncoder().encode(JSON.stringify(input)));
}
test('original nullability meanings remain distinct through reversible transition and actual Record behavior',()=>{
 for(const availability of ['required','absent-allowed','unspecified']){
  const p=prepare(availability),collection=collectCatalogAssertionObservations(p,owner,fields),r=collectCatalogCoreAssertionIdentities(p,collection);
  expect(p.documents[0]!.umfVersion).toBe('0.7.0');expect(p.documents[0]!.interpretation.target.umf).toBe('0.8.0');
  expect(p.documents[0]!.interpretation.target.modules[0]!.elements[0]!.nullability).toBe(availability);
  const meanings=r.fieldMeanings.filter(m=>m.assertion.ruleName==='core.nullability');expect(meanings.length).toBe(1);const retained=meanings[0]!;
  expect(retained.originalMeaning).toEqual({state:'known',nullability:availability});expect(retained.ownerProfile).toBe(collection.fieldProfile!);
  expect(r.entries.includes(retained.assertion)).toBe(true);expect(retained.assertion.assertion.sourcePointer).toBe('/modules/0/elements/0/nullability');
  expect(Object.isFrozen(retained.originalMeaning)).toBe(true);expect(retained.interpretationQualified).toBe(false);expect(r.complete).toBe(false);
  const absent=record.checkRecord(p.documents[0]!.interpretation.target,{module:'m',element:'R'},[]) as any;
  const present=record.checkRecord(p.documents[0]!.interpretation.target,{module:'m',element:'R'},[{field:{module:'m',element:'v'},state:'present',value:{string:'ok'}}]) as any;
  expect(present.validation.valid).toBe(true);
  expect(absent.validation.valid).toBe(availability!=='required');
  expect(absent.validation.diagnostics.some((d:any)=>d.code==='REQUIRED_RECORD_VALUE')).toBe(availability==='required');
  expect(absent.validation.diagnostics.some((d:any)=>d.code==='RECORD_AVAILABILITY_UNKNOWN')).toBe(availability==='unspecified');
  expect(present.validation.complete).toBe(availability!=='unspecified');
  if(availability==='absent-allowed')expect(absent.validation.complete).toBe(true);
  if(availability==='unspecified')expect(absent.validation.complete).toBe(false);
 }
});
test('future authored nullability remains unavailable to the known semantic subset',()=>{
 const p=prepare('future-availability'),r=collectCatalogCoreAssertionIdentities(p,collectCatalogAssertionObservations(p,owner,fields));
 expect(r.fieldMeanings.filter(m=>m.assertion.ruleName==='core.nullability')).toEqual([]);expect(r.entries.some(e=>e.ruleName==='core.nullability')).toBe(false);
 expect(r.deferred.some(o=>o.operation==='nullability'&&(o.result as any).observation.meaning.value==='future-availability')).toBe(true);expect(r.complete).toBe(false);
});
test('loaded diagnostic owners cannot replace required meaning or its context before state filtering',async()=>{
 const mutations=["r.meaning.nullability='absent-allowed'","r.meaning.nullability='unspecified'","r.meaning={state:'missing'}","r.meaning={state:'unknown',value:'required'}","r.meaning={state:'inapplicable'}","r.meaning={state:'partial',nullability:'required'}","r.identity.element='R'","r.path='/modules/0/elements/1/nullability'","r.operation='inspect-core-cardinality'","r.version='4.0.0'"];
 const cases:readonly (readonly [string|undefined,string])[]=[...mutations.map(m=>['required',m] as const),['future-availability',"r.meaning.value='different-future'"],[undefined,"r.meaning={state:'known',nullability:'required'}"]];
 for(const [availability,mutation] of cases){
  const p=prepare(availability);
  const directory=await mkdtemp(join(tmpdir(),'truss-nullability-owner-'));
  try{
   // Real loader/collection path, controlled fixture pins only; no issuer claim.
   const script=`import * as base from ${JSON.stringify(resolve(process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER!,'producer.js'))};\nexport const inspectCoreElementKind=base.inspectCoreElementKind,inspectCoreCardinality=base.inspectCoreCardinality,inspectCoreFacets=base.inspectCoreFacets;\nexport function inspectCoreNullability(...args){const r=base.inspectCoreNullability(...args);if(args[1].element==='v'){${mutation}}return r}\n`;
   await writeFile(join(directory,'producer.js'),script);await writeFile(join(directory,'producer-manifest.json'),JSON.stringify({revision:fields.sourceRevision,producerMode:'assertion-fields',bundleSha256:new Bun.CryptoHasher('sha256').update(script).digest('hex')}));
   const controlled=await loadUmfFieldAssertionProducer(directory),collection=collectCatalogAssertionObservations(p,owner,controlled);
   expect(()=>collectCatalogCoreAssertionIdentities(p,collection)).toThrow('nullability');
  }finally{await rm(directory,{recursive:true,force:true})}
 }
});


test('original missing Field and inapplicable Record nullability remain distinct observations',()=>{
 const p=prepare(),collection=collectCatalogAssertionObservations(p,owner,fields),r=collectCatalogCoreAssertionIdentities(p,collection);
 const observations=collection.observations.filter(o=>o.operation==='nullability');
 expect(observations.map(o=>(o.result as any).observation.meaning)).toEqual([{state:'missing'},{state:'inapplicable'}]);
 expect(r.absent.some(o=>o===observations[0])).toBe(true);expect(r.deferred.some(o=>o===observations[1])).toBe(true);
 expect(r.fieldMeanings.filter(m=>m.assertion.ruleName==='core.nullability')).toEqual([]);expect(r.entries.some(e=>e.ruleName==='core.nullability')).toBe(false);expect(r.complete).toBe(false);
 const absent=record.checkRecord(p.documents[0]!.interpretation.target,{module:'m',element:'R'},[]) as any;
 expect(absent.validation.complete).toBe(false);expect(absent.validation.diagnostics.some((d:any)=>d.code==='RECORD_AVAILABILITY_UNKNOWN')).toBe(true);
});
