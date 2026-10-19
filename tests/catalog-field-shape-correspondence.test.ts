// SPDX-License-Identifier: MIT OR Apache-2.0
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
function prepare(element:any){
 const model={umf:'0.7.0',id:'doc',vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[{id:'v',extensions:{},...(element.kind==='record'?{members:[]}:{}),...element},{id:'leaf',kind:'field',scalarType:'string',nullability:'required',cardinality:'one',extensions:{}},{id:'leaf2',kind:'field',scalarType:'string',nullability:'required',cardinality:'one',extensions:{}},{id:'R',kind:'record',members:[{module:'m',element:element.kind==='field'?'v':'leaf'}],extensions:{}}]}]};
 const input=structuredClone(fixture),bytes=Buffer.from(JSON.stringify(model));input.binding={state:'absent'};input.transforms=[];
 input.documents=[{documentId:'doc',documentRevision:'1',umfProfile:preparation.umfProfile,ingress:{kind:'native'},artifact:{identity:'doc',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')}}];
 return preparation.prepare(new TextEncoder().encode(JSON.stringify(input)));
}
function meanings(p:ReturnType<typeof prepare>){return collectCatalogCoreAssertionIdentities(p,collectCatalogAssertionObservations(p,owner,fields))}
function selected(r:ReturnType<typeof meanings>,family:string){return r.fieldMeanings.filter(m=>m.assertion.ruleName==='core.'+family&&m.assertion.assertion.sourcePointer==='/modules/0/elements/0/'+family)}
test('original kind states preserve explicit roles, unknown labels and unspecified role',()=>{
 for(const [element,expected] of [[{kind:'field',scalarType:'string'},{state:'known',kind:'field'}],[{kind:'record'},{state:'known',kind:'record'}],[{kind:'group'},{state:'known',kind:'group'}],[{kind:'future-role'},{state:'unknown',value:'future-role'}],[{scalarType:'string'},{state:'unspecified'}]] as const){
  const p=prepare(element),collection=collectCatalogAssertionObservations(p,owner,fields),r=collectCatalogCoreAssertionIdentities(p,collection);
  const observation=collection.observations.find(o=>o.operation==='kind'&&(o.identity as any).element==='v')!;
  expect((observation.result as any).observation.meaning).toEqual(expected);
  const retained=selected(r,'kind');expect(retained.length).toBe(expected.state==='known'?1:0);
  if(retained.length){expect(retained[0]!.originalMeaning).toEqual(expected);expect(retained[0]!.ownerProfile).toBe(collection.fieldProfile!);expect(retained[0]!.interpretationQualified).toBe(false)}
  else expect(r.deferred.includes(observation)).toBe(true);
  expect(r.complete).toBe(false);
 }
});
test('one array and map preserve item meaning and actual transitioned Record shapes',()=>{
 const examples=[['one',{kind:'field',scalarType:'string',nullability:'required',cardinality:'one'},{string:'x'},{array:[]}],['array',{kind:'field',nullability:'required',cardinality:'array',itemType:{module:'m',element:'leaf'}},{array:[{string:'x'},{string:'x'}]},{string:'x'}],['map',{kind:'field',nullability:'required',cardinality:'map',itemType:{module:'m',element:'leaf'}},{map:{a:{string:'x'}}},{array:[]}]] as const;
 for(const [cardinality,element,value,wrong] of examples){
  const p=prepare(element),r=meanings(p),retained=selected(r,'cardinality')[0]!;
  expect(retained.originalMeaning).toEqual({state:'known',cardinality,...('itemType' in element?{itemType:element.itemType}:{})});
  expect(Object.isFrozen(retained.originalMeaning)).toBe(true);expect(retained.interpretationQualified).toBe(false);expect(r.complete).toBe(false);
  const check=(literal:unknown)=>record.checkRecord(p.documents[0]!.interpretation.target,{module:'m',element:'R'},[{field:{module:'m',element:'v'},state:'present',value:literal}]) as any;
  expect(p.documents[0]!.interpretation.target.umf).toBe('0.8.0');expect(check(value).validation.valid).toBe(true);expect(check(value).validation.complete).toBe(true);expect(check(wrong).validation.valid).toBe(false);
  if(cardinality==='array')expect(check({array:[{integerToken:'1'}]}).validation.valid).toBe(false);
 }
});
test('cardinality unspecified missing unknown and inapplicable remain separate and incomplete',()=>{
 for(const [element,expected] of [[{kind:'field',scalarType:'string',nullability:'required',cardinality:'unspecified'},{state:'known',cardinality:'unspecified'}],[{kind:'field',scalarType:'string',nullability:'required'},{state:'missing'}],[{kind:'field',nullability:'required',cardinality:'future-container'},{state:'unknown',value:'future-container'}],[{kind:'record'},{state:'inapplicable'}]] as const){
  const p=prepare(element),collection=collectCatalogAssertionObservations(p,owner,fields),r=collectCatalogCoreAssertionIdentities(p,collection);
  const observation=collection.observations.find(o=>o.operation==='cardinality'&&(o.identity as any).element==='v')!;
  expect((observation.result as any).observation.meaning).toEqual(expected);expect(selected(r,'cardinality').length).toBe(expected.state==='known'?1:0);
  if(expected.state==='missing')expect(r.absent.includes(observation)).toBe(true);
  if(['unknown','inapplicable'].includes(expected.state))expect(r.deferred.includes(observation)).toBe(true);
  expect(r.complete).toBe(false);
  if(element.kind==='field'){
   const checked=record.checkRecord(p.documents[0]!.interpretation.target,{module:'m',element:'R'},[]) as any;
   expect(checked.validation.complete).toBe(false);expect(checked.validation.diagnostics.some((d:any)=>d.code==='RECORD_CARDINALITY_UNKNOWN')).toBe(true);
  }
 }
});
test('loaded owners cannot substitute role, container shape, item references or opaque qualifiers',async()=>{
 const scalar={kind:'field',scalarType:'string',nullability:'required',cardinality:'one'};
 const array={kind:'field',nullability:'required',cardinality:'array',itemType:{module:'m',element:'leaf',future:{tuple:['a','b']}}};
 const cases:[string,any,string][]=[
  ['kind',scalar,"r.meaning.kind='record'"],['kind',scalar,"r.meaning={state:'unspecified'}"],['kind',scalar,"r.meaning={state:'unknown',value:'field'}"],['kind',scalar,"r.identity.element='leaf'"],['kind',scalar,"r.version='5.0.0'"],['kind',{scalarType:'string'},"r.meaning={state:'known',kind:'field'}"],['kind',{kind:'future-role'},"r.meaning.value='other-role'"],
  ...["r.meaning.cardinality='map'","r.meaning={state:'missing'}","r.meaning={state:'unknown',value:'array'}","delete r.meaning.itemType","r.meaning.itemType.element='leaf2'","delete r.meaning.itemType.future","r.meaning.itemType.future.tuple.reverse()","r.path='/modules/0/elements/1/cardinality'","r.version='3.0.0'","r.operation='inspect-core-nullability'"].map(m=>['cardinality',array,m] as [string,any,string]),
  ['cardinality',scalar,"r.meaning.itemType={module:'m',element:'leaf'}"],['cardinality',{kind:'field',nullability:'required'},"r.meaning={state:'known',cardinality:'one'}"],['cardinality',{kind:'field',cardinality:'future-container'},"r.meaning.value='other-container'"],
  ['cardinality',array,"r.meaning.itemType=Object.fromEntries(Object.entries(r.meaning.itemType).reverse())"],
 ];
 for(const [family,element,mutation] of cases){
  const p=prepare(element),directory=await mkdtemp(join(tmpdir(),'truss-field-shape-owner-'));
  try{
   const script=`import * as base from ${JSON.stringify(resolve(process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER!,'producer.js'))};\nexport const inspectCoreNullability=base.inspectCoreNullability,inspectCoreFacets=base.inspectCoreFacets;\nexport function inspectCoreElementKind(...args){const r=base.inspectCoreElementKind(...args);if(args[1].element==='v'){${family==='kind'?mutation:''}}return r}\nexport function inspectCoreCardinality(...args){const r=base.inspectCoreCardinality(...args);if(args[1].element==='v'){${family==='cardinality'?mutation:''}}return r}\n`;
   await writeFile(join(directory,'producer.js'),script);await writeFile(join(directory,'producer-manifest.json'),JSON.stringify({revision:fields.sourceRevision,producerMode:'assertion-fields',bundleSha256:new Bun.CryptoHasher('sha256').update(script).digest('hex')}));
   const controlled=await loadUmfFieldAssertionProducer(directory),collection=collectCatalogAssertionObservations(p,owner,controlled);
   if(mutation.includes('Object.fromEntries')){
    const r=collectCatalogCoreAssertionIdentities(p,collection),retained=selected(r,'cardinality')[0]!;
    expect(retained.originalMeaning.itemType).toEqual(array.itemType);expect(Object.isFrozen(retained.originalMeaning.itemType.future)).toBe(true);expect(retained.interpretationQualified).toBe(false);
   }else expect(()=>collectCatalogCoreAssertionIdentities(p,collection)).toThrow(family);
  }finally{await rm(directory,{recursive:true,force:true})}
 }
});


test('facets retain interpreted groups and actual value boundaries after reversible transition',()=>{
 const cases=[['string',{length:{max:1,unit:'unicode-scalar'}},{string:'😀'},{string:'😀😀'}],['binary',{length:{max:1,unit:'byte'}},{binaryHex:'ff'},{binaryHex:'ffaa'}],['integer',{integerWidth:{bits:8,signed:true}},{integerToken:'127'},{integerToken:'128'}],['decimal',{precision:5,scale:2},{decimalToken:'12.34'},{decimalToken:'12.345'}],['decimal',{precision:5,scale:2},{decimalToken:'999.99'},{decimalToken:'1000.00'}]] as const;
 for(const [scalarType,facets,good,bad] of cases){
  const p=prepare({kind:'field',scalarType,nullability:'required',cardinality:'one',facets}),r=meanings(p),retained=selected(r,'facets')[0]!;
  expect(retained.originalMeaning).toEqual({state:'known',facets,interpreted:facets,uninterpretedPaths:[]});
  expect(retained.ownerState).toBe('known');expect(retained.interpretationQualified).toBe(false);expect(Object.isFrozen(retained.originalMeaning)).toBe(true);
  const check=(literal:unknown)=>record.checkRecord(p.documents[0]!.interpretation.target,{module:'m',element:'R'},[{field:{module:'m',element:'v'},state:'present',value:literal}]) as any;
  expect(check(good).validation.valid).toBe(true);expect(check(good).validation.complete).toBe(true);expect(check(bad).validation.valid).toBe(false);expect(r.complete).toBe(false);
 }
});
test('facets retain independent original warning paths and unknown units without invented interpretation',()=>{
 const facets={length:{max:2,unit:'unicode-scalar',future:{tuple:['a','b']}},future:{policy:'opaque'}},p=prepare({kind:'field',scalarType:'string',nullability:'required',cardinality:'one',facets}),r=meanings(p),retained=selected(r,'facets')[0]!;
 expect(retained.originalMeaning).toEqual({state:'partial',facets,interpreted:{length:{max:2,unit:'unicode-scalar'}},uninterpretedPaths:['/modules/0/elements/0/facets/future','/modules/0/elements/0/facets/length/future']});
 expect(retained.ownerState).toBe('partial');expect(retained.interpretationQualified).toBe(false);expect(Object.isFrozen(retained.originalMeaning.facets.length.future)).toBe(true);
 const unknown=meanings(prepare({kind:'field',scalarType:'string',nullability:'required',cardinality:'one',facets:{length:{max:2,unit:'future-unit'}}}));
 expect(selected(unknown,'facets')[0]!.originalMeaning.interpreted).toEqual({});expect(selected(unknown,'facets')[0]!.ownerState).toBe('partial');
 const empty=selected(meanings(prepare({kind:'field',scalarType:'string',facets:{}})),'facets')[0]!;
 expect(empty.originalMeaning).toEqual({state:'known',facets:{},interpreted:{},uninterpretedPaths:[]});expect(empty.interpretationQualified).toBe(false);
 const missing=prepare({kind:'field',scalarType:'string'}),collection=collectCatalogAssertionObservations(missing,owner,fields),mr=collectCatalogCoreAssertionIdentities(missing,collection);
 const observation=collection.observations.find(o=>o.operation==='facets'&&(o.identity as any).element==='v')!;expect(mr.absent.includes(observation)).toBe(true);expect(selected(mr,'facets')).toEqual([]);
});
test('loaded facet owners cannot replace retained values projections states or unknown paths',async()=>{
 const element={kind:'field',scalarType:'string',nullability:'required',cardinality:'one',facets:{length:{max:2,unit:'unicode-scalar',future:{tuple:['a','b']}},future:{policy:'opaque'}}};
 const mutations=["r.meaning.facets.length.max=3","r.meaning.interpreted.length.max=3","delete r.meaning.interpreted.length","r.meaning.interpreted.future={policy:'invented'}","delete r.meaning.facets.future","r.meaning.facets.length.future.tuple.reverse()","r.meaning.uninterpretedPaths=[]","r.meaning.state='known'","r.meaning={state:'missing'}","r.meaning={state:'inapplicable'}","r.path='/modules/0/elements/1/facets'","r.version='2.0.0'","r.meaning.facets=Object.fromEntries(Object.entries(r.meaning.facets).reverse())"];
 const cases:readonly (readonly [any,string])[]=[...mutations.map(m=>[element,m] as const),
  [{kind:'field',scalarType:'integer',nullability:'required',cardinality:'one',facets:{integerWidth:{bits:8,signed:true}}},"r.meaning.interpreted.integerWidth.bits=16"],
  [{kind:'field',scalarType:'integer',nullability:'required',cardinality:'one',facets:{integerWidth:{bits:8,signed:true}}},"r.meaning.interpreted.integerWidth.signed=false"],
  [{kind:'field',scalarType:'decimal',nullability:'required',cardinality:'one',facets:{precision:5,scale:2}},"r.meaning.interpreted.precision=6"],
  [{kind:'field',scalarType:'decimal',nullability:'required',cardinality:'one',facets:{precision:5,scale:2}},"r.meaning.interpreted.scale=3"],
  [{kind:'field',scalarType:'string'},"r.meaning={state:'known',facets:{},interpreted:{},uninterpretedPaths:[]}"],
  [{kind:'field',scalarType:'string',facets:{length:{max:2,unit:'future-unit'}}},"r.meaning.interpreted.length={max:2,unit:'unicode-scalar'}"]];
 for(const [sourceElement,mutation] of cases){
  const p=prepare(sourceElement),directory=await mkdtemp(join(tmpdir(),'truss-facet-owner-'));
  try{
   const script=`import * as base from ${JSON.stringify(resolve(process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER!,'producer.js'))};\nexport const inspectCoreElementKind=base.inspectCoreElementKind,inspectCoreNullability=base.inspectCoreNullability,inspectCoreCardinality=base.inspectCoreCardinality;\nexport function inspectCoreFacets(...args){const r=base.inspectCoreFacets(...args);if(args[1].element==='v'){${mutation}}return r}\n`;
   await writeFile(join(directory,'producer.js'),script);await writeFile(join(directory,'producer-manifest.json'),JSON.stringify({revision:fields.sourceRevision,producerMode:'assertion-fields',bundleSha256:new Bun.CryptoHasher('sha256').update(script).digest('hex')}));
   const controlled=await loadUmfFieldAssertionProducer(directory),collection=collectCatalogAssertionObservations(p,owner,controlled);
   if(mutation.includes('Object.fromEntries'))expect(selected(collectCatalogCoreAssertionIdentities(p,collection),'facets')[0]!.originalMeaning.facets).toEqual(element.facets);
   else expect(()=>collectCatalogCoreAssertionIdentities(p,collection)).toThrow('facets');
  }finally{await rm(directory,{recursive:true,force:true})}
 }
});

import {collectCatalogFacetRuleFamilies,requireOriginalCatalogFacetRuleFamilies} from '../packages/umf-bun/src/catalog-facet-rule-families';
test('distinct decimal duties share an original pointer without collapsing family identity',()=>{
 const p=prepare({kind:'field',scalarType:'decimal',nullability:'required',cardinality:'one',facets:{precision:5,scale:2,future:{policy:'opaque'}}});
 const collection=collectCatalogAssertionObservations(p,owner,fields),candidate=collectCatalogFacetRuleFamilies(p,collection);
 expect(candidate.rules.map(r=>r.identity.family)).toEqual(['decimal_precision','decimal_fixed_scale']);
 expect(candidate.rules.map(r=>r.identity.occurrence.sourcePointer)).toEqual(['/modules/0/elements/0/facets','/modules/0/elements/0/facets']);
 expect(candidate.rules.map(r=>r.parameters)).toEqual([{precision:5,scale:2},{precision:5,scale:2}]);
 expect(new Set(candidate.rules.map(r=>JSON.stringify(r.identity))).size).toBe(2);
 for(const rule of candidate.rules){
  expect(rule.source).toBe(p.original.input.documents[0].artifact);expect(rule.identity.profile).toBe(candidate.profile);
  expect(rule.identity.semanticOwnerProfile).toBe(collection.fieldProfile!);expect(candidate.carriers.includes(rule.carrier)).toBe(true);
  expect(rule.identity.occurrence).toBe(rule.carrier.assertion.assertion);expect(rule.enforcement).toBe('none');expect(rule.interpretationQualified).toBe(false);
  expect(rule.carrier.originalMeaning.uninterpretedPaths).toEqual(['/modules/0/elements/0/facets/future']);expect(Object.isFrozen(rule.parameters)).toBe(true);
 }
 expect(candidate.complete).toBe(false);expect(candidate.semanticFamilyCoverageComplete).toBe(false);expect(candidate.interpretationQualified).toBe(false);
 const bytes=Buffer.from(candidate.manifest.bytesBase64,'base64');expect(new Bun.CryptoHasher('sha256').update(bytes).digest('hex')).toBe(candidate.profile.sha256);
 requireOriginalCatalogFacetRuleFamilies(p,candidate);
 expect(()=>requireOriginalCatalogFacetRuleFamilies(p,{...candidate})).toThrow('candidate custody');
 const other=prepare({kind:'field',scalarType:'decimal',nullability:'required',cardinality:'one',facets:{precision:5,scale:2,future:{policy:'opaque'}}});
 expect(()=>requireOriginalCatalogFacetRuleFamilies(other,candidate)).toThrow('candidate custody');
 expect(()=>collectCatalogFacetRuleFamilies(other,collection)).toThrow('observation collection custody');
 const repeat=collectCatalogFacetRuleFamilies(p,collection);expect(repeat.rules.map(r=>r.identity)).toEqual(candidate.rules.map(r=>r.identity));
});
test('facet families follow interpreted groups while empty and unknown groups invent no duty',()=>{
 for(const [scalarType,facets,families] of [['string',{length:{max:2,unit:'unicode-scalar'}},['length']],['integer',{integerWidth:{bits:8,signed:true}},['integer_width']],['string',{},[]],['string',{length:{max:2,unit:'future-unit'}},[]]] as const){
  const p=prepare({kind:'field',scalarType,facets}),candidate=collectCatalogFacetRuleFamilies(p,collectCatalogAssertionObservations(p,owner,fields));
  expect(candidate.rules.map(r=>r.identity.family)).toEqual([...families]);expect(candidate.complete).toBe(false);
  expect(candidate.carriers.length).toBe(1);expect(candidate.carriers[0]!.interpretationQualified).toBe(false);
 }
});
