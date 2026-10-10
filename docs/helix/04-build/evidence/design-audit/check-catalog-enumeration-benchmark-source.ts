/** Existing UMF metadata/roundtrip evidence only; no Truss support or native installation. */
import {validateDocument} from '/Users/erik/Projects/umf/src/validation/document';
import {readDocument,writeDocument} from '/Users/erik/Projects/umf/src/model/document';
const root='/Users/erik/Projects/umf';
const git=(args:string[])=>{const r=Bun.spawnSync(['git','-C',root,...args]);if(r.exitCode)throw Error('owner observation failed');return new TextDecoder().decode(r.stdout).trim();};
const before={head:git(['rev-parse','HEAD']),status:git(['status','--porcelain'])};
const path='docs/helix/02-design/contracts/bindings/catalog-enumeration-benchmark-v0.1.proposal.umf.json';
const raw=await Bun.file(path).text();const source=readDocument(raw,'json');const result=validateDocument(source);
if(!result.valid)throw Error(JSON.stringify(result));
const canonical=(v:any):any=>Array.isArray(v)?v.map(canonical):v!==null&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const exact=(actual:any,expected:any,label:string)=>{if(JSON.stringify(canonical(actual))!==JSON.stringify(canonical(expected)))throw Error('fixture mismatch: '+label);};
function checkFixture(doc:any){
 exact(Object.keys(doc).sort(),['id','modules','umf','vocabularies'],'document fields');
 exact([doc.umf,doc.id,doc.vocabularies],['0.7.0','truss.catalog-enumeration.benchmark.v1',{}],'document profile');
 if(doc.modules.length!==1)throw Error('fixture mismatch: module membership');
 const mod=doc.modules[0];
 exact(Object.keys(mod).sort(),['elements','id','namespace','relationships'],'module fields');
 exact([mod.id,mod.namespace],['catalog-benchmark','truss.catalog.benchmark'],'module identity');
 if(mod.elements.length!==5000||mod.relationships.length!==1000)throw Error('fixture mismatch: cardinalities');
 const elements=new Map(mod.elements.map((e:any)=>[e.id,e])),relationships=new Map(mod.relationships.map((e:any)=>[e.id,e]));
 if(elements.size!==5000||relationships.size!==1000)throw Error('fixture mismatch: duplicate identities');
 const ref=(element:string)=>({module:'catalog-benchmark',element});
 const fields=[['code','string'],['label','string'],['rank','integer'],['enabled','boolean']];
 for(let i=1;i<=1000;i++){
  const t='T'+String(i).padStart(4,'0'),next='T'+String(i%1000+1).padStart(4,'0');
  for(const [name,scalarType] of fields)exact(elements.get(t+'.'+name),{id:t+'.'+name,name,kind:'field',scalarType,nullability:'required',cardinality:'one',extensions:{}},t+'.'+name);
  exact(elements.get(t),{id:t,name:t,kind:'record',members:fields.map(([n])=>ref(t+'.'+n)),keys:[{id:'by-code',name:'by-code',fields:[ref(t+'.code')],primary:true},{id:'by-label-rank',name:'by-label-rank',fields:[ref(t+'.label'),ref(t+'.rank')]}],extensions:{}},t);
  exact(relationships.get(t+'.next'),{id:t+'.next',name:t+'.next',source:[ref(t)],target:[{...ref(next),key:'by-code'}],sourceMultiplicity:{min:0,max:1},targetMultiplicity:{min:0,max:1},targetLifecycle:'independent',directed:true},t+'.next');
 }
}
checkFixture(source);
const fixtureControls:any[]=[];
for(const [name,mutate] of [
 ['changed_scalar_family',(d:any)=>d.modules[0].elements[3].scalarType='integer'],
 ['changed_presence',(d:any)=>d.modules[0].elements[3].nullability='absent-allowed'],
 ['changed_composite_key_order',(d:any)=>d.modules[0].elements[4].keys[1].fields.reverse()],
 ['changed_relationship_bound',(d:any)=>d.modules[0].relationships[0].targetMultiplicity.max=2],
 ['changed_ring_endpoint',(d:any)=>d.modules[0].relationships[0].target[0].element='T0001'],
 ['changed_record_name',(d:any)=>d.modules[0].elements[4].name='AlteredTypeName']
] as const){
 const candidate=structuredClone(source) as any;mutate(candidate);
 const validation=validateDocument(candidate);if(!validation.valid)throw Error('control must remain UMF-valid: '+name);
 let refused=false;try{checkFixture(candidate);}catch(e){if(!(e instanceof Error)||!e.message.startsWith('fixture mismatch:'))throw e;refused=true;}
 if(!refused)throw Error('fixture checker accepted workload substitution: '+name);
 fixtureControls.push({name,umfValid:validation.valid,umfComplete:validation.complete,status:'expected-fixture-refusal'});
}

const reloaded=readDocument(writeDocument(source,'json'),'json');
if(JSON.stringify(source)!==JSON.stringify(reloaded))throw Error('metadata roundtrip mismatch');
const missingEndpoint=structuredClone(source) as any;missingEndpoint.modules[0].relationships[0].target[0].element='missing';
const invalidEndpoint=validateDocument(missingEndpoint);if(invalidEndpoint.valid)throw Error('missing relationship endpoint accepted');
const missingKey=structuredClone(source) as any;missingKey.modules[0].relationships[0].target[0].key='missing';
const invalidKey=validateDocument(missingKey);if(invalidKey.valid)throw Error('missing relationship key accepted');
const badBounds=structuredClone(source) as any;badBounds.modules[0].relationships[0].targetMultiplicity.min=3;
const invalidBounds=validateDocument(badBounds);if(invalidBounds.valid)throw Error('inverted multiplicity accepted');
const duplicateName=structuredClone(source) as any;duplicateName.modules[0].relationships[1].name=duplicateName.modules[0].relationships[0].name;
const invalidName=validateDocument(duplicateName);if(invalidName.valid)throw Error('duplicate module relationship name accepted');
const after={head:git(['rev-parse','HEAD']),status:git(['status','--porcelain'])};if(JSON.stringify(before)!==JSON.stringify(after)||await Bun.file(path).text()!==raw)throw Error('source changed');
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const ownerFiles=['src/validation/document.ts','src/validation/relationships.ts','src/validation/keys.ts','src/model/document.ts','spec/core/relationship-document.schema.json'];
const pins=await Promise.all(ownerFiles.map(async path=>({path,sha256:hash(await Bun.file(root+'/'+path).text())})));
await Bun.write('docs/helix/04-build/evidence/design-audit/catalog-enumeration-benchmark-source.json',JSON.stringify({scope:'UMF 0.7 proposed benchmark metadata validation/serialization and independent authored identity/member/key/ring correspondence; four malformed variants refused. No Truss catalog extraction, native installation, Weft binding, public enumeration or latency qualification.',expectedMembership:{types:1000,properties:4000,keys:2000,keyComponents:3000,relationships:1000,endpointReferences:2000},source:{path,sha256:hash(raw)},owner:{root,...before,files:pins},bunVersion:Bun.version,validation:result,roundtripExactTree:true,fixtureControls,controls:[{name:'missing_endpoint',validation:invalidEndpoint},{name:'missing_key',validation:invalidKey},{name:'inverted_multiplicity',validation:invalidBounds},{name:'duplicate_relationship_name',validation:invalidName}]},null,2)+'\n');
console.log(JSON.stringify({valid:result.valid,complete:result.complete,controls:4,fixtureControls:fixtureControls.length,roundtripExactTree:true}));
