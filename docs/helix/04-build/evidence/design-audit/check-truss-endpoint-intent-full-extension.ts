/** Representation probe only; not catalog admission or adopted endpoint semantics. */
import {createHash} from 'node:crypto';
import {readFile,writeFile,readdir} from 'node:fs/promises';
import {resolve} from 'node:path';
const owner=resolve(process.argv[2]??'');
if(!process.argv[2])throw Error('Exact clean committed UMF source directory required');
const allSourcePins:Record<string,string>={};
async function walk(path:string){
 for(const entry of await readdir(owner+'/'+path,{withFileTypes:true})){
  const child=path+'/'+entry.name;
  if(entry.isDirectory())await walk(child);
  else if(entry.isFile())allSourcePins[child]=createHash('sha256').update(await readFile(owner+'/'+child)).digest('hex');
  else throw Error('Unexpected owner source member');
 }
}
await walk('src');await walk('spec');
const ownerTreeSha256=createHash('sha256').update(JSON.stringify(Object.fromEntries(Object.entries(allSourcePins).sort(([a],[b])=>a<b?-1:a>b?1:0)))).digest('hex');
if(Object.keys(allSourcePins).length!==1342||ownerTreeSha256!=='299c8309fab01ca8e1675ff74d99e235ae0acb28bbfaad392200e2122fa60d9e')throw Error('Changed original committed owner source tree');
const {Registry}=await import(owner+'/src/registry/registry.ts');
const {validateDocument}=await import(owner+'/src/validation/document.ts');
const {upgradeSchemaPropertiesEnvelope,verifySchemaPropertiesUpgrade,rollbackSchemaPropertiesEnvelope}=await import(owner+'/src/model/schema-properties-transition.ts');
const id='truss-endpoint-intent-candidate',version='0.1.0';
const schemaBytes=await readFile(new URL('../../../02-design/contracts/truss-endpoint-intent-v0.1.proposal.schema.json',import.meta.url));
const schemaSha256=createHash('sha256').update(schemaBytes).digest('hex');
if(schemaSha256!=='b4362c9c6842f51d061c39021cfe6c38dc18dac183e46d0e005c5cad97fd2493')throw Error('Original complete candidate schema required');
const manifest={id,version,coreVersion:'0.1.0',description:'Unadopted complete Truss endpoint-intent document language',schema:JSON.parse(schemaBytes.toString('utf8')),
 semantics:'Document-local intent checks only. Declared external selection is not resolved package membership, accepted definition, security admission or native enforcement.',scopes:['document'],capabilities:{validation:'semantic',directions:[],evidence:[]}};
