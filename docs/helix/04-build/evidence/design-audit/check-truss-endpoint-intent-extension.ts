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
const id='truss-endpoint-intent-probe',version='0.1.0';
const coordinate={type:'object',properties:{document:{type:'string',minLength:1},revision:{type:'string',minLength:1},module:{type:'string',minLength:1},element:{type:'string',minLength:1}},required:['document','revision','module','element'],additionalProperties:false};
const manifest={id,version,coreVersion:'0.1.0',description:'Unadopted Truss endpoint-intent representation probe',
 schema:{type:'object',properties:{intents:{type:'array',items:{type:'object',properties:{id:{type:'string',minLength:1},source:{type:'object',properties:{module:{type:'string',minLength:1},element:{type:'string',minLength:1}},required:['module','element'],additionalProperties:false},target:coordinate},required:['id','source','target'],additionalProperties:false}}},required:['intents'],additionalProperties:false},
 semantics:'Probe local source ownership; external target is declared intent, not a core relationship or resolved endpoint.',
 scopes:['document'],capabilities:{validation:'semantic',directions:[],evidence:[]}};
const semantics=(payload:any,context:any)=>{
 const diagnostics:any[]=[],seen=new Set<string>();
 payload.intents.forEach((intent:any,index:number)=>{
  const source=context.document.modules.find((m:any)=>m.id===intent.source.module)?.elements.find((e:any)=>e.id===intent.source.element);
  if(source?.kind!=='record')diagnostics.push({code:'TRUSS_PROBE_SOURCE',path:context.path+'/intents/'+index+'/source',message:'Local Record source required',severity:'error'});
  if(seen.has(intent.id))diagnostics.push({code:'TRUSS_PROBE_DUPLICATE',path:context.path+'/intents/'+index+'/id',message:'Duplicate intent',severity:'error'});
  seen.add(intent.id);
 });return diagnostics;
};
const registry=new Registry().register(manifest,semantics);
const original:any={umf:'0.7.0',id:'source',vocabularies:{[id]:{version}},extensions:{[id]:{intents:[{id:'external',source:{module:'m',element:'Source'},target:{document:'not-supplied',revision:'r2',module:'remote',element:'Target'}}]}},modules:[{id:'m',namespace:'probe',elements:[{id:'Source',kind:'record',members:[{module:'m',element:'source.id'}],keys:[{id:'identity',name:'Identity',fields:[{module:'m',element:'source.id'}],primary:true}],extensions:{}},{id:'source.id',kind:'field',scalarType:'integer',nullability:'required',cardinality:'one',extensions:{}}]}]};
const results:any[]=[];
function check(name:string,document:any,selected:any,valid:boolean,complete:boolean){
 const before=JSON.stringify(document),result=validateDocument(document,selected);
 if(result.valid!==valid||result.complete!==complete||JSON.stringify(document)!==before)throw Error(name+': unexpected validity/completeness/source mutation '+JSON.stringify(result));
 results.push({name,result,sourceSha256:createHash('sha256').update(before).digest('hex')});
}
check('registered-pending-external-intent',original,registry,true,true);
check('unregistered-content-is-retained-only',original,new Registry(),true,false);
const wrong=structuredClone(original);wrong.extensions[id].intents[0].source.element='not-local';
check('wrong-local-source-refuses',wrong,registry,false,false);
const duplicate=structuredClone(original);duplicate.extensions[id].intents.push(structuredClone(duplicate.extensions[id].intents[0]));
check('duplicate-intent-refuses',duplicate,registry,false,false);
const native=structuredClone(original);native.modules[0].relationships=[{id:'invalid-core',name:'Invalid core',source:[{module:'m',element:'Source'}],target:[{module:'m',element:'Missing',key:'identity'}],sourceMultiplicity:{min:0,max:'*'},targetMultiplicity:{min:0,max:'*'},targetLifecycle:'independent',directed:true}];
check('extension-does-not-repair-invalid-core-endpoint',native,registry,false,false);
const paths=['src/registry/registry.ts','src/validation/document.ts','src/validation/relationships.ts','src/model/types.ts','spec/core/extension-package.schema.json'];
const sourceSha256:Record<string,string>={};for(const path of paths)sourceSha256[path]=createHash('sha256').update(await readFile(owner+'/'+path)).digest('hex');
const receipt={status:'passed',ownerRevision:'1f7b5f5d2a355c4b476e3a96b289b9048f03f567',ownerTreeSha256,ownerSourceMembers:1342,sourceSha256,manifest,results,scope:'Existing Registry/validateDocument representability only. Truss-owned probe semantics; not core cross-document support, resolved relationship meaning, provisional/skip/promotion policy, native acceptance or adopted extension.'};
await writeFile(new URL('./truss-endpoint-intent-extension-probe.json',import.meta.url),JSON.stringify(receipt,null,2)+'\n');
console.log(results.length+' owner-validator controls; representation probe only');
