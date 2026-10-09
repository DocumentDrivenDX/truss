import {test,expect} from 'bun:test';
import {loadUmfProducer,loadUmfDeclarationProducer} from '../packages/umf-bun/src/index';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {collectCatalogAssertionObservations} from '../packages/umf-bun/src/catalog-assertion-observations';
const recordDirectory=process.env.TRUSS_UMF_PRODUCER;const metadataDirectory=process.env.TRUSS_UMF_DECLARATION_PRODUCER;
if(!recordDirectory||!metadataDirectory)throw Error('Both original pinned owner producer directories required');
const record=await loadUmfProducer(recordDirectory);const metadata=await loadUmfDeclarationProducer(metadataDirectory);
const original=JSON.stringify({umf:'0.7.0',id:'source',vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[{id:'R',kind:'record',members:[{module:'m',element:'label'}],keys:[{id:'K',name:'key',fields:[{module:'m',element:'label'}],primary:true}],extensions:{}},{id:'label',name:'label',kind:'field',scalarType:'string',nullability:'required',cardinality:'one',extensions:{}}],relationships:[{id:'self',name:'self',source:[{module:'m',element:'R'}],target:[{module:'m',element:'R',key:'K'}],sourceMultiplicity:{min:0,max:1},targetMultiplicity:{min:0,max:1},targetLifecycle:'independent',directed:true}]}]});
const inspected=record.inspect(original);
test('original authored keys are inspected through owner API with source pointer and unverified provenance',()=>{const observation=metadata.inspectKeys(inspected.source,{module:'m',element:'R'});expect(observation.meaning.state).toBe('known');expect(observation.meaning.keys[0].id).toBe('K');expect(observation.path).toBe('/modules/0/elements/0/keys');expect(observation.provenance).toBe('unverified')});
test('relationship meaning is version scoped and cannot borrow upgraded envelope semantics',()=>{const original=metadata.inspectRelationships(inspected.source,{module:'m'});expect(original.meaning.state).toBe('known');expect(original.meaning.relationships[0].id).toBe('self');expect(()=>metadata.inspectRelationships(inspected.target,{module:'m'})).toThrow()});
test('schema properties use explicit reversible target and preserve complete owner diagnostic observations',()=>{const before=JSON.stringify(inspected.target);const observation=metadata.inspectSchemaProperties(inspected.target,{scope:'element',module:'m',element:'label'});expect(observation.path).toBe('/modules/0/elements/1');expect(observation.source.umf).toBe('0.8.0');expect(observation.diagnostics).toEqual(inspected.targetValidation!.diagnostics);expect(observation.provenance).toBe('unverified');expect(JSON.stringify(inspected.target)).toBe(before)});

