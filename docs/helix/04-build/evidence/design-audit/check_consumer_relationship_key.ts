/** Original consumer/UMF selector experiment; no compiler/native adoption. */
import {createHash} from 'node:crypto';
import {selectCoreRelationships} from '/Users/erik/Projects/umf/src/model/relationship-selection';
const root='/Users/erik/Projects/hohfeld/.claude/worktrees/helix-bootstrap-setup-f77e53';
const cases=[
 {path:root+'/src/hohfeld/conformance/module.umf.json',expected:[0]},
 {path:root+'/examples/catalog/catalog.umf.json',expected:[0,14,14,0]},
];
const observations=[];let negatives=0;
for(const c of cases){
 const bytes=new Uint8Array(await Bun.file(c.path).arrayBuffer());
 const doc=JSON.parse(new TextDecoder('utf8',{fatal:true}).decode(bytes));
 const result=selectCoreRelationships(doc,{});
 const expected=c.expected.map(i=>`/modules/0/elements/${i}/keys/0`);
 const actual=result.selection.map(s=>s.targets[0]!.keyPath);
 if(JSON.stringify(actual)!==JSON.stringify(expected)||result.selection.some(s=>s.targets.length!==1||s.targets[0]!.reference.key!=='identity'))throw Error('Original key-ID selection mismatch');
 for(let i=0;i<c.expected.length;i++){
  const changed=structuredClone(doc);changed.modules[0].relationships[i].target[0].key='Identity';
  let code='';try{selectCoreRelationships(changed,{});}catch(e){code=(e as {code?:string}).code??'';}
  if(code!=='RELATIONSHIP_SELECTION_SOURCE')throw Error('Display-name substitution did not refuse at source admission');
  negatives++;
 }
 observations.push({path:c.path,sha256:createHash('sha256').update(bytes).digest('hex'),expectedKeyPaths:expected,actualKeyPaths:actual,provenance:result.provenance,navigationScope:result.navigationScope});
}
const ownerPaths=['/Users/erik/Projects/umf/src/model/relationship-selection.ts','/Users/erik/Projects/weft/crates/weft-core/src/application_model.rs'];
const sources=[];for(const path of ownerPaths){const bytes=new Uint8Array(await Bun.file(path).arrayBuffer());sources.push({path,sha256:createHash('sha256').update(bytes).digest('hex')});}
await Bun.write(import.meta.dir+'/consumer-relationship-key-selection.json',JSON.stringify({scope:'actual UMF core selector and source-only Weft comparison; no compiler/native/security/profile adoption',positiveModels:cases.length,displayNameSubstitutionRefusals:negatives,sources,observations,nativeImplementationQualified:false},null,2)+'\n');
console.log('Two original consumer models resolve key ID; five display-name substitutions refuse');
