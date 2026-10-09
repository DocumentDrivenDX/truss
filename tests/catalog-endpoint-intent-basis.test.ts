import {test,expect} from 'bun:test';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {createCatalogEndpointIntentBasis} from '../packages/umf-bun/src/catalog-endpoint-intent-basis';
const directory=process.env.TRUSS_UMF_PRODUCER;if(!directory)throw Error('Original Record producer directory required');
const preparation=await createCatalogInputPreparation(directory,'/Users/erik/Projects/umf/package.json');
const basis=await createCatalogEndpointIntentBasis('/Users/erik/Projects/umf/package.json');
const fixture=await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json();
function payload(){return {interfaceVersion:'truss-endpoint-intents/0.1.0',dependencies:[{document:'second-doc',revision:'r1',sourceReference:'second-doc-source'}],intents:[{id:'link',module:'m',name:'link',sources:[{document:'first-doc',module:'m',element:'Item',definition:{state:'selected',revision:'r1',sourceReference:'first-doc-source'}}],targets:[{document:'second-doc',module:'m',element:'Item',definition:{state:'selected',revision:'r1',sourceReference:'second-doc-source'},key:{state:'absent'}}],sourceBounds:{min:'0',max:'*'},targetBounds:{min:'0',max:'1'},directed:true,lifecycle:'independent',composition:false,inverse:null,associationRecord:null}]}}
function prepare(value:any=payload()){
 const input=structuredClone(fixture.input);input.binding={state:'absent'};input.transforms=[];
 input.documents=['first-doc','second-doc'].map(documentId=>{
  const extension=documentId==='first-doc'?{[basis.extensionId]:value}:{};
  const text=JSON.stringify({umf:'0.7.0',id:documentId,vocabularies:documentId==='first-doc'?{[basis.extensionId]:{version:'0.1.0'}}:{},extensions:extension,modules:[{id:'m',namespace:'m',elements:[{id:'Item',kind:'record',members:[{module:'m',element:'label'}],extensions:{}},{id:'label',kind:'field',scalarType:'string',nullability:'required',cardinality:'one',extensions:{}}]}]});
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
