/** Actual existing upstream field checker with explicit 0.7 -> 0.8 receipts. */
import {verifyExactArtifacts} from '@documentdrivendx/truss-postgresql';
import {readFile,writeFile,mkdtemp} from 'node:fs/promises';
import {join} from 'node:path';
import {createRequire} from 'node:module';
const root=process.argv[2],examples=process.argv[3];if(!root||!examples)throw Error('Pinned newer UMF checkout and example directory required');
const revision='16c35e8d943769ccfa7bb57d16785aa7159abe65';
const git=(args:string[])=>{const r=Bun.spawnSync(['git',...args],{cwd:root});if(r.exitCode)throw Error('Source observation failed');return new TextDecoder().decode(r.stdout).trim();};
if(git(['rev-parse','HEAD'])!==revision||git(['status','--porcelain']))throw Error('Exact clean UMF source required');
const temporary=await mkdtemp('/private/tmp/truss-umf-value-');const entry=join(temporary,'producer.ts');
await writeFile(entry,`export {readDocument} from ${JSON.stringify(root+'/src/model/document.ts')};\nexport {validateDocument} from ${JSON.stringify(root+'/src/validation/document.ts')};\nexport {validateCoreFieldValue} from ${JSON.stringify(root+'/src/model/schema-properties.ts')};\nexport {upgradeSchemaPropertiesEnvelope,verifySchemaPropertiesUpgrade,rollbackSchemaPropertiesEnvelope} from ${JSON.stringify(root+'/src/model/schema-properties-transition.ts')};\n`);
const build=await Bun.build({entrypoints:[entry],outdir:temporary,target:'browser',format:'esm',naming:'producer.js'});if(!build.success)throw Error('Actual field producer build failed');
const bundle=await readFile(join(temporary,'producer.js'));const producer=await import(join(temporary,'producer.js'));
const originals=[];
for(const identity of ['schema-v1.umf.json','schema-v2.umf.json','schema-v3.umf.json','schema-unknown.umf.json']){
 const bytes=await readFile(examples+'/'+identity);const [artifact]=await verifyExactArtifacts([{identity,bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')}],{maxArtifacts:1,maxSingleBytes:65536,maxTotalBytes:65536});originals.push(artifact);
}
const sourceBytes=await readFile(examples+'/local-string-source.jsonl');
// Only explicitly mapped string properties are selected. The complete original
// source bytes/hash remain separate; opaque retained_json is never parsed.
const values=[];
for(const line of sourceBytes.toString('utf8').trim().split('\n')){
 const event=JSON.parse(line);if(event.kind!=='event'||event.operation==='delete')continue;
 for(const [id,value] of Object.entries(JSON.parse(event.props_json))){
  if(!['23','24'].includes(id)||typeof value!=='string')throw Error('Unsupported explicit fixture property');
  values.push({delivery:event.delivery_id,fixturePropertyId:id,field:{module:'fixture',element:id==='23'?'label':'caption'},literal:{string:value}});
 }
}
const run=(u:any,artifacts:any[],values:any[])=>{
 const results=artifacts.map(artifact=>{
  const source=u.readDocument(new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(Uint8Array.from(atob(artifact.bytesBase64),(c:string)=>c.charCodeAt(0))),'json');
  const upgrade=u.upgradeSchemaPropertiesEnvelope(source);u.verifySchemaPropertiesUpgrade(upgrade);
  const rollback=u.rollbackSchemaPropertiesEnvelope(upgrade,upgrade.target);
  if(JSON.stringify(rollback.target)!==JSON.stringify(source))throw Error('Original schema not recoverable');
  if(artifact.identity==='schema-unknown.umf.json'&&upgrade.target['x-future-assertion']?.meaning!=='retained until supported')throw Error('Unknown assertion lost');
  const probes=[];
  for(const module of upgrade.target.modules)for(const element of module.elements)if(element.kind==='field'){
   const field={module:module.id,element:element.id};
   for(const literal of [{string:'雪🙂'},null,{integerToken:'9007199254740993123'}])probes.push({field,literal,result:u.validateCoreFieldValue(upgrade.target,field,literal)});
  }
  return {identity:artifact.identity,originalSha256:artifact.sha256,sourceValidation:u.validateDocument(source),upgrade,rollback,probes,
   legacyValueCheck:u.validateCoreFieldValue(source,{module:'fixture',element:'label'},{string:'original'}),targetValidation:u.validateDocument(upgrade.target)};
 });
 for(const result of results)for(const probe of result.probes){
  if(probe.literal&&'integerToken' in probe.literal&&probe.result.valid)throw Error('Wrong scalar family admitted');
  if(probe.field.element==='label'&&probe.literal===null&&probe.result.valid)throw Error('Required null admitted');
  if(result.identity==='schema-v3.umf.json'&&probe.field.element==='caption'&&probe.literal===null&&(!probe.result.valid||!probe.result.complete))throw Error('Explicit absent-allowed null not checked');
 }
 const target=results.find(result=>result.identity==='schema-v3.umf.json')!.upgrade.target;
 const sourceChecks=values.map(value=>({...value,originalResult:u.validateCoreFieldValue(target,value.field,value.literal)}));
 if(sourceChecks.some(check=>!check.originalResult.valid||!check.originalResult.complete))throw Error('Actual source string value check not complete');
 if(results.some(result=>result.legacyValueCheck.valid))throw Error('Silent version reinterpretation');
 return {results,sourceChecks};
};
const bunResult=run(producer,originals,values);
const require=createRequire(root+'/package.json');const {chromium}=require('playwright');
const server=Bun.serve({hostname:'127.0.0.1',port:0,fetch(request){return new URL(request.url).pathname==='/producer.js'?new Response(bundle,{headers:{'content-type':'text/javascript'}}):new Response('<!doctype html><title>UMF field checks</title>');}});
let browser;
try{
 browser=await chromium.launch({headless:true,...(process.env.UMF_CHROMIUM_PATH?{executablePath:process.env.UMF_CHROMIUM_PATH}:{})});const page=await browser.newPage();await page.goto('http://127.0.0.1:'+server.port);
 const browserResult=await page.evaluate(async({originals,values,runText}:any)=>{const path='/producer.js',u=await import(path);const run=eval('('+runText+')');return run(u,originals,values);},{originals,values,runText:run.toString()});
 if(JSON.stringify(browserResult)!==JSON.stringify(bunResult))throw Error('Original check results differ between runtimes');
 await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/umf-field-values.json',import.meta.url),JSON.stringify({umfSourceRevision:revision,producerBundleSha256:new Bun.CryptoHasher('sha256').update(bundle).digest('hex'),originalArtifacts:originals,sourceSha256:new Bun.CryptoHasher('sha256').update(sourceBytes).digest('hex'),loader:'bun/'+Bun.version,browser:browser.version(),...bunResult,qualification:'Actual existing UMF core 0.8 field checker with explicit verified reversible 0.7 upgrade receipts; original inputs retained. Complete checks for selected present string values only. Fixture property IDs are explicit local mappings, not accepted native IDs. Unknown nullability/document assertion and whole-record/key/relationship/native obligations remain unresolved. No blanket writable support, native acceptance, qualified validator isolation, source ACK or streaming authority.'},null,2)+'\n');
 console.log('Actual UMF value checks and explicit upgrade receipts agree in Bun/Chromium: '+bunResult.sourceChecks.length+' original source values.');
}finally{await browser?.close();server.stop(true);}