const semantics=(payload:any,context:any)=>{
 const diagnostics:any[]=[],seen=new Set<string>(),dependencies=new Map<string,string>();
 const add=(code:string,path:string)=>diagnostics.push({code,path:context.path+path,message:'Candidate document intent correspondence refused',severity:'error'});
 // This selected probe bound applies to callback work only, after owner schema validation.
 const occurrences=payload.dependencies.length+payload.intents.reduce((sum:number,intent:any)=>sum+intent.sources.length+intent.targets.length+(intent.associationRecord===null?0:1),0);
 if(occurrences>100){add('TRUSS_INTENT_BOUND','');return diagnostics;}
 payload.dependencies.forEach((dependency:any,index:number)=>{
  const key=JSON.stringify([dependency.document,dependency.revision]);
  if(dependencies.has(key))add('TRUSS_INTENT_DEPENDENCY_DUPLICATE','/dependencies/'+index);
  dependencies.set(key,dependency.sourceReference);
 });
 payload.intents.forEach((intent:any,index:number)=>{
  const at='/intents/'+index,key=JSON.stringify([intent.module,intent.id]);
  if(seen.has(key))add('TRUSS_INTENT_DUPLICATE',at+'/id');seen.add(key);
  if(!context.document.modules.some((module:any)=>module.id===intent.module))add('TRUSS_INTENT_MODULE',at+'/module');
  for(const slot of ['sourceBounds','targetBounds']){const bounds=intent[slot];if(bounds.max!=='*'&&(bounds.min.length>bounds.max.length||(bounds.min.length===bounds.max.length&&bounds.min>bounds.max)))add('TRUSS_INTENT_BOUNDS',at+'/'+slot);}
  const endpoint=(value:any,path:string)=>{
   if(value.definition.state==='pending')return;
   if(value.document!==context.document.id){
    if(dependencies.get(JSON.stringify([value.document,value.definition.revision]))!==value.definition.sourceReference)add('TRUSS_INTENT_DEPENDENCY_SELECTION',path+'/definition');
    return;
   }
   const records=context.document.modules.filter((module:any)=>module.id===value.module).flatMap((module:any)=>module.elements.filter((element:any)=>element.id===value.element&&element.kind==='record'));
   if(records.length!==1){add('TRUSS_INTENT_LOCAL_RECORD',path);return;}
   if(value.key?.state==='selected'&&(records[0].keys??[]).filter((key:any)=>key.name===value.key.name).length!==1)add('TRUSS_INTENT_LOCAL_KEY',path+'/key');
  };
  for(const slot of ['sources','targets']){const members=new Set<string>();intent[slot].forEach((value:any,member:number)=>{
   const lineage=JSON.stringify([value.document,value.module,value.element]),path=at+'/'+slot+'/'+member;
   if(members.has(lineage))add('TRUSS_INTENT_ENDPOINT_DUPLICATE',path);members.add(lineage);endpoint(value,path);
  });}
  if(intent.associationRecord!==null)endpoint(intent.associationRecord,at+'/associationRecord');
 });return diagnostics;
};
const registry=new Registry().register(manifest,semantics);
const local={document:'source',module:'m',element:'Source',definition:{state:'selected',revision:'r1',sourceReference:'source-source'}};
const original:any={umf:'0.7.0',id:'source',vocabularies:{[id]:{version}},extensions:{[id]:{interfaceVersion:'truss-endpoint-intents/0.1.0',dependencies:[],intents:[{id:'external',module:'m',name:'External',sources:[local],targets:[{document:'remote',module:'other',element:'Target',definition:{state:'pending',expectedRevision:null},key:{state:'pending',name:'Remote identity'}}],sourceBounds:{min:'0',max:'*'},targetBounds:{min:'0',max:'1'},directed:true,lifecycle:'independent',composition:false,inverse:null,associationRecord:null}]}},modules:[{id:'m',namespace:'probe',elements:[{id:'Source',kind:'record',members:[{module:'m',element:'source.id'}],keys:[{id:'identity',name:'Identity',fields:[{module:'m',element:'source.id'}],primary:true}],extensions:{}},{id:'source.id',kind:'field',scalarType:'integer',nullability:'required',cardinality:'one',extensions:{}}]}]};
const results:any[]=[];
function check(name:string,document:any,selected:any,valid:boolean,complete:boolean,code?:string){
 const before=JSON.stringify(document),result=validateDocument(document,selected);
 if(result.valid!==valid||result.complete!==complete||JSON.stringify(document)!==before||(code&&!result.diagnostics.some((diagnostic:any)=>diagnostic.code===code)))throw Error(name+': unexpected owner result '+JSON.stringify(result));
 results.push({name,result,sourceSha256:createHash('sha256').update(before).digest('hex')});
}
check('complete-registered-pending-language',original,registry,true,true);
check('unregistered-full-content-retained-incomplete',original,new Registry(),true,false);
const change=(name:string,edit:(payload:any,document:any)=>void,code:string)=>{const document=structuredClone(original);edit(document.extensions[id],document);check(name,document,registry,false,false,code);};
change('wrong-local-Record',(p)=>p.intents[0].sources[0].element='source.id','TRUSS_INTENT_LOCAL_RECORD');
change('wrong-declaring-module',(p)=>p.intents[0].module='missing','TRUSS_INTENT_MODULE');
change('duplicate-qualified-intent',(p)=>p.intents.push(structuredClone(p.intents[0])),'TRUSS_INTENT_DUPLICATE');
change('reversed-exact-bounds',(p)=>p.intents[0].targetBounds={min:'9007199254740993',max:'9007199254740992'},'TRUSS_INTENT_BOUNDS');
change('duplicate-endpoint-lineage',(p)=>p.intents[0].targets.push(structuredClone(p.intents[0].targets[0])),'TRUSS_INTENT_ENDPOINT_DUPLICATE');
change('selected-external-requires-declaration',(p)=>p.intents[0].targets[0].definition={state:'selected',revision:'r2',sourceReference:'remote-source'},'TRUSS_INTENT_DEPENDENCY_SELECTION');
change('duplicate-required-dependency',(p)=>p.dependencies=[{document:'remote',revision:'r2',sourceReference:'remote-source'},{document:'remote',revision:'r2',sourceReference:'remote-source'}],'TRUSS_INTENT_DEPENDENCY_DUPLICATE');
change('wrong-local-key-name',(p)=>p.intents[0].targets=[{...local,key:{state:'selected',name:'identity'}}],'TRUSS_INTENT_LOCAL_KEY');
change('association-must-be-Record',(p)=>p.intents[0].associationRecord={...local,element:'source.id'},'TRUSS_INTENT_LOCAL_RECORD');
const selected=structuredClone(original);selected.extensions[id].dependencies=[{document:'remote',revision:'r2',sourceReference:'remote-source'}];selected.extensions[id].intents[0].targets[0].definition={state:'selected',revision:'r2',sourceReference:'remote-source'};
check('declared-external-syntax-not-package-resolution',selected,registry,true,true);
const changedReference=structuredClone(selected);changedReference.extensions[id].dependencies[0].sourceReference='another-source';check('changed-external-reference-refuses',changedReference,registry,false,false,'TRUSS_INTENT_DEPENDENCY_SELECTION');
const overBound=structuredClone(original);overBound.extensions[id].intents[0].targets=Array.from({length:100},(_,i)=>({...structuredClone(original.extensions[id].intents[0].targets[0]),element:'Target'+i}));check('selected-callback-occurrence-bound',overBound,registry,false,false,'TRUSS_INTENT_BOUND');
const localKey=structuredClone(original);localKey.extensions[id].intents[0].targets=[{...local,key:{state:'selected',name:'Identity'}}];check('original-local-key-name',localKey,registry,true,true);
const malformed=structuredClone(original);delete malformed.extensions[id].intents[0].directed;check('missing-full-carrier-field',malformed,registry,false,false);
const invalidCore=structuredClone(original);invalidCore.modules[0].relationships=[{id:'invalid-core',name:'Invalid core',source:[{module:'m',element:'Source'}],target:[{module:'m',element:'Missing',key:'identity'}],sourceMultiplicity:{min:0,max:'*'},targetMultiplicity:{min:0,max:'*'},targetLifecycle:'independent',directed:true}];check('full-extension-does-not-repair-invalid-core',invalidCore,registry,false,false);
const originalText=JSON.stringify(original);
const transition=upgradeSchemaPropertiesEnvelope(original);
verifySchemaPropertiesUpgrade(transition);
if(JSON.stringify(original)!==originalText||transition.target.umf!=='0.8.0'||
 JSON.stringify(transition.target.extensions[id])!==JSON.stringify(original.extensions[id]))
 throw Error('Original source or complete extension changed during owner transition');
