import {test,expect} from 'bun:test';
import {createCatalogEndpointRecords} from '../packages/umf-bun/src/catalog-endpoint-records';
import {createCatalogEndpointDocumentOrder} from '../packages/umf-bun/src/catalog-endpoint-document-order';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {createCatalogEndpointIntentBasis} from '../packages/umf-bun/src/catalog-endpoint-intent-basis';
const directory=process.env.TRUSS_UMF_PRODUCER;if(!directory)throw Error('Original Record producer directory required');
const preparation=await createCatalogInputPreparation(directory,'/Users/erik/Projects/umf/package.json');
const basis=await createCatalogEndpointIntentBasis('/Users/erik/Projects/umf/package.json');
const records=await createCatalogEndpointRecords('/Users/erik/Projects/umf/package.json');
const ordering=await createCatalogEndpointDocumentOrder('/Users/erik/Projects/umf/package.json');
const fixture=await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json();
function payload(){return {interfaceVersion:'truss-endpoint-intents/0.1.0',dependencies:[{document:'second-doc',revision:'r1',sourceReference:'second-doc-source'}],intents:[{id:'link',module:'m',name:'link',sources:[{document:'first-doc',module:'m',element:'Item',definition:{state:'selected',revision:'r1',sourceReference:'first-doc-source'}}],targets:[{document:'second-doc',module:'m',element:'Item',definition:{state:'selected',revision:'r1',sourceReference:'second-doc-source'},key:{state:'absent'}}],sourceBounds:{min:'0',max:'*'},targetBounds:{min:'0',max:'1'},directed:true,lifecycle:'independent',composition:false,inverse:null,associationRecord:null}]}}
function prepare(value:any=payload(),second:any=null,ids=['first-doc','second-doc']){
 const input=structuredClone(fixture.input);input.binding={state:'absent'};input.transforms=[];
 input.documents=ids.map(documentId=>{
  const carrier=documentId==='first-doc'?value:documentId==='second-doc'?second:null;
  const extension=carrier===null?{}:{[basis.extensionId]:carrier};
  const text=JSON.stringify({umf:'0.7.0',id:documentId,vocabularies:carrier!==null?{[basis.extensionId]:{version:'0.1.0'}}:{},extensions:extension,modules:[{id:'m',namespace:'m',elements:[{id:'Item',kind:'record',members:[{module:'m',element:'label'}],keys:[{id:'label-key-id',name:'label-key',fields:[{module:'m',element:'label'}]}],extensions:{}},{id:'label',kind:'field',scalarType:'string',nullability:'required',cardinality:'one',extensions:{}}]}]});
  return {documentId,documentRevision:'r1',artifact:{identity:documentId+'-source',bytesBase64:Buffer.from(text).toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(text).digest('hex')},umfProfile:preparation.umfProfile,ingress:{kind:'native'}};
 });return preparation.prepare(new TextEncoder().encode(JSON.stringify(input)));
}
test('complete original carrier collects dependency and endpoint occurrences without claiming interpretation',()=>{
 const original=prepare(),result=basis.collect(original,3);
 expect(result.occurrences).toBe(3);expect(result.documents[0]!.referenceOccurrences.map(r=>r.kind)).toEqual(['dependency','selected','selected']);
 expect(result.documents[0]!.supplied.matches.map(r=>r.documentId)).toEqual(['second-doc','first-doc','second-doc']);
 expect(result.documents[0]!.payload).toBe((original.documents[0]!.interpretation.source as any).extensions[basis.extensionId]);
 expect(result.scope).toBe('original_endpoint_intent_shape_and_supplied_source_basis_only');
 expect(original.documents[0]!.validation.sourceValidation.complete).toBe(false);
});
test('pending intent preserves absence without inventing a source',()=>{
 const value=payload();value.dependencies=[];(value.intents[0]!.targets[0] as any).definition={state:'pending',expectedRevision:'r2'};
 const result=basis.collect(prepare(value),2);expect(result.documents[0]!.supplied.matches.length).toBe(1);
 expect(result.documents[0]!.referenceOccurrences[1]!.kind).toBe('pending');
});
test('incidental supplied target cannot replace declared dependency',()=>{
 const value=payload();value.dependencies=[];expect(()=>basis.collect(prepare(value),3)).toThrow('exact declared dependency');
});
test('duplicate dependency intent or endpoint lineage and reversed bounds refuse',()=>{
 for(const change of [(v:any)=>v.dependencies.push({...v.dependencies[0]}),(v:any)=>v.intents.push(structuredClone(v.intents[0])),(v:any)=>v.intents[0].targets.push(structuredClone(v.intents[0].targets[0])),(v:any)=>v.intents[0].targetBounds={min:'2',max:'1'}]){
  const value=payload();change(value);expect(()=>basis.collect(prepare(value),10)).toThrow();
 }
});
test('all occurrences include dependency pending and association work in one bound',()=>{
 expect(()=>basis.collect(prepare(),2)).toThrow('occurrence bound exceeded');
 const value=payload();value.intents[0]!.associationRecord=structuredClone(value.intents[0]!.sources[0]) as any;
 expect(()=>basis.collect(prepare(value),3)).toThrow('occurrence bound exceeded');
 expect(basis.collect(prepare(value),4).occurrences).toBe(4);
});
test('copied preparation and malformed required carrier cannot borrow basis',()=>{
 expect(()=>basis.collect({...prepare()},3)).toThrow('validated catalog preparation');
 const value=payload();delete (value.intents[0] as any).lifecycle;expect(()=>basis.collect(prepare(value),3)).toThrow('complete candidate endpoint carrier');
});