async function prepared(umf:'0.7.0'|'0.8.0'){const preparation=await createCatalogInputPreparation(recordDirectory!,'/Users/erik/Projects/umf/package.json');const input=structuredClone((await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input);const bytes=Buffer.from(umf==='0.7.0'?original:JSON.stringify(inspected.target));input.binding={state:'absent'};input.transforms=[];input.documents=[{documentId:'source',documentRevision:'r1',artifact:{identity:'source',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')},umfProfile:preparation.umfProfile,ingress:{kind:'native'}}];return preparation.prepare(new TextEncoder().encode(JSON.stringify(input)))}
test('prepared original sources collect owner observations with independent version basis and exact evidence',async()=>{const result=collectCatalogAssertionObservations(await prepared('0.7.0'),metadata);expect(result.observations.length).toBe(6);const relationship=result.observations.find(o=>o.operation==='relationships')!;expect((relationship.result as any).observation.meaning.state).toBe('known');expect(relationship.basis).toBe('original');const decoded=JSON.parse(Buffer.from(relationship.evidence.bytesBase64,'base64').toString());expect(decoded.operation).toBe('relationships');expect(decoded.result).toEqual(relationship.result);expect(Object.isFrozen(relationship.result)).toBe(true)});
test('unavailable original 0.8 relationship inspection remains explicit and preserves owner failure',async()=>{const result=collectCatalogAssertionObservations(await prepared('0.8.0'),metadata);const relationship=result.observations.find(o=>o.operation==='relationships')!;expect((relationship.result as any).state).toBe('unavailable');expect((relationship.result as any).code).toBe('RELATIONSHIP_RESULT');expect((relationship.result as any).path).toBe('');expect(result.observations.find(o=>o.operation==='schema_properties')!.basis).toBe('original');expect(result.scope).toBe('original_owner_assertion_observations_only')});

test('Field owner observations retain separate bundle evidence and original basis',async()=>{
 const directory=process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER;if(!directory)throw Error('Original Field assertion producer directory required');
 const {loadUmfFieldAssertionProducer}=await import('../packages/umf-bun/src/index');const fields=await loadUmfFieldAssertionProducer(directory);
 const result=collectCatalogAssertionObservations(await prepared('0.7.0'),metadata,fields);expect(result.observations.length).toBe(14);
 const field=result.observations.find(o=>o.operation==='nullability'&&(o.identity as any).element==='label')!;
 expect((field.result as any).observation.meaning).toEqual({state:'known',nullability:'required'});expect(field.basis).toBe('original');
 const evidence=JSON.parse(Buffer.from(field.evidence.bytesBase64,'base64').toString());expect(evidence.profile).toEqual(result.fieldProfile);expect(evidence.profile.sha256).toBe(fields.bundleSha256);
});

test('complete owner observation coverage detects omission, replacement and changed evidence',async()=>{
 const directory=process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER;if(!directory)throw Error('Field assertion producer required');
 const {loadUmfFieldAssertionProducer}=await import('../packages/umf-bun/src/index');const {assessCatalogObservationCoverage}=await import('../packages/umf-bun/src/catalog-observation-coverage');
 const input=await prepared('0.7.0'),fields=await loadUmfFieldAssertionProducer(directory),collection=collectCatalogAssertionObservations(input,metadata,fields);
 const coverage=assessCatalogObservationCoverage(input,collection);expect(coverage.observationsRequired).toBe('14');expect(coverage.availability).toBe('available');expect(coverage.unavailable).toEqual([]);
 expect(()=>assessCatalogObservationCoverage(input,{...collection,fieldProfile:null})).toThrow('Field observation bundle');
 expect(()=>assessCatalogObservationCoverage(input,{...collection,observations:collection.observations.slice(1)})).toThrow('inventory');
 const duplicate=[...collection.observations];duplicate[1]=duplicate[0];expect(()=>assessCatalogObservationCoverage(input,{...collection,observations:duplicate})).toThrow('identity/basis');
 const changed=[...collection.observations];changed[0]={...changed[0],evidence:{...changed[0].evidence,sha256:'0'.repeat(64)}};expect(()=>assessCatalogObservationCoverage(input,{...collection,observations:changed})).toThrow('evidence correspondence');
});
test('full observation occurrence coverage cannot turn unavailable 0.8 APIs into available meaning',async()=>{
 const directory=process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER;if(!directory)throw Error('Field assertion producer required');
 const {loadUmfFieldAssertionProducer}=await import('../packages/umf-bun/src/index');const {assessCatalogObservationCoverage}=await import('../packages/umf-bun/src/catalog-observation-coverage');
 const input=await prepared('0.8.0'),fields=await loadUmfFieldAssertionProducer(directory),collection=collectCatalogAssertionObservations(input,metadata,fields),coverage=assessCatalogObservationCoverage(input,collection);
 expect(coverage.observationsRequired).toBe('14');expect(coverage.availability).toBe('incomplete');expect(coverage.unavailable.some(o=>o.operation==='relationships'&&o.code==='RELATIONSHIP_RESULT')).toBe(true);expect(BigInt(coverage.observationsAvailable)).toBeLessThan(14n);expect(coverage.scope).toBe('original_owner_observation_correspondence_only');
});
