import {test,expect} from 'bun:test';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {resolveCatalogEndpointSuppliedSources} from '../packages/umf-bun/src/catalog-endpoint-source-references';
const directory=process.env.TRUSS_UMF_PRODUCER;if(!directory)throw Error('Original Record producer directory required');
const preparation=await createCatalogInputPreparation(directory,'/Users/erik/Projects/umf/package.json');
const fixture=await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json();
function request(){
 const input=structuredClone(fixture.input);input.binding={state:'absent'};input.transforms=[];
 input.documents=['first-doc','second-doc'].map(documentId=>{
  const text=' \n'+JSON.stringify({umf:'0.7.0',id:documentId,vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[{id:'Item',kind:'record',members:[{module:'m',element:'label'}],extensions:{}},{id:'label',kind:'field',scalarType:'string',nullability:'required',cardinality:'one',extensions:{}}]}]})+'\n';
  return {documentId,documentRevision:'r1',artifact:{identity:documentId+'-source',bytesBase64:Buffer.from(text).toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(text).digest('hex')},umfProfile:preparation.umfProfile,ingress:{kind:'native'}};
 });return input;
}
const prepare=(input=request())=>preparation.prepare(new TextEncoder().encode(JSON.stringify(input)));
const selection=(document:string)=>({document,revision:'r1',sourceReference:document+'-source'});
test('original local and mutual supplied selections retain actual source bytes rather than transitioned bytes',()=>{
 const prepared=prepare();
 const first=resolveCatalogEndpointSuppliedSources(prepared,'first-doc',[selection('first-doc'),selection('second-doc')],2);
 const second=resolveCatalogEndpointSuppliedSources(prepared,'second-doc',[selection('first-doc')],1);
 expect(first.matches.map(m=>m.documentId)).toEqual(['first-doc','second-doc']);
 expect(second.matches[0]!.artifact).toEqual(prepared.original.input.documents[0]!.artifact);
 expect(first.matches[0]!.originalText).toBe(prepared.documents[0]!.originalText);
 expect(first.matches[0]!.umfVersion).toBe('0.7.0');
 expect(first.scope).toBe('original_supplied_source_reference_correspondence_only');
 expect(Object.isFrozen(first.matches[0]!.artifact)).toBe(true);
});
test('reconstructed preparation cannot borrow original source custody',()=>{
 const prepared=prepare();
 for(const fake of [{...prepared},structuredClone(prepared)])expect(()=>resolveCatalogEndpointSuppliedSources(fake,'first-doc',[selection('first-doc')],1)).toThrow('validated catalog preparation');
});
test('wrong document revision reference and containing context refuse without latest fallback',()=>{
 const prepared=prepare();
 for(const changed of [{...selection('second-doc'),document:'missing'},{...selection('second-doc'),revision:'r2'},{...selection('second-doc'),sourceReference:'first-doc-source'},{...selection('second-doc'),sourceReference:'accepted-but-unregistered'}])
  expect(()=>resolveCatalogEndpointSuppliedSources(prepared,'first-doc',[changed],1)).toThrow('correspondence unavailable');
 expect(()=>resolveCatalogEndpointSuppliedSources(prepared,'missing',[],0)).toThrow('containing source');
});
test('duplicate opaque inventory references refuse even with otherwise valid original sources',()=>{
 const input=request();input.documents[1].artifact.identity=input.documents[0].artifact.identity;
 expect(()=>resolveCatalogEndpointSuppliedSources(prepare(input),'first-doc',[],0)).toThrow('Ambiguous original');
});
test('explicit occurrence bounds and copied projections preserve repeated references and caller isolation',()=>{
 const prepared=prepare(),selected=selection('second-doc');
 expect(()=>resolveCatalogEndpointSuppliedSources(prepared,'first-doc',[selected],0)).toThrow('bound');
 for(const bound of [NaN,Infinity,-1,0.5])expect(()=>resolveCatalogEndpointSuppliedSources(prepared,'first-doc',[],bound)).toThrow('bound');
 const result=resolveCatalogEndpointSuppliedSources(prepared,'first-doc',[selected,selected],2);selected.document='changed';
 expect(result.matches.map(m=>m.documentId)).toEqual(['second-doc','second-doc']);
 expect(resolveCatalogEndpointSuppliedSources(prepared,'first-doc',[],0).matches).toEqual([]);
});