check('registered-transition-target-complete-language',transition.target,registry,true,true);
check('unregistered-transition-target-retains-incomplete-language',transition.target,new Registry(),true,false);
const restored=rollbackSchemaPropertiesEnvelope(transition,transition.target);
if(JSON.stringify(restored.target)!==originalText)throw Error('Full extension original rollback correspondence');
check('registered-restored-original-complete-language',restored.target,registry,true,true);
const wrongTargetKey=structuredClone(transition.target) as any;
wrongTargetKey.extensions[id].intents[0].targets=[{...local,key:{state:'selected',name:'identity'}}];
check('transition-target-retains-authored-key-name-rule',wrongTargetKey,registry,false,false,'TRUSS_INTENT_LOCAL_KEY');
const forgedTransition=structuredClone(transition) as any;
forgedTransition.target.extensions[id].intents[0].name='Changed retained intent';
let forgedRefused=false;
try{verifySchemaPropertiesUpgrade(forgedTransition)}catch{forgedRefused=true}
if(!forgedRefused)throw Error('Changed original transition receipt accepted');
results.push({name:'changed-extension-transition-receipt-refuses',operation:'verifySchemaPropertiesUpgrade',refused:true});
const editedCurrent=structuredClone(transition.target) as any;
editedCurrent.extensions[id].intents[0].name='Subsequent retained intent';
check('edited-current-target-still-valid-language',editedCurrent,registry,true,true);
const editedRollback=rollbackSchemaPropertiesEnvelope(transition,editedCurrent);
if(JSON.stringify(editedRollback.target)!==originalText||JSON.stringify(editedRollback.source)!==JSON.stringify(editedCurrent))
 throw Error('Owner rollback failed to preserve distinct current and original sources');
results.push({name:'rollback-preserves-edited-current-separately-from-original',operation:'rollbackSchemaPropertiesEnvelope',
 currentSha256:createHash('sha256').update(JSON.stringify(editedRollback.source)).digest('hex'),
 restoredOriginalSha256:createHash('sha256').update(JSON.stringify(editedRollback.target)).digest('hex'),
 scope:'Rollback is not unchanged-current-target verification'});
const receipt={status:'passed',ownerRevision:'1f7b5f5d2a355c4b476e3a96b289b9048f03f567',ownerTreeSha256,ownerSourceMembers:1342,schemaSha256,checkerSha256:createHash('sha256').update(await readFile(new URL(import.meta.url))).digest('hex'),manifest,results,scope:'Full candidate document language Registry/validateDocument experiment only; not adopted vocabulary, complete package membership, accepted-history custody, security, provisional/native relationship enforcement or release acceptance. Callback occurrence limit100 is not a complete decoder/resource profile.'};
await writeFile(new URL('./truss-endpoint-intent-transition-correspondence.json',import.meta.url),JSON.stringify(receipt,null,2)+'\n');
console.log(results.length+' original-owner full candidate language controls; no package/native acceptance');
