import {test,expect} from 'bun:test';
import {mkdtemp,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {collectCatalogTypeReceipts,requireOriginalCatalogTypeReceipts} from '../packages/umf-bun/src/catalog-type-receipts';
import {collectCatalogReportPreparation} from '../packages/umf-bun/src/catalog-report-preparation';
import {parseOriginalReceiptJson} from '../packages/umf-bun/src/catalog-receipt-json';
import {loadUmfDeclarationProducer,loadUmfFieldAssertionProducer,loadUmfRecordTypeReceiptProducer} from '../packages/umf-bun/src/index';
const preparation=await createCatalogInputPreparation(process.env.TRUSS_UMF_PRODUCER!,'/Users/erik/Projects/umf/package.json'),directory=process.env.TRUSS_UMF_RECORD_TYPE_RECEIPT_PRODUCER!;
const owner=await loadUmfRecordTypeReceiptProducer(directory),author=await import(resolve(directory,'producer.js'));
const declarations=await loadUmfDeclarationProducer(process.env.TRUSS_UMF_DECLARATION_PRODUCER!),fields=await loadUmfFieldAssertionProducer(process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER!);
const fixture=(await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input;
const hash=(b:Uint8Array|string)=>new Bun.CryptoHasher('sha256').update(b).digest('hex');
function setup(){
 const source={umf:'0.7.0',id:'doc',vocabularies:{},modules:[{id:'m',namespace:'m',elements:[{id:'v',name:'v',kind:'field',cardinality:'one',extensions:{},'future/value':{values:['b','a'],decimal:0.1},references:[{role:'future-role',module:'m',element:'R','future/qualifier':{values:['b','a']}}]},{id:'R',kind:'record',members:[],extensions:{}},{id:'Owner',kind:'record',members:[{module:'m',element:'v'}],extensions:{}}]},{id:'other',namespace:'other',elements:[{id:'R',kind:'record',members:[],extensions:{}},{id:'v',kind:'field',extensions:{}}]}]};
 const identity={module:'m',element:'v'},field=author.declareCoreElementKind(source,identity,'field'),record=author.declareCoreElementKind(field.target,{module:'other',element:'R'},'record'),receipt=author.declareCoreRecordType(field,record);
 const sourceBytes=Buffer.from(' \n'+JSON.stringify(receipt.target)+'\n'),input=structuredClone(fixture);input.binding={state:'absent'};input.transforms=[];input.documents=[{documentId:'doc',documentRevision:'r1',umfProfile:preparation.umfProfile,ingress:{kind:'native'},artifact:{identity:'original-doc',bytesBase64:sourceBytes.toString('base64'),sha256:hash(sourceBytes)}}];
 const prepared=preparation.prepare(Buffer.from(JSON.stringify(input))),bytes=Buffer.from(' \n'+JSON.stringify(receipt)+'\n'),artifact={identity:'original-type-receipt',bytesBase64:bytes.toString('base64'),sha256:hash(bytes)};
 const requests={version:'0.1.0',receipts:[{documentId:'doc',documentRevision:'r1',field:identity,artifact}]};
 return {prepared,input,receipt,requests,wire:Buffer.from(' \n'+JSON.stringify(requests)+'\n'),bytes};
}
const packet=(requests:unknown)=>Buffer.from(JSON.stringify(requests));
test('original receipt bytes qualified current document and appended occurrence stay distinct from authority',()=>{
 const s=setup(),c=collectCatalogTypeReceipts(s.prepared,owner,s.wire),entry=c.entries[0]!;
 expect(c.entries.length).toBe(1);expect(c.ownerProfile.version).toBe('ec3fae2bdb93bdbaff30c38ee370030da7db1760');expect(c.ownerProfile.sha256).toBe(owner.bundleSha256);expect(c.requestArtifact.bytesBase64).toBe(s.wire.toString('base64'));expect(c.requestArtifact.sha256).toBe(hash(s.wire));
 expect(entry.receiptArtifact).toEqual(s.requests.receipts[0]!.artifact);expect(entry.receiptArtifact.bytesBase64).toBe(s.bytes.toString('base64'));expect(entry.source).toBe(s.prepared.original.input.documents[0]!.artifact);expect(entry.documentRevision).toBe('r1');expect(entry.sourcePointer).toBe('/modules/0/elements/0/references/1');expect(Buffer.from(entry.originalReferenceBytesBase64,'base64').toString()).toBe(JSON.stringify({role:'record-type',module:'other',element:'R'}));
 expect(entry.ownerMeaning).toMatchObject({receipt:s.receipt,receiptConsistency:'verified',issuerAuthority:'unverified',enforcement:'none',link:{index:1,target:{identity:{module:'other',element:'R'},path:'/modules/1/elements/0',kind:'record'},typeAssertion:'unverified'}});
 expect(entry.ownerProfile).toBe(c.ownerProfile);expect(entry.issuerAuthority).toBe('unverified');expect(entry.enforcement).toBe('none');expect(entry.interpretationQualified).toBe(false);expect(c.complete).toBe(false);
 const retained=JSON.parse(Buffer.from(entry.ownerEvidence.bytesBase64,'base64').toString());expect(retained.originalSourceSha256).toBe(entry.source.sha256);expect(retained.receiptArtifact).toEqual(entry.receiptArtifact);expect(retained.result).toEqual(entry.ownerMeaning);expect(entry.ownerEvidence.sha256).toBe(hash(Buffer.from(entry.ownerEvidence.bytesBase64,'base64')));
 s.wire.fill(0);s.bytes.fill(0);s.requests.receipts[0]!.artifact.identity='changed';expect(entry.receiptArtifact.identity).toBe('original-type-receipt');expect(()=>((entry.ownerMeaning as any).receipt.source.modules[0].elements[0]['future/value'].values.reverse())).toThrow();expect(()=>((entry as any).receiptArtifact.identity='changed')).toThrow();
});
test('whole packet refuses missing wrong crossed duplicate and stale receipts without partial collections',()=>{
 const s=setup();expect(()=>collectCatalogTypeReceipts(s.prepared,{...owner},s.wire)).toThrow('loaded assertion owner');
 const empty=collectCatalogTypeReceipts(s.prepared,owner,packet({version:'0.1.0',receipts:[]}));expect(empty.entries).toEqual([]);expect(empty.complete).toBe(false);
 for(const mutation of [
  (r:any)=>{r.extra=true},(r:any)=>{r.version='future'},(r:any)=>{delete r.receipts[0].artifact},(r:any)=>{r.receipts[0].field.element='absent'},(r:any)=>{r.receipts[0].field.module='other'},(r:any)=>{r.receipts[0].documentId='other'},(r:any)=>{r.receipts[0].documentRevision='r2'},(r:any)=>{r.receipts[0].artifact.sha256='0'.repeat(64)},(r:any)=>{r.receipts[0].artifact.bytesBase64+='='},(r:any)=>{r.receipts.push(structuredClone(r.receipts[0]))},(r:any)=>{r.receipts=Array(65).fill(r.receipts[0])},
 ]){const changed=structuredClone(s.requests);mutation(changed);expect(()=>collectCatalogTypeReceipts(s.prepared,owner,packet(changed))).toThrow()}
 for(const mutate of [(r:any)=>{r.target.id='changed'},(r:any)=>{r.source.modules[0].elements[0]['future/value'].values.reverse()},(r:any)=>{r.fieldAuthor.source.id='crossed'},(r:any)=>{r.provenance.idealPath='/modules/0/elements/0/references/0'},(r:any)=>{r.signature='authenticated'}]){
  const r=structuredClone(s.receipt);mutate(r);const bytes=packet(r),requests=structuredClone(s.requests);requests.receipts[0]!.artifact={identity:'changed-receipt',bytesBase64:bytes.toString('base64'),sha256:hash(bytes)};expect(()=>collectCatalogTypeReceipts(s.prepared,owner,packet(requests))).toThrow();
 }
 const raw=Buffer.from(s.bytes.toString().replace('"operation":','"operation":"forged","operation":')),requests=structuredClone(s.requests);requests.receipts[0]!.artifact={identity:'duplicate-json',bytesBase64:raw.toString('base64'),sha256:hash(raw)};expect(()=>collectCatalogTypeReceipts(s.prepared,owner,packet(requests))).toThrow('duplicate_member');
 expect(()=>collectCatalogTypeReceipts(s.prepared,owner,new Uint8Array(new SharedArrayBuffer(s.wire.length)))).toThrow('carrier');expect(()=>collectCatalogTypeReceipts(s.prepared,owner,new Uint8Array(1048577))).toThrow('resource');
});
test('receipt numeric parsing preserves supported decimal meaning and refuses silent Number loss',()=>{
 for(const raw of ['0.1','1e-1','1.000','0e999999999999999999999999999999999999999999999999999999999999999999999999999','123.45','1.25e+2'])expect(parseOriginalReceiptJson(Buffer.from('{"n":'+raw+'}'))).toEqual({n:Number(raw)});
 for(const raw of ['1e-500','1e500','0.10000000000000001','9007199254740993','-0'])expect(()=>parseOriginalReceiptJson(Buffer.from('{"n":'+raw+'}'))).toThrow('numeric meaning');
 expect(()=>parseOriginalReceiptJson(Buffer.from('{"n":1,"n":1}'))).toThrow('duplicate_member');
});
test('loaded owner result substitutions refuse before interpretation or report use',async()=>{
 const mutations=["r.source.id='changed'","r.identity.module='other'","r.receipt.source.id='changed'","r.path='/modules/0/elements/0/references/0'","r.recordPath='/modules/0/elements/1'","r.link.index=0","r.link.reference.role='future-role'","r.link.target.identity.module='m'","r.link.target.kind='field'","r.receiptConsistency='unverified'","r.issuerAuthority='authenticated'","r.enforcement='database'","r.link.typeAssertion='verified'","r.extraAuthority=true","r.source.modules[0].elements[0].references.reverse()","r.receipt.source.modules[0].elements[0]['future/value'].values.reverse()","Object.defineProperty(r,'source',{enumerable:true,get(){throw Error('getter was invoked')}})","r=Object.fromEntries(Object.entries(r).reverse())"];
 for(const mutation of mutations){const s=setup(),temp=await mkdtemp(join(tmpdir(),'truss-type-owner-control-'));
  try{const script=`import * as base from ${JSON.stringify(resolve(directory,'producer.js'))};\nexport function inspectCoreRecordTypeReceipt(...args){let r=base.inspectCoreRecordTypeReceipt(...args);${mutation};return r}\n`;await writeFile(join(temp,'producer.js'),script);await writeFile(join(temp,'producer-manifest.json'),JSON.stringify({revision:owner.sourceRevision,producerMode:'record-type-receipts',bundleSha256:hash(script)}));const loaded=await loadUmfRecordTypeReceiptProducer(temp);
   if(mutation.includes('Object.fromEntries'))expect(collectCatalogTypeReceipts(s.prepared,loaded,s.wire).entries.length).toBe(1);else expect(()=>collectCatalogTypeReceipts(s.prepared,loaded,s.wire)).toThrow(mutation.includes('defineProperty')?'Inert receipt JSON':'full owner result');
  }finally{await rm(temp,{recursive:true,force:true})}
 }
});
test('collection custody crosses neither preparations nor private report native boundaries',async()=>{
 const s=setup(),c=collectCatalogTypeReceipts(s.prepared,owner,s.wire);expect(()=>requireOriginalCatalogTypeReceipts(s.prepared,{...c})).toThrow('collection custody');const other=preparation.prepare(packet(s.input));expect(()=>requireOriginalCatalogTypeReceipts(other,c)).toThrow('collection custody');
 let calls=0;const connection={unsafe:async(query:string)=>{calls++;if(query.includes('runtime_collect_report_documents'))return [{doc_id:'doc',doc_revision:'r1',content_sha256:s.prepared.original.input.documents[0]!.artifact.sha256,ord:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'}];if(query.includes('runtime_collect_new_catalog_counts'))return [{types_added:'0',properties_added:'0',keys_added:'0',relationships_added:'0',endpoints_added:'0',elements_retired:'0',provisional_count:'0',writer_xid:'42',operation_ordinal:'0',effect_generation:'11'}];return []}};
 for(const value of [false,0,'',null])await expect(collectCatalogReportPreparation(connection,s.prepared,'1',declarations,fields,undefined,undefined,undefined,value as any)).rejects.toThrow('collection custody');expect(calls).toBe(0);
 await expect(collectCatalogReportPreparation(connection,other,'1',declarations,fields,undefined,undefined,undefined,c)).rejects.toThrow('collection custody');expect(calls).toBe(0);
 const report=await collectCatalogReportPreparation(connection,s.prepared,'1',declarations,fields,undefined,undefined,undefined,c);expect(report.typeReceipts).toBe(c);expect(report.coreAssertionIdentities.complete).toBe(false);expect(calls).toBeGreaterThan(0);expect(report.coreAssertionIdentities.entries.some(e=>e.ruleName==='core.recordType')).toBe(false);
});
