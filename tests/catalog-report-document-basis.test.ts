import {test,expect} from 'bun:test';
import {collectCatalogReportDocumentBasis} from '../packages/umf-bun/src/catalog-report-document-basis';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
const directory=process.env.TRUSS_UMF_PRODUCER;if(!directory)throw Error('Original producer required');
const preparation=await createCatalogInputPreparation(directory,'/Users/erik/Projects/umf/package.json');
const input=structuredClone((await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input);input.binding={state:'absent'};input.transforms=[];
const bytes=Buffer.from(JSON.stringify({umf:'0.7.0',id:'doc',vocabularies:{unknown:{version:'1.0.0'}},extensions:{unknown:{opaque:true}},modules:[]}));const digest=new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
input.documents=[{documentId:'doc',documentRevision:'r1',artifact:{identity:'doc',bytesBase64:bytes.toString('base64'),sha256:digest},umfProfile:preparation.umfProfile,ingress:{kind:'native'}}];
const original=preparation.prepare(new TextEncoder().encode(JSON.stringify(input)));function basis(){return original}
// Native result rows remain synthetic here; source preparation uses the actual pinned owner.
function rows(){return [{doc_id:'doc',doc_revision:'r1',content_sha256:digest,ord:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'}]}
test('document basis preserves partial original observation without making complete report',async()=>{const result=await collectCatalogReportDocumentBasis({unsafe:async()=>rows()},basis(),'1');expect(result.documents).toEqual(rows().map(({writer_xid,operation_ordinal,effect_generation,...document})=>document));expect(result.nativeObservation).toEqual({writerXid:'42',operationOrdinal:'0',effectGeneration:'11'});expect(JSON.parse(Buffer.from(result.observations[0].evidence.bytesBase64,'base64').toString()).observation.sourceValidation.complete).toBe(false);expect(result.scope).toBe('original_report_document_basis_only');expect(result.observations[0]).not.toHaveProperty('completeness')});
test('omitted and extra native archive observations refuse',async()=>{for(const native of [[],[...rows(),...rows()]])await expect(collectCatalogReportDocumentBasis({unsafe:async()=>native},basis(),'1')).rejects.toThrow('bijection')});
test('native identity revision digest and ordinal substitutions refuse',async()=>{for(const [field,value] of [['doc_id','other'],['doc_revision','r2'],['content_sha256','c'.repeat(64)],['ord','00']]){const native=rows();(native[0] as any)[field]=value;await expect(collectCatalogReportDocumentBasis({unsafe:async()=>native},basis(),'1')).rejects.toThrow('correspondence')}});

test('missing or noncanonical native generation cannot be guessed',async()=>{for(const value of [undefined,'00','-1','9223372036854775808']){const native=rows();(native[0] as any).effect_generation=value;await expect(collectCatalogReportDocumentBasis({unsafe:async()=>native},basis(),'1')).rejects.toThrow('observation tuple')}});
