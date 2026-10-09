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
 const result=collectCatalogCoreAssertionIdentities(prepared,observations);expect(result.entries.length).toBe(7);expect(result.absent.length).toBe(1);expect(result.complete).toBe(false);expect(result.deferred.length).toBeGreaterThan(0);
 for(const entry of result.entries){expect(entry.source).toBe(prepared.original.input.documents[0].artifact);expect(entry.assertion.definitionPin).toBe(entry.source.sha256);expect(entry.enforcement).toBe('none');expect(entry.reason).toBe('unqualified');expect(entry.ownerEvidence.sha256.length).toBe(64)}
 expect(result.entries.find(e=>e.ruleName==='core.facets')!.assertion.sourcePointer).toBe('/modules/0/elements/0/facets');
});
test('cloned observation collections cannot issue source identities',()=>{
 expect(()=>collectCatalogCoreAssertionIdentities(prepared,{...observations})).toThrow('observation collection custody');
});
