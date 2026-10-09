import {test,expect} from 'bun:test';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {loadUmfDeclarationProducer,loadUmfFieldAssertionProducer} from '../packages/umf-bun/src/index';
import {collectCatalogReportPreparation} from '../packages/umf-bun/src/catalog-report-preparation';
const recordDir=process.env.TRUSS_UMF_PRODUCER,ownerDir=process.env.TRUSS_UMF_DECLARATION_PRODUCER,fieldDir=process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER;if(!recordDir||!ownerDir||!fieldDir)throw Error('All original owner directories required');
const preparation=await createCatalogInputPreparation(recordDir,'/Users/erik/Projects/umf/package.json'),owner=await loadUmfDeclarationProducer(ownerDir),fields=await loadUmfFieldAssertionProducer(fieldDir);
const input=structuredClone((await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input);input.binding={state:'absent'};input.transforms=[];
const bytes=Buffer.from(JSON.stringify({umf:'0.7.0',id:'doc',vocabularies:{unknown:{version:'1.0.0'}},extensions:{unknown:{opaque:true}},modules:[]}));const digest=new Bun.CryptoHasher('sha256').update(bytes).digest('hex');input.documents=[{documentId:'doc',documentRevision:'r1',artifact:{identity:'doc',bytesBase64:bytes.toString('base64'),sha256:digest},umfProfile:preparation.umfProfile,ingress:{kind:'native'}}];const prepared=preparation.prepare(new TextEncoder().encode(JSON.stringify(input)));
const countRow=()=>({types_added:'0',properties_added:'0',keys_added:'0',relationships_added:'0',endpoints_added:'0',elements_retired:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'});
function connection(rows:Record<string,string>[]=[countRow()]){const queries:string[]=[];return {queries,unsafe:async(query:string)=>{queries.push(query);if(query.includes('runtime_collect_report_documents'))return [{doc_id:'doc',doc_revision:'r1',content_sha256:digest,ord:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'}];if(query.includes('runtime_collect_new_catalog_counts'))return rows;return []}}}
// Native results are synthetic; actual server composition is qualified in the cohort harness.
test('composition preserves original partial interpretation and extensions without accepted claim',async()=>{
 const native=connection(),result=await collectCatalogReportPreparation(native,prepared,'1',owner,fields);expect(result.counts.typesAdded).toBe('0');expect(result.observationCoverage.availability).toBe('available');expect(result.extensions.entries.length).toBe(1);expect(prepared.documents[0].interpretation.sourceValidation.complete).toBe(false);expect(result.scope).toBe('original_new_catalog_report_preparation_only');expect(native.queries.at(-1)).toContain('runtime_require_catalog_observation');expect(Object.isFrozen(result.counts)).toBe(true);
});
test('mixed native observation tuple and missing/extra count rows refuse',async()=>{
 for(const rows of [[],[countRow(),countRow()],[{...countRow(),effect_generation:'12'}],[{...countRow(),writer_xid:'43'}]])await expect(collectCatalogReportPreparation(connection(rows),prepared,'1',owner,fields)).rejects.toThrow();
});
test('count grammar bounds columns and new-only retirement are explicit',async()=>{
 for(const row of [{...countRow(),types_added:'00'},{...countRow(),types_added:'16385'},{...countRow(),elements_retired:'1'},{...countRow(),extra:'0'}])await expect(collectCatalogReportPreparation(connection([row]),prepared,'1',owner,fields)).rejects.toThrow();
});
test('forged preparation refuses before issuing native reads',async()=>{
 const native=connection();await expect(collectCatalogReportPreparation(native,structuredClone(prepared),'1',owner,fields)).rejects.toThrow('validated catalog preparation');expect(native.queries).toEqual([]);
});


test('composed validation evidence preserves diagnostics at both source and reversible target bases',async()=>{
 const result=await collectCatalogReportPreparation(connection(),prepared,'1',owner,fields),evidence=result.validationEvidence;
 expect(evidence.documentInterpretations.length).toBe(1);expect(evidence.documentInterpretations[0].completeness).toBe('partial');expect(evidence.documentInterpretations[0].contentSha256).toBe(digest);
 const decoded=evidence.diagnostics.map(entry=>JSON.parse(Buffer.from(entry.diagnostic.bytesBase64,'base64').toString()));
 for(const [basis,validation] of [['original',prepared.documents[0].interpretation.sourceValidation],['reversible_target',prepared.documents[0].interpretation.targetValidation]] as const)expect(decoded.filter(e=>e.basis===basis).map(e=>e.diagnostic)).toEqual(validation!.diagnostics);
 for(const entry of evidence.diagnostics){expect(entry.source.artifact).toBe(prepared.original.input.documents[0].artifact);expect(entry.source.sourcePointer).toBe('');expect(entry.classification).toBe('upstream_validation');expect(entry.diagnostic.sha256).toBe(new Bun.CryptoHasher('sha256').update(Buffer.from(entry.diagnostic.bytesBase64,'base64')).digest('hex'))}
 expect(evidence.profile.sha256).toBe(new Bun.CryptoHasher('sha256').update(Buffer.from(evidence.manifest.bytesBase64,'base64')).digest('hex'));
 expect(evidence.documentInterpretations[0].evidence).toEqual(result.documentBasis.observations[0].evidence);
});

test('original 0.8 validation does not invent a transition or duplicate a target-basis diagnostic scan',async()=>{
 const {collectCatalogValidationEvidence}=await import('../packages/umf-bun/src/catalog-validation-evidence');const originalInput=structuredClone(input),bytes=Buffer.from(JSON.stringify(prepared.documents[0].interpretation.target));
 originalInput.documents[0].artifact={identity:'original-08',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')};const source=preparation.prepare(new TextEncoder().encode(JSON.stringify(originalInput))),result=collectCatalogValidationEvidence(source);
 expect(source.documents[0].interpretation.transition).toBeNull();expect(result.diagnostics.map(entry=>JSON.parse(Buffer.from(entry.diagnostic.bytesBase64,'base64').toString()).basis).every(b=>b==='original')).toBe(true);expect(result.diagnostics.length).toBe(source.documents[0].interpretation.sourceValidation.diagnostics.length);expect(result.documentInterpretations[0].completeness).toBe('partial');
});
