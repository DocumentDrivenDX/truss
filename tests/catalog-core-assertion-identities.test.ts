import {test,expect} from 'bun:test';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {collectCatalogAssertionObservations} from '../packages/umf-bun/src/catalog-assertion-observations';
import {collectCatalogCoreAssertionIdentities} from '../packages/umf-bun/src/catalog-core-assertion-identities';
import {loadUmfDeclarationProducer,loadUmfFieldAssertionProducer} from '../packages/umf-bun/src/index';
const preparation=await createCatalogInputPreparation(process.env.TRUSS_UMF_PRODUCER!,'/Users/erik/Projects/umf/package.json');
const owner=await loadUmfDeclarationProducer(process.env.TRUSS_UMF_DECLARATION_PRODUCER!),fields=await loadUmfFieldAssertionProducer(process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER!);
const input=structuredClone((await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input);input.binding={state:'absent'};input.transforms=[];
const model={umf:'0.7.0',id:'doc',vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[{id:'v',kind:'field',scalarType:'string',nullability:'required',cardinality:'one',facets:{future:{value:'opaque'}},extensions:{}},{id:'w',kind:'field',scalarType:'string',nullability:'required',cardinality:'one',extensions:{}}]}]};
const bytes=Buffer.from(JSON.stringify(model));input.documents=[{documentId:'doc',documentRevision:'1',umfProfile:preparation.umfProfile,ingress:{kind:'native'},artifact:{identity:'doc',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')}}];
const prepared=preparation.prepare(new TextEncoder().encode(JSON.stringify(input))),observations=collectCatalogAssertionObservations(prepared,owner,fields);
test('original pointer identities retain partial meanings without inventing missing facets or enforcement',()=>{
 const result=collectCatalogCoreAssertionIdentities(prepared,observations);expect(result.entries.length).toBe(7);expect(result.absent.length).toBe(2);expect(result.complete).toBe(false);expect(result.deferred.length).toBeGreaterThan(0);
 for(const entry of result.entries){expect(entry.source).toBe(prepared.original.input.documents[0].artifact);expect(entry.assertion.definitionPin).toBe(entry.source.sha256);expect(entry.enforcement).toBe('none');expect(entry.reason).toBe('unqualified');expect(entry.ownerEvidence.sha256.length).toBe(64)}
 expect(result.entries.find(e=>e.ruleName==='core.facets')!.assertion.sourcePointer).toBe('/modules/0/elements/0/facets');
});
test('cloned observation collections cannot issue source identities',()=>{
 expect(()=>collectCatalogCoreAssertionIdentities(prepared,{...observations})).toThrow('observation collection custody');
});
test('authored key and relationship IDs remain qualified by original occurrence pointers',()=>{
 const declared:any=structuredClone(model);
 declared.modules[0].elements.push({id:'R',kind:'record',members:[{module:'m',element:'v'}],keys:[{id:'same',name:'key',fields:[{module:'m',element:'v'}],primary:true}],extensions:{}});
 declared.modules[0].relationships=[{id:'same',name:'self',source:[{module:'m',element:'R'}],target:[{module:'m',element:'R',key:'same'}],sourceMultiplicity:{min:0,max:1},targetMultiplicity:{min:0,max:1},targetLifecycle:'independent',directed:true}];
 const originalInput=structuredClone(input),source=Buffer.from(JSON.stringify(declared));originalInput.documents[0].artifact={identity:'declared',bytesBase64:source.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(source).digest('hex')};
 const prepared=preparation.prepare(new TextEncoder().encode(JSON.stringify(originalInput))),result=collectCatalogCoreAssertionIdentities(prepared,collectCatalogAssertionObservations(prepared,owner,fields));
 const entries=result.entries.filter(e=>e.ruleName==='core.keys'||e.ruleName==='core.relationships');expect(entries.length).toBe(2);
 expect(entries.map(e=>e.assertion.sourcePointer)).toEqual(['/modules/0/relationships/0','/modules/0/elements/2/keys/0']);
 expect(entries.map(e=>e.assertion.kind)).toEqual(['authored','authored']);expect(entries.map(e=>(e.assertion as any).authoredIdentity)).toEqual(['same','same']);
 expect(entries.every(e=>e.enforcement==='none')).toBe(true);expect(result.complete).toBe(false);
});
test('original 0.8 schema properties keep authored pointers and legacy API failures explicit',()=>{
 const declared:any=structuredClone(model);declared.umf='0.8.0';declared.title='Original document annotation';declared.modules[0].elements[0].allowedValues=[{string:'red'}];declared.modules[0].elements[0].default={value:{string:'red'},on:'missing'};
 const originalInput=structuredClone(input),source=Buffer.from(JSON.stringify(declared));originalInput.documents[0].artifact={identity:'original08',bytesBase64:source.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(source).digest('hex')};
 const prepared=preparation.prepare(new TextEncoder().encode(JSON.stringify(originalInput))),result=collectCatalogCoreAssertionIdentities(prepared,collectCatalogAssertionObservations(prepared,owner,fields));
 expect(result.entries.map(e=>e.assertion.sourcePointer)).toEqual(['/modules/0/elements/0/allowedValues','/modules/0/elements/0/default','/modules/0/elements/0/facets']);
 expect(result.deferred.some(o=>o.operation==='schema_properties'&&(o.identity as any).scope==='document')).toBe(true);expect(result.entries.some(e=>e.ruleName.endsWith('.title'))).toBe(false);
 expect(result.deferred.some(o=>(o.result as any).state==='unavailable')).toBe(true);expect(result.complete).toBe(false);expect(result.entries.every(e=>e.enforcement==='none')).toBe(true);
});


import {collectCatalogOriginalOccurrenceInventory,originalCatalogOccurrenceBytes} from '../packages/umf-bun/src/catalog-original-occurrence-inventory';
test('complete original value coverage keeps unclassified and opaque meaning unavailable',()=>{
 const result=collectCatalogOriginalOccurrenceInventory(prepared,observations),doc=result.documents[0]!;
 // Independent traversal of the authored test model, not the producer's occurrence array.
 const expected:string[]=[];const visit=(value:any,pointer:string)=>{expected.push(pointer);if(Array.isArray(value))value.forEach((v,i)=>visit(v,pointer+'/'+i));else if(value!==null&&typeof value==='object')for(const [k,v] of Object.entries(value))visit(v,pointer+'/'+k.replace(/~/g,'~0').replace(/\//g,'~1'))};visit(model,'');
 expect(doc.occurrences.map(o=>o.pointer)).toEqual(expected);expect(result.sourceCoverageComplete).toBe(true);expect(result.complete).toBe(false);expect(result.interpretationQualified).toBe(false);
 expect(doc.occurrences.filter(o=>o.disposition==='assertion').map(o=>[o.pointer,o.assertions[0]!.ruleName])).toEqual([
  ['/modules/0/elements/0/kind','core.kind'],['/modules/0/elements/0/nullability','core.nullability'],['/modules/0/elements/0/cardinality','core.cardinality'],['/modules/0/elements/0/facets','core.facets'],
  ['/modules/0/elements/1/kind','core.kind'],['/modules/0/elements/1/nullability','core.nullability'],['/modules/0/elements/1/cardinality','core.cardinality'],
 ]);
 const opaque=doc.occurrences.find(o=>o.pointer==='/modules/0/elements/0/facets/future/value')!;expect(opaque.disposition).toBe('unavailable');expect(opaque.assertions).toEqual([]);
 const pos=doc.occurrences.indexOf(opaque);expect(new TextDecoder().decode(originalCatalogOccurrenceBytes(prepared,result,0,pos))).toBe('"opaque"');
 for(const row of doc.occurrences){expect(row.sourceSha256).toBe(input.documents[0].artifact.sha256);expect(row.owner.documentId).toBe('doc');for(const assertion of row.assertions){expect(assertion.assertion.sourcePointer).toBe(row.pointer);expect(assertion.enforcement).toBe('none')}}
});
test('occurrence inventory retains original custody instead of copied or foreign preparation',()=>{
 const result=collectCatalogOriginalOccurrenceInventory(prepared,observations);
 expect(()=>collectCatalogOriginalOccurrenceInventory(prepared,{...observations})).toThrow('observation collection custody');
 expect(()=>originalCatalogOccurrenceBytes(prepared,{...result},0,0)).toThrow('inventory custody');
 const other=preparation.prepare(new TextEncoder().encode(JSON.stringify(input)));
 expect(()=>originalCatalogOccurrenceBytes(other,result,0,0)).toThrow('inventory custody');
 const otherObservations=collectCatalogAssertionObservations(other,owner,fields);
 expect(()=>collectCatalogOriginalOccurrenceInventory(other,observations)).toThrow('observation collection custody');
 expect(()=>collectCatalogOriginalOccurrenceInventory(prepared,otherObservations)).toThrow('observation collection custody');
 const returned=originalCatalogOccurrenceBytes(prepared,result,0,0);returned.fill(0);
 expect(new TextDecoder().decode(originalCatalogOccurrenceBytes(prepared,result,0,0))).toBe(JSON.stringify(model));
 expect(()=>originalCatalogOccurrenceBytes(prepared,result,-1,0)).toThrow('position');
});

test('mixed original versions and lexical numeric opaque bytes remain distinct from transition targets',()=>{
 const originalInput=structuredClone(input);const sources=['0.7.0','0.8.0'].map((version,i)=>{
  const source:any=structuredClone(model);source.umf=version;source.id='doc'+i;source.modules[0].elements[0].facets.future.value='unsafe';
  return JSON.stringify(source).replace('"unsafe"','1.2300e+2');
 });
 originalInput.documents=sources.map((text,i)=>{const b=Buffer.from(text);return {...structuredClone(input.documents[0]),documentId:'doc'+i,artifact:{identity:'doc'+i,bytesBase64:b.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(b).digest('hex')}}});
 const p=preparation.prepare(new TextEncoder().encode(JSON.stringify(originalInput))),o=collectCatalogAssertionObservations(p,owner,fields),r=collectCatalogOriginalOccurrenceInventory(p,o);
 expect(r.documents.map(d=>d.sourceVersion)).toEqual(['0.7.0','0.8.0']);expect(p.documents[0]!.interpretation.target.umf).toBe('0.8.0');
 for(let i=0;i<2;i++){
  const d=r.documents[i]!,position=d.occurrences.findIndex(o=>o.pointer==='/modules/0/elements/0/facets/future/value');
  expect(d.occurrences[position]!.disposition).toBe('unavailable');expect(d.occurrences[position]!.sourceSha256).toBe(originalInput.documents[i].artifact.sha256);
  expect(new TextDecoder().decode(originalCatalogOccurrenceBytes(p,r,i,position))).toBe('1.2300e+2');
  expect(new TextDecoder().decode(originalCatalogOccurrenceBytes(p,r,i,0))).toBe(sources[i]);
  expect(d.occurrences.every(o=>o.owner.documentId==='doc'+i)).toBe(true);
 }
 expect(r.complete).toBe(false);
});

test('the original UMF profile still refuses unsafe integer source before inventory issuance',()=>{
 const originalInput=structuredClone(input),source=JSON.stringify(model).replace('"opaque"','9007199254740993'),b=Buffer.from(source);
 originalInput.documents[0].artifact={identity:'unsafe',bytesBase64:b.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(b).digest('hex')};
 expect(()=>preparation.prepare(new TextEncoder().encode(JSON.stringify(originalInput)))).toThrow('Integer exceeds exact JavaScript range');
});