test('ordering includes every original independent document and preserves original object custody',()=>{
 const limits={documents:3,edges:1,identityBytes:256};
 for(const ids of [['first-doc','second-doc','third-doc'],['third-doc','second-doc','first-doc']]){
  const original=prepare(payload(),null,ids),result=ordering.order(original,3,limits);
  expect(result.documents.map(d=>d.documentId)).toEqual(['second-doc','first-doc','third-doc']);
  expect(result.documents[0]).toBe(original.documents.find(d=>d.documentId==='second-doc')!);
  expect(result.scope).toBe('original_supplied_endpoint_dependency_order_only');
 }
});
test('reciprocal original declarations form one complete deterministic component',()=>{
 const reciprocal={interfaceVersion:'truss-endpoint-intents/0.1.0',dependencies:[{document:'first-doc',revision:'r1',sourceReference:'first-doc-source'}],intents:[]};
 const result=ordering.order(prepare(payload(),reciprocal,['second-doc','third-doc','first-doc']),4,{documents:3,edges:2,identityBytes:256});
 expect(result.components).toEqual([['first-doc','second-doc'],['third-doc']]);
 expect(result.documents.map(d=>d.documentId)).toEqual(['first-doc','second-doc','third-doc']);
});
test('ordering refuses changed revision and insufficient full-set bounds',()=>{
 const value=payload();value.dependencies[0].revision='r2';
 expect(()=>ordering.order(prepare(value),3,{documents:2,edges:1,identityBytes:256})).toThrow();
 expect(()=>ordering.order(prepare(),3,{documents:1,edges:1,identityBytes:256})).toThrow('document bound');
 expect(()=>ordering.order(prepare(),3,{documents:2,edges:0,identityBytes:256})).toThrow('graph bound');
 expect(()=>ordering.order({...prepare()},3,{documents:2,edges:1,identityBytes:256})).toThrow('validated catalog preparation');
});

test('selected endpoints resolve owning original Records and exact key names',()=>{
 const value=payload();value.intents[0].targets[0].key={state:'selected',name:'label-key'} as any;
 const original=prepare(value),result=records.resolve(original,3);
 expect(result.endpoints.length).toBe(2);
 expect(result.endpoints[1].record).toBe(original.declarations[1].records[0]);
 expect(result.endpoints[1].key?.id).toBe('label-key-id');
 expect(result.scope).toBe('original_supplied_endpoint_record_key_correspondence_only');
});
test('non-Record endpoint and foreign key claims cannot resolve by incidental ownership',()=>{
 for(const change of [(v:any)=>v.intents[0].targets[0].element='label',(v:any)=>v.intents[0].targets[0].module='other',(v:any)=>v.intents[0].targets[0].key={state:'selected',name:'label-key-id'}]){
  const value=payload();change(value);expect(()=>records.resolve(prepare(value),3)).toThrow('correspondence unavailable');
 }
});
test('pending definitions and pending keys retain explicit unresolved meaning',()=>{
 const value=payload();value.dependencies=[];value.intents[0].targets[0].definition={state:'pending',expectedRevision:null} as any;
 const pending=records.resolve(prepare(value),2).endpoints[1];expect(pending.state).toBe('pending');expect(pending.record).toBeNull();
 const selected=payload();selected.intents[0].targets[0].key={state:'pending',name:'future-key'} as any;
 const result=records.resolve(prepare(selected),3).endpoints[1];expect(result.record).not.toBeNull();expect(result.key).toBeNull();
 expect(result.endpoint.key.state).toBe('pending');
});
