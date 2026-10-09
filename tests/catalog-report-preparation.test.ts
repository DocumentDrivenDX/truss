import {test,expect} from 'bun:test';
import {collectCatalogExtensionArtifacts} from '../packages/umf-bun/src/catalog-extension-artifacts';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {loadUmfDeclarationProducer,loadUmfFieldAssertionProducer} from '../packages/umf-bun/src/index';
import {collectCatalogReportPreparation} from '../packages/umf-bun/src/catalog-report-preparation';
import {createCatalogReportCorrespondence} from '../packages/umf-bun/src/catalog-report-correspondence';
import {createAcceptanceProfileResolver} from '../packages/umf-bun/src/acceptance-profiles';
import {collectCatalogOriginalExecutionBasis} from '../packages/umf-bun/src/catalog-original-execution-basis';
const recordDir=process.env.TRUSS_UMF_PRODUCER,ownerDir=process.env.TRUSS_UMF_DECLARATION_PRODUCER,fieldDir=process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER;if(!recordDir||!ownerDir||!fieldDir)throw Error('All original owner directories required');
const preparation=await createCatalogInputPreparation(recordDir,'/Users/erik/Projects/umf/package.json'),owner=await loadUmfDeclarationProducer(ownerDir),fields=await loadUmfFieldAssertionProducer(fieldDir);
const input=structuredClone((await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input);input.binding={state:'absent'};input.transforms=[];
const bytes=Buffer.from(JSON.stringify({umf:'0.7.0',id:'doc',vocabularies:{unknown:{version:'1.0.0'}},extensions:{unknown:{opaque:true}},modules:[]}));const digest=new Bun.CryptoHasher('sha256').update(bytes).digest('hex');input.documents=[{documentId:'doc',documentRevision:'r1',artifact:{identity:'doc',bytesBase64:bytes.toString('base64'),sha256:digest},umfProfile:preparation.umfProfile,ingress:{kind:'native'}}];const prepared=preparation.prepare(new TextEncoder().encode(JSON.stringify(input)));
const countRow=()=>({types_added:'0',properties_added:'0',keys_added:'0',relationships_added:'0',endpoints_added:'0',elements_retired:'0',provisional_count:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'});
function connection(rows:Record<string,string>[]=[countRow()]){const queries:string[]=[];return {queries,unsafe:async(query:string)=>{queries.push(query);if(query.includes('runtime_collect_report_documents'))return [{doc_id:'doc',doc_revision:'r1',content_sha256:digest,ord:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'}];if(query.includes('runtime_collect_new_catalog_counts'))return rows;return []}}}
// Native results are synthetic; actual server composition is qualified in the cohort harness.
test('composition preserves original partial interpretation and extensions without accepted claim',async()=>{
 const native=connection(),result=await collectCatalogReportPreparation(native,prepared,'1',owner,fields);expect(result.counts.typesAdded).toBe('0');expect(result.observationCoverage.availability).toBe('available');expect(result.extensions.entries.length).toBe(1);expect(prepared.documents[0].interpretation.sourceValidation.complete).toBe(false);expect(result.scope).toBe('original_new_catalog_report_preparation_only');expect(native.queries.at(-1)).toContain('runtime_require_catalog_observation');expect(Object.isFrozen(result.counts)).toBe(true);
});
test('mixed native observation tuple and missing/extra count rows refuse',async()=>{
 for(const rows of [[],[countRow(),countRow()],[{...countRow(),effect_generation:'12'}],[{...countRow(),writer_xid:'43'}]])await expect(collectCatalogReportPreparation(connection(rows),prepared,'1',owner,fields)).rejects.toThrow();
});
test('count grammar bounds columns and new-only retirement are explicit',async()=>{
 for(const row of [{...countRow(),types_added:'00'},{...countRow(),types_added:'16385'},{...countRow(),elements_retired:'1'},{...countRow(),extra:'0'},{...countRow(),provisional_count:'1'}])await expect(collectCatalogReportPreparation(connection([row]),prepared,'1',owner,fields)).rejects.toThrow();
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
 expect(result.coreAssertionIdentities.complete).toBe(false);expect(result.coreAssertionIdentities.deferred.length).toBeGreaterThan(0);
});

test('original 0.8 validation does not invent a transition or duplicate a target-basis diagnostic scan',async()=>{
 const {collectCatalogValidationEvidence}=await import('../packages/umf-bun/src/catalog-validation-evidence');const originalInput=structuredClone(input),bytes=Buffer.from(JSON.stringify(prepared.documents[0].interpretation.target));
 originalInput.documents[0].artifact={identity:'original-08',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')};const source=preparation.prepare(new TextEncoder().encode(JSON.stringify(originalInput))),result=collectCatalogValidationEvidence(source);
 expect(source.documents[0].interpretation.transition).toBeNull();expect(result.diagnostics.map(entry=>JSON.parse(Buffer.from(entry.diagnostic.bytesBase64,'base64').toString()).basis).every(b=>b==='original')).toBe(true);expect(result.diagnostics.length).toBe(source.documents[0].interpretation.sourceValidation.diagnostics.length);expect(result.documentInterpretations[0].completeness).toBe('partial');
});

test('new-only report preparation cannot ignore a declared transform registration',async()=>{
 const declared=structuredClone(input);declared.transforms=structuredClone((await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input.transforms);const original=preparation.prepare(new TextEncoder().encode(JSON.stringify(declared))),native=connection();
 await expect(collectCatalogReportPreparation(native,original,'1',owner,fields)).rejects.toThrow('Complete transform execution');expect(native.queries).toEqual([]);
});
const correspondence=await createCatalogReportCorrespondence('/Users/erik/Projects/umf/package.json');
const untrustedReport=(await Bun.file('docs/helix/03-test/report-wire-untrusted.fixture.json').json()).report;
function reportFor(basis:Awaited<ReturnType<typeof collectCatalogReportPreparation>>){return {...structuredClone(untrustedReport),rev:basis.provisionalRevision,acceptedInput:prepared.original.input,documents:basis.documentBasis.documents,counts:basis.counts,provisional:basis.provisional,diagnostics:basis.validationEvidence.diagnostics,documentInterpretations:basis.validationEvidence.documentInterpretations,extensions:collectCatalogExtensionArtifacts(prepared).extensions}}
const wire=(value:unknown)=>new TextEncoder().encode(JSON.stringify(value));
test('report profile binds original registered bytes and refuses substitution before native observation',async()=>{
 const basis=await collectCatalogReportPreparation(connection(),prepared,'1',owner,fields);
 const bytes=wire({purpose:'test byte custody, no semantic authority'});
 const pin={identity:'registered-report',version:'0.1.0',sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')};
 const resolver=createAcceptanceProfileResolver([{role:'report',profile:pin,artifactIdentity:'original-report-profile',bytes}]);
 const report={...reportFor(basis),reportProfile:pin},native=connection();
 const result=await correspondence.verifyWithRegisteredReportProfile(native,prepared,basis,wire(report),resolver,pin);
 expect(result.scope).toBe('ten_producer_fields_and_registered_report_bytes_only');
 expect(result.verifiedFields).toContain('reportProfile');
 expect(result.registeredReportArtifact.sha256).toBe(pin.sha256);
 for(const supplied of [{...pin,identity:'substituted'},{...pin,version:'another'},{...pin,sha256:'0'.repeat(64)}]){
  native.queries.length=0;
  await expect(correspondence.verifyWithRegisteredReportProfile(native,prepared,basis,wire({...report,reportProfile:supplied}),resolver,pin)).rejects.toThrow('profile correspondence');
  expect(native.queries).toEqual([]);
 }
 native.queries.length=0;
 await expect(correspondence.verifyWithRegisteredReportProfile(native,prepared,basis,new Uint8Array(),{...resolver},pin)).rejects.toThrow('byte-custody resolver');
 await expect(correspondence.verifyWithRegisteredReportProfile(native,prepared,basis,new Uint8Array(),createAcceptanceProfileResolver([]),pin)).rejects.toThrow('report profile unavailable');
 expect(native.queries).toEqual([]);
});

test('combined report check refuses unissued execution custody before profile resolution or native I/O',async()=>{
 const native=connection(),basis=await collectCatalogReportPreparation(native,prepared,'1',owner,fields);
 native.queries.length=0;
 await expect(correspondence.verifyWithExecutionAndRegisteredReportProfile(native,prepared,basis,new Uint8Array(),{candidate:untrustedReport.originalExecution} as any,createAcceptanceProfileResolver([]),untrustedReport.reportProfile)).rejects.toThrow('candidate custody');
 expect(native.queries).toEqual([]);
});
test('complete wire corresponds to ten issued producer fields while other fixture fields remain untrusted',async()=>{
 const native=connection(),basis=await collectCatalogReportPreparation(native,prepared,'1',owner,fields);
 const result=await correspondence.verify(native,prepared,basis,wire(reportFor(basis)));
 expect(result.verifiedFields.length).toBe(10);expect(result.scope).toBe('ten_original_report_producer_fields_only');expect(native.queries.at(-1)).toContain('runtime_require_catalog_observation');
});
test('native ingress absence does not admit injected loss or transform registration',async()=>{
 const basis=await collectCatalogReportPreparation(connection(),prepared,'1',owner,fields);
 expect(basis.ingressBasis.originalIngress[0].contentSha256).toBe(digest);
 for(const extra of [{losses:[{source:input.documents[0].artifact,sourcePointer:"",lossProfile:input.layoutProfile,loss:input.documents[0].artifact}]},{transformRegistrations:[{registration:input.layoutProfile,manifest:input.documents[0].artifact,originalImplementationRecognition:input.documents[0].artifact}]}]){
  const native=connection();await expect(correspondence.verify(native,prepared,basis,wire({...reportFor(basis),...extra}))).rejects.toThrow('producer correspondence');expect(native.queries).toEqual([]);
 }
 const declared=structuredClone(input);declared.binding=structuredClone((await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input.binding);
 const original=preparation.prepare(wire(declared)),native=connection();await expect(collectCatalogReportPreparation(native,original,'1',owner,fields)).rejects.toThrow('binding effect interpretation');expect(native.queries).toEqual([]);
});
test('changed source effect and diagnostic fields refuse before native recheck',async()=>{
 const basis=await collectCatalogReportPreparation(connection(),prepared,'1',owner,fields);
 for(const field of ['rev','acceptedInput','documents','counts','diagnostics','documentInterpretations']){
  const report=structuredClone(reportFor(basis));
  if(field==='rev')report.rev='2';if(field==='acceptedInput')report.acceptedInput.layoutProfile.identity='forged';
  if(field==='documents')report.documents[0].doc_revision='forged';if(field==='counts')report.counts.typesAdded='1';
  if(field==='diagnostics')report.diagnostics[0].diagnostic.identity='forged';
  if(field==='documentInterpretations')report.documentInterpretations[0].completeness='complete';
  const native=connection();await expect(correspondence.verify(native,prepared,basis,wire(report))).rejects.toThrow('producer correspondence');expect(native.queries).toEqual([]);
 }
});
test('copied report basis and stale native cut cannot supply correspondence',async()=>{
 const basis=await collectCatalogReportPreparation(connection(),prepared,'1',owner,fields),native=connection();
 await expect(correspondence.verify(native,prepared,{...basis},wire(reportFor(basis)))).rejects.toThrow('bound catalog report preparation');expect(native.queries).toEqual([]);
 await expect(correspondence.verify({unsafe:async()=>{throw Error('stale original cut')}},prepared,basis,wire(reportFor(basis)))).rejects.toThrow('stale original cut');
});
test('native actor basis retains original bytes and rejects inconsistent result carriers',async()=>{
 const basis=await collectCatalogReportPreparation(connection(),prepared,'1',owner,fields);
 const context=' {"interfaceVersion":"truss-native-operation-context/0.2","xid":"42","ordinal":"0","actingUser":"actor","sessionUser":"login","database":"db","backendPid":"7","actorRoleOid":"10","sessionRoleOid":"11"} ';
 const row={context_hex:Buffer.from(context).toString('hex'),database_role:'actor',login_role:'login',database_name:'db',backend_pid:'7',actor_role_oid:'10',login_role_oid:'11'};
 const native=(rows:Record<string,string>[])=>({unsafe:async(query:string)=>query.includes('runtime_collect_catalog_original_context')?rows:[]});
 const result=await collectCatalogOriginalExecutionBasis(native([row]),prepared,basis);
 expect(Buffer.from(result.contextEvidence.bytesBase64,'base64').toString()).toBe(context);expect(result.databaseRole).toBe('actor');expect(result.scope).toBe('original_native_actor_context_basis_only');
 for(const rows of [[],[row,row],[{...row,extra:'x'}],[{...row,database_role:'forged'}],[{...row,context_hex:'7b7d'}],[{...row,context_hex:'AB'}],[{...row,actor_role_oid:'12'}]])await expect(collectCatalogOriginalExecutionBasis(native(rows),prepared,basis)).rejects.toThrow();
 await expect(collectCatalogOriginalExecutionBasis(native([row]),prepared,{...basis})).rejects.toThrow('bound catalog report preparation');
});


test('report correspondence refuses omitted, duplicated or substituted original extension artifacts',async()=>{
 const correspondence=await createCatalogReportCorrespondence('/Users/erik/Projects/umf/package.json');
 const native=connection(),basis=await collectCatalogReportPreparation(native,prepared,'1',owner,fields);
 for(const extensions of [[],[...collectCatalogExtensionArtifacts(prepared).extensions,...collectCatalogExtensionArtifacts(prepared).extensions],[{...collectCatalogExtensionArtifacts(prepared).extensions[0],identity:'substituted'}]]){
  const report={...reportFor(basis),extensions};
  await expect(correspondence.verify(native,prepared,basis,wire(report))).rejects.toThrow('producer correspondence required: extensions');
 }
});


test('execution report comparison refuses copied/unissued candidate before parsing or native I/O',async()=>{
 const native=connection(),basis=await collectCatalogReportPreparation(native,prepared,'1',owner,fields);
 native.queries.length=0;
 await expect(correspondence.verifyWithExecutionCandidate(native,prepared,basis,new Uint8Array(),{candidate:untrustedReport.originalExecution} as any)).rejects.toThrow('candidate custody');
 expect(native.queries).toEqual([]);
});
