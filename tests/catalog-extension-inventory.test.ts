import {test,expect} from 'bun:test';
import {createCatalogInputPreparation} from '../packages/umf-bun/src/catalog-input';
import {collectCatalogExtensionInventory} from '../packages/umf-bun/src/catalog-extension-inventory';
const directory=process.env.TRUSS_UMF_PRODUCER;if(!directory)throw Error('Original producer required');
const preparation=await createCatalogInputPreparation(directory,'/Users/erik/Projects/umf/package.json');
async function prepared(){const input=structuredClone((await Bun.file('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').json()).input);input.binding={state:'absent'};input.transforms=[];
 const id='a/~',extensions={[id]:{expression:'opaque()',exact:'9007199254740993'}};
 const original=' \n'+JSON.stringify({umf:'0.7.0',id:'source',vocabularies:{[id]:{version:'1.0.0'}},extensions,modules:[{id:'m',namespace:'m',extensions,elements:[{id:'value',kind:'field',scalarType:'string',nullability:'required',cardinality:'one',extensions}]}]})+'\n';const bytes=Buffer.from(original);
 input.documents=[{documentId:'source',documentRevision:'r1',artifact:{identity:'source',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')},umfProfile:preparation.umfProfile,ingress:{kind:'native'}}];return preparation.prepare(new TextEncoder().encode(JSON.stringify(input)))}
test('repeated extension identity retains distinct original scopes and escaped source pointers',async()=>{
 const result=collectCatalogExtensionInventory(await prepared());expect(result.entries.map(e=>e.sourcePointer)).toEqual(['/extensions/a~1~0','/modules/0/extensions/a~1~0','/modules/0/elements/0/extensions/a~1~0']);expect(result.entries.map(e=>e.owner)).toEqual([{scope:'document',documentId:'source'},{documentId:'source',moduleId:'m'},{documentId:'source',moduleId:'m'}]);expect(result.entries.map(e=>e.scope)).toEqual(['document','module','element']);
});
test('original archive bytes and incomplete payload meaning survive without fragment substitution',async()=>{
 const source=await prepared(),result=collectCatalogExtensionInventory(source);for(const entry of result.entries){expect(entry.source).toBe(source.original.input.documents[0].artifact);expect(Buffer.from(entry.source.bytesBase64,'base64').toString()).toBe(source.documents[0].originalText);expect(entry.vocabulary).toEqual({version:'1.0.0'});expect(entry.payload).toEqual({expression:'opaque()',exact:'9007199254740993'});expect(Object.isFrozen(entry.payload)).toBe(true)}expect(source.documents[0].interpretation.sourceValidation.complete).toBe(false);expect(Object.isFrozen(result.entries)).toBe(true);
});
