/** Validate an explicitly authored review target; originals remain unchanged. */
import {createHash} from 'node:crypto';
import {validateDocument} from '/Users/erik/Projects/umf/src/validation/document';
import {selectCoreRelationships} from '/Users/erik/Projects/umf/src/model/relationship-selection';
const packetPath=import.meta.dir+'/../../../03-test/consumer-explicit-names.proposal.json';
const packet=await Bun.file(packetPath).json();const observations=[];
for(const source of packet.sources){
 const bytes=new Uint8Array(await Bun.file(source.sourcePath).arrayBuffer());
 if(createHash('sha256').update(bytes).digest('hex')!==source.sourceSha256)throw Error('Original consumer source changed');
 const original=JSON.parse(new TextDecoder('utf8',{fatal:true}).decode(bytes));
 const target=structuredClone(original);
 for(const edit of source.authoredNameAdditions){
  const match=/^\/modules\/0\/elements\/([0-9]+)\/name$/.exec(edit.pointer);
  if(!match)throw Error('Unknown authored edit');
  const e=target.modules[0].elements[Number(match[1])];
  if(e.id!==edit.element||Object.hasOwn(e,'name')||typeof edit.name!=='string'||!edit.name)throw Error('Authored edit correspondence');
  e.name=edit.name;
 }
 const validation=validateDocument(target);if(!validation.valid)throw Error('Invalid explicit target');
 const undo=structuredClone(target);for(const edit of source.authoredNameAdditions){const index=Number(edit.pointer.split('/')[4]);delete undo.modules[0].elements[index].name;}
 if(JSON.stringify(undo)!==JSON.stringify(original))throw Error('Unrequested semantic content changed');
 const before=selectCoreRelationships(original,{}),after=selectCoreRelationships(target,{});
 if(JSON.stringify(before.selection.map(x=>x.targets))!==JSON.stringify(after.selection.map(x=>x.targets)))throw Error('Original relationship/key correspondence changed');
 const current=new Uint8Array(await Bun.file(source.sourcePath).arrayBuffer());if(createHash('sha256').update(current).digest('hex')!==source.sourceSha256)throw Error('Original source mutated');
 observations.push({sourcePath:source.sourcePath,sourceSha256:source.sourceSha256,authoredNames:source.authoredNameAdditions.length,targetSha256:createHash('sha256').update(JSON.stringify(target)).digest('hex'),valid:validation.valid,complete:validation.complete,diagnostics:validation.diagnostics,originalOtherContentPreserved:true,relationshipKeyCorrespondencePreserved:true});
}
await Bun.write(import.meta.dir+'/consumer-explicit-names.json',JSON.stringify({scope:'UMF validation of explicitly authored candidate names only; no consumer/compiler/native adoption',observations,nativeImplementationQualified:false},null,2)+'\n');
console.log('Two explicitly named review targets validate; original content and key correspondence preserved');
