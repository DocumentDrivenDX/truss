/** Equal-membership revisions for independent future enumeration races; no native acceptance. */
import {readDocument,writeDocument} from '/Users/erik/Projects/umf/src/model/document';
import {validateDocument} from '/Users/erik/Projects/umf/src/validation/document';
const root='/Users/erik/Projects/umf';const git=(args:string[])=>{const r=Bun.spawnSync(['git','-C',root,...args]);if(r.exitCode)throw Error('owner observation failed');return new TextDecoder().decode(r.stdout).trim();};
const before={head:git(['rev-parse','HEAD']),status:git(['status','--porcelain'])};
const paths=['docs/helix/02-design/contracts/bindings/catalog-enumeration-benchmark-v0.1.proposal.umf.json','docs/helix/02-design/contracts/bindings/catalog-enumeration-race-revision-two-v0.1.proposal.umf.json'];
const raw=await Promise.all(paths.map(p=>Bun.file(p).text()));
const [a,b]=raw.map(s=>readDocument(s,'json')) as any[];
const validations=[validateDocument(a),validateDocument(b)];if(validations.some(v=>!v.valid))throw Error('invalid race fixture');
const expected=structuredClone(a);
for(const e of expected.modules[0].elements){e.name+='-revision-two';if(e.kind==='record')for(const k of e.keys)k.name+='-revision-two';}
for(const r of expected.modules[0].relationships)r.name+='-revision-two';
if(JSON.stringify(expected)!==JSON.stringify(b))throw Error('unexpected source/identity/member/topology change');
if(JSON.stringify(readDocument(writeDocument(b,'json'),'json'))!==JSON.stringify(b))throw Error('race source roundtrip changed');
const verifyViewFixture=(v:any)=>{
 const text=JSON.stringify(v);if(text!==JSON.stringify(a)&&text!==JSON.stringify(b))throw Error('mixed authored fixture');
};
verifyViewFixture(a);verifyViewFixture(b);
const hybrids=[structuredClone(a),structuredClone(a),structuredClone(a)];
hybrids[0].modules[0].elements[0].name=b.modules[0].elements[0].name;
hybrids[1].modules[0].elements[4].keys[0].name=b.modules[0].elements[4].keys[0].name;
hybrids[2].modules[0].relationships[0].name=b.modules[0].relationships[0].name;
let refused=0;for(const h of hybrids){if(!validateDocument(h).valid)throw Error('hybrid should remain UMF-valid');try{verifyViewFixture(h);}catch(e){if((e as Error).message!=='mixed authored fixture')throw e;refused++;}}
if(refused!==3)throw Error('hybrid accepted');
if(JSON.stringify(before)!==JSON.stringify({head:git(['rev-parse','HEAD']),status:git(['status','--porcelain'])}))throw Error('owner changed');
for(let i=0;i<paths.length;i++)if(await Bun.file(paths[i]!).text()!==raw[i])throw Error('original fixture changed');
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
await Bun.write('docs/helix/04-build/evidence/design-audit/catalog-enumeration-race-source.json',JSON.stringify({scope:'UMF 0.7 source validity/exact roundtrip and equal complete source membership with independently specified display-name-only revision changes; three UMF-valid hybrid source fixtures refused by full original byte/tree membership. No actual native view/identity/history/acceptance/concurrency or latency qualification.',sources:paths.map((path,i)=>({path,sha256:hash(raw[i]!)})),owner:{root,...before,validatorSha256:hash(await Bun.file(root+'/src/validation/document.ts').text())},validations,changes:{fieldNames:4000,recordNames:1000,keyNames:2000,relationshipNames:1000,identitiesMembersKeysEndpointsBoundsUnchanged:true},hybridControls:refused,roundtripExactTree:true},null,2)+'\n');
console.log(JSON.stringify({valid:true,complete:validations.every(v=>v.complete),hybridControls:refused,nativeExecution:false}));
