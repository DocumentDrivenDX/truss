import {test,expect} from 'bun:test';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {createAcceptanceProfileResolver} from '../packages/umf-bun/src/acceptance-profiles';
import {prepareDefaultCatalogHomes} from '../packages/umf-bun/src/catalog-default-homes';
const directory=process.env.TRUSS_UMF_PRODUCER;if(!directory)throw Error('Original Record producer directory required');
const preparation=await createCatalogInputPreparation(directory,'/Users/erik/Projects/umf/package.json');
const fixture=await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json();
function request(){const input=structuredClone(fixture.input);input.binding={state:'absent'};input.transforms=[];
 input.documents=['first-doc','second-doc'].map(documentId=>{const original=' \n'+JSON.stringify({umf:'0.7.0',id:documentId,vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[{id:'Item',kind:'record',members:[{module:'m',element:'label'}],extensions:{}},{id:'label',kind:'field',scalarType:'string',nullability:'required',cardinality:'one',extensions:{}}]}]})+'\n';const bytes=Buffer.from(original);return {documentId,documentRevision:'original-r1',artifact:{identity:documentId,bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')},umfProfile:preparation.umfProfile,ingress:{kind:'native'}}});return input}
const run=(input:unknown)=>preparation.prepare(new TextEncoder().encode(JSON.stringify(input)));
test('real owner validates original ordered UMF sources with reversible interpretation',()=>{const input=request();const result=run(input);expect(result.documents.map(d=>d.documentId)).toEqual(['first-doc','second-doc']);for(let i=0;i<2;i++){const doc=result.documents[i]!;expect(doc.originalText).toBe(Buffer.from(input.documents[i].artifact.bytesBase64,'base64').toString());expect(doc.umfVersion).toBe('0.7.0');expect(doc.interpretation.target.umf).toBe('0.8.0');expect(doc.validation.sourceValidation.valid).toBe(true);expect(doc.validation.transition).not.toBeNull()}expect(result.scope).toBe('original_umf_preparation_only')});
test('foreign original interpretation profile cannot borrow validation',()=>{const input=request();input.documents[0].umfProfile={...preparation.umfProfile,sha256:'0'.repeat(64)};expect(()=>run(input)).toThrow('Unsupported original UMF profile')});
test('archive document identity must equal original owner source',()=>{const input=request();input.documents[0].documentId='other';expect(()=>run(input)).toThrow('Original document identity mismatch')});
test('shape-only original {} source does not become accepted UMF',()=>{const input=request();const bytes=Buffer.from('{}');input.documents[0].artifact={identity:'invalid',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')};expect(()=>run(input)).toThrow()});

test('native archive carrier has exact five original fields without interpretation substitution',()=>{const result=run(request());expect(Object.keys(result.archiveDocuments[0]).sort()).toEqual(['documentId','originalText','revision','umfVersion','validation']);expect(Object.isFrozen(result.archiveDocuments[0].validation)).toBe(true)});

test('source declaration extraction preserves original owner and Field references',()=>{const result=run(request());expect(result.declarations.map(d=>d.records[0].documentId)).toEqual(['first-doc','second-doc']);const record=result.declarations[0].records[0];expect([record.moduleId,record.elementId]).toEqual(['m','Item']);expect(record.fields[0].declaration).toBe(result.documents[0].interpretation.source.modules[0].elements[1]);expect(record.fields[0].reference).toEqual({module:'m',element:'label'});expect(Object.isFrozen(record.fields[0].declaration)).toBe(true)});

test('configured original registry refuses unregistered synthetic root profiles',async()=>{const guarded=await createCatalogInputPreparation(directory!,'/Users/erik/Projects/umf/package.json',createAcceptanceProfileResolver([]));expect(()=>guarded.prepare(new TextEncoder().encode(JSON.stringify(request())))).toThrow('/layoutProfile')});

test('absent binding derives complete default json homes from original members',()=>{const result=run(request());const defaults=prepareDefaultCatalogHomes(result);expect(defaults.homes).toEqual(['first-doc','second-doc'].map(documentId=>({documentId,moduleId:'m',elementId:'Item',fieldModule:'m',fieldId:'label',home:'json'})));expect(defaults.originalInputSha256).toBe(new Bun.CryptoHasher('sha256').update(Buffer.from(result.original.originalUtf8Hex,'hex')).digest('hex'));expect(Object.isFrozen(defaults.homes[0])).toBe(true)});
test('present binding cannot be silently replaced with default homes',()=>{const input=request();input.binding=structuredClone(fixture.input.binding);expect(()=>prepareDefaultCatalogHomes(run(input))).toThrow('Original explicit binding home interpretation required')});

test('embedded duplicate source members refuse before owner interpretation',()=>{
 const input=request();const text=Buffer.from(input.documents[0].artifact.bytesBase64,'base64').toString().replace('"id":"first-doc"','"id":"discarded","id":"first-doc"');const bytes=Buffer.from(text);
 input.documents[0].artifact={identity:'duplicate-source',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')};
 expect(()=>run(input)).toThrow('duplicate_member');
});

test('reconstructed preparations cannot enter home, extension, report or native staging helpers',async()=>{
 const {collectCatalogExtensionInventory}=await import('../packages/umf-bun/src/catalog-extension-inventory');
 const {collectCatalogReportDocumentBasis}=await import('../packages/umf-bun/src/catalog-report-document-basis');
 const {stageNewCatalogCohort}=await import('../packages/umf-bun/src/catalog-new-stage');
 const original=run(request()),clone=structuredClone(original);let calls=0;const connection={unsafe:async()=>{calls++;return []}};
 expect(()=>prepareDefaultCatalogHomes(clone)).toThrow('validated catalog preparation');
 expect(()=>collectCatalogExtensionInventory(clone)).toThrow('validated catalog preparation');
 await expect(collectCatalogReportDocumentBasis(connection,clone,'1')).rejects.toThrow('validated catalog preparation');
 await expect(stageNewCatalogCohort(connection,clone,[],{})).rejects.toThrow('validated catalog preparation');
 expect(calls).toBe(0);expect(prepareDefaultCatalogHomes(original).homes.length).toBe(2);
});

test('new-only staging cannot silently ignore declared transforms',async()=>{
 const {stageNewCatalogCohort}=await import('../packages/umf-bun/src/catalog-new-stage');const input=request();input.transforms=structuredClone(fixture.input.transforms);const original=run(input);let calls=0;
 await expect(stageNewCatalogCohort({unsafe:async()=>{calls++;return []}},original,prepareDefaultCatalogHomes(original).homes,{})).rejects.toThrow('Complete transform execution');expect(calls).toBe(0);
});
