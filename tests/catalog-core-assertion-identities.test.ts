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
