/** Source-only lifecycle fixture/UMF observation check; never native acceptance. */
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
const umfRoot=resolve(process.argv[2]??'/Users/erik/Projects/umf');
const require=(ok:boolean,message:string)=>{if(!ok)throw Error(message);};
const digest=(bytes:string)=>createHash('sha256').update(bytes).digest('hex');
const receipt=await Bun.file('docs/helix/04-build/evidence/design-audit/reference-lifecycle-umf-validation.json').json();
const command=(args:string[])=>{const r=Bun.spawnSync(args,{cwd:umfRoot});require(r.exitCode===0,'dependency observation failed');return r.stdout.toString().trim();};
require(command(['git','rev-parse','HEAD'])===receipt.umfHead,'UMF revision differs from original observation');
require(command(['git','status','--porcelain'])==='','UMF checkout contains uncommitted changes');
require(digest(await Bun.file(resolve(umfRoot,'src/validation/document.ts')).text())==='2569bf6aadd33e3b228b3ae9ffd5d3c0da60500e8f26baa078bba81b17c8634b','original validator source differs');
const {validateDocument}=await import(resolve(umfRoot,'src/validation/document.ts'));
require(receipt.observations.length===3,'missing or extra original fixture');
const docs=[];
for(const observation of receipt.observations){
 const bytes=await Bun.file(observation.path).text();require(digest(bytes)===observation.sha256,'fixture bytes differ');
 const doc=JSON.parse(bytes);docs.push(doc);const actual=validateDocument(doc);
 require(JSON.stringify(actual)===JSON.stringify(observation.result),'original validator output differs');
 require(actual.valid===true&&actual.complete===false,'experimental validation scope differs');
}
const retired=structuredClone(docs[0]);const m=retired.modules[0];m.elements=m.elements.filter((e:any)=>e.id!=='Item.note');
const item=m.elements.find((e:any)=>e.id==='Item');item.members=item.members.filter((e:any)=>e.element!=='Item.note');
require(JSON.stringify(retired)===JSON.stringify(docs[1]),'retirement changes more than original field/member removal');
const fresh=structuredClone(docs[0]);fresh.modules[0].elements.find((e:any)=>e.id==='Item.note').id='Item.note.new-incarnation';
fresh.modules[0].elements.find((e:any)=>e.id==='Item').members.find((e:any)=>e.element==='Item.note').element='Item.note.new-incarnation';
require(JSON.stringify(fresh)===JSON.stringify(docs[2]),'fresh incarnation changes more than original field/member identity');
console.log('Three original fixtures and validator observations reproduced; complete=false; no native qualification.');
