import {test,expect} from 'bun:test';
import {loadUmfProducer,loadUmfFieldAssertionProducer} from '../packages/umf-bun/src/index';
const recordDir=process.env.TRUSS_UMF_PRODUCER,fieldDir=process.env.TRUSS_UMF_FIELD_ASSERTION_PRODUCER;
if(!recordDir||!fieldDir)throw Error('Both original producer directories required');
const record=await loadUmfProducer(recordDir),fields=await loadUmfFieldAssertionProducer(fieldDir);
const original=JSON.stringify({umf:'0.7.0',id:'field-source',vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[{id:'value',kind:'field',scalarType:'string',nullability:'required',cardinality:'one',facets:{length:{max:10,unit:'unicode-scalar'},future:{value:'opaque'}},extensions:{}}]}]});
const observation=record.inspect(original),identity={module:'m',element:'value'};
test('owner separates interpreted facets from unknown source members',()=>{
 const inspected=fields.inspectFacets(observation.source,identity);expect(inspected.path).toBe('/modules/0/elements/0/facets');expect(inspected.meaning.state).toBe('partial');expect(inspected.meaning.interpreted).toEqual({length:{max:10,unit:'unicode-scalar'}});expect(inspected.meaning.facets.future).toEqual({value:'opaque'});expect(inspected.meaning.uninterpretedPaths).toContain('/modules/0/elements/0/facets/future');expect(inspected.provenance).toBe('unverified');
});
test('kind, availability and cardinality retain independent original meanings',()=>{
 expect(fields.inspectKind(observation.source,identity).meaning.state).toBe('known');expect(fields.inspectNullability(observation.source,identity).meaning).toEqual({state:'known',nullability:'required'});expect(fields.inspectCardinality(observation.source,identity).meaning.state).toBe('known');expect(JSON.stringify(observation.source)).toBe(original);
});
test('upgraded source cannot borrow the original field assertion result profile',()=>{
 for(const inspect of [fields.inspectKind,fields.inspectNullability,fields.inspectCardinality,fields.inspectFacets])expect(()=>inspect(observation.target,identity)).toThrow();
});
