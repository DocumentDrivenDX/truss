/** Existing UMF authored-ideal operation/selection evidence, never native Truss adoption. */
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {declareCoreRecordMembers,declareCoreKey,lookupCoreKey,verifyCoreKeyOperation} from '/Users/erik/Projects/umf/src/model/keys';
import {declareCoreRelationship,verifyCoreRelationshipOperation} from '/Users/erik/Projects/umf/src/model/relationships';
import {selectCoreElements} from '/Users/erik/Projects/umf/src/model/selection';
import {selectCoreRelationships,verifyCoreRelationshipSelection} from '/Users/erik/Projects/umf/src/model/relationship-selection';
const owner='/Users/erik/Projects/umf';
const git=(args:string[])=>{const r=Bun.spawnSync(['git','-C',owner,...args]);if(r.exitCode)throw Error('owner observation failed');return new TextDecoder().decode(r.stdout).trim();};
const before={head:git(['rev-parse','HEAD']),status:git(['status','--porcelain'])};
const path='docs/helix/02-design/contracts/bindings/reference-account-items-v0.1.proposal.umf.json';const raw=await Bun.file(path).text(),source=readDocument(raw,'json');
const operations=[];const lookups=[];
for(const name of ['Account','Item']){
 const record=source.modules[0]!.elements.find(e=>e.id===name)!;const identity={module:'integration',element:name};
 const members=declareCoreRecordMembers(source,identity,record.members as any);verifyCoreKeyOperation(members,source);operations.push(members);
 const key=declareCoreKey(source,identity,(record.keys as any)[0]);verifyCoreKeyOperation(key,source);operations.push(key);
 const lookup=lookupCoreKey(source,{...identity,key:'by-code'});if(lookup.uninterpretedPaths.length)throw Error('uninterpreted key');lookups.push(lookup);
}
const relationship=declareCoreRelationship(source,{module:'integration'},(source.modules[0]!.relationships as any)[0]);verifyCoreRelationshipOperation(relationship,source);operations.push(relationship);
const selected=selectCoreElements(source,{references:'transitive',identities:[{module:'integration',element:'Account'},{module:'integration',element:'Item'}]});
const expected=['Account','Account.code','Item','Item.amount','Item.code','Item.note'];if(JSON.stringify(selected.selection.map(e=>e.element.id).sort())!==JSON.stringify(expected))throw Error('selection identity inventory');
if(selected.boundaryMembers?.length||selected.boundaryKeyFields?.length||selected.boundaryReferences.length)throw Error('unexpected boundary');
const relations=selectCoreRelationships(source,{identities:[{module:'integration',id:'account-items'}]});verifyCoreRelationshipSelection(relations);
if(relations.selection.length!==1||relations.selection[0]!.uninterpretedPaths.length||relations.selection[0]!.targets[0]!.keyPath!=='/modules/0/elements/5/keys/0')throw Error('relationship target/key source correspondence');
let controls=0;
const wrongKey=structuredClone(operations[1]) as any;wrongKey.request.fields[0].element='Item.code';try{verifyCoreKeyOperation(wrongKey,source);}catch{controls++;}
const wrongSelection=structuredClone(relations);wrongSelection.selection[0]!.targets[0]!.keyPath='/modules/0/elements/4/keys/0';try{verifyCoreRelationshipSelection(wrongSelection);}catch{controls++;}
if(controls!==2)throw Error('corrupted owner receipt accepted');
const after={head:git(['rev-parse','HEAD']),status:git(['status','--porcelain'])};if(JSON.stringify(before)!==JSON.stringify(after)||await Bun.file(path).text()!==raw)throw Error('source changed');
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');const files=['src/model/keys.ts','src/model/relationships.ts','src/model/selection.ts','src/model/relationship-selection.ts'];
const pins=await Promise.all(files.map(async path=>({path,sha256:hash(await Bun.file(owner+'/'+path).text())})));
await Bun.write('docs/helix/04-build/evidence/design-audit/reference-account-items-identity.json',JSON.stringify({scope:'Existing UMF authored members/key/relationship receipts and exact metadata selection/source paths; no native identity, catalog ID allocation, codec, enforcement or Weft binding adoption',owner:{root:owner,...before,files:pins},source:{path,sha256:hash(raw)},operations,lookups,selected,relations,corruptedReceiptRefusals:controls},null,2)+'\n');
console.log(JSON.stringify({authoredOperations:operations.length,keys:lookups.length,selectedElements:6,relationships:1,corruptedReceiptRefusals:controls}));
