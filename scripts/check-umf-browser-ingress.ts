/** Real browser qualification for exact ingress + original UMF semantic producer. */
import {createRequire} from 'node:module';
import {readFile,writeFile,mkdtemp} from 'node:fs/promises';
import {join} from 'node:path';
const umfRoot=process.argv[2],examples=process.argv[3];if(!umfRoot||!examples)throw Error('Pinned UMF checkout and examples required');
const require=createRequire(umfRoot+'/package.json');const {chromium}=require('playwright');
const expected=JSON.parse(await readFile(new URL('../docs/helix/04-build/evidence/inert-assembly/umf-semantic-ingress.json',import.meta.url),'utf8'));
const rev=Bun.spawnSync(['git','rev-parse','HEAD'],{cwd:umfRoot});const status=Bun.spawnSync(['git','status','--porcelain'],{cwd:umfRoot});
if(rev.exitCode||status.exitCode||new TextDecoder().decode(rev.stdout).trim()!==expected.umfSourceRevision||status.stdout.length)throw Error('Exact clean UMF source required');
const temporary=await mkdtemp('/private/tmp/truss-umf-browser-');const entry=join(temporary,'producer.ts');
await writeFile(entry,`export {readDocument} from ${JSON.stringify(umfRoot+'/src/model/document.ts')};\nexport {validateDocument} from ${JSON.stringify(umfRoot+'/src/validation/document.ts')};\n`);
await writeFile(entry,`export {inspectCoreNullability} from ${JSON.stringify(umfRoot+'/src/model/nullability.ts')};\nexport {inspectCoreCardinality} from ${JSON.stringify(umfRoot+'/src/model/cardinality.ts')};\nexport {inspectCoreFacets} from ${JSON.stringify(umfRoot+'/src/model/facets.ts')};\nexport {inspectCoreKeys} from ${JSON.stringify(umfRoot+'/src/model/keys.ts')};\nexport {inspectCoreRelationships} from ${JSON.stringify(umfRoot+'/src/model/relationships.ts')};\n`,{flag:'a'});
const built=await Bun.build({entrypoints:[entry],outdir:temporary,target:'browser',format:'esm',naming:'producer.js'});if(!built.success)throw Error('Original producer build failed');
const producer=await readFile(join(temporary,'producer.js'));const truss=await readFile(new URL('../packages/postgresql/dist/index.js',import.meta.url));
const hash=(bytes:Uint8Array)=>new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
if(hash(producer)!==expected.producerBundleSha256)throw Error('Producer bundle changed');
const artifacts=await Promise.all(expected.results.map(async(result:any)=>{const bytes=await readFile(examples+'/'+result.identity);if(hash(bytes)!==result.sha256)throw Error('Original example changed');return {identity:result.identity,bytesBase64:bytes.toString('base64'),sha256:result.sha256};}));
const server=Bun.serve({hostname:'127.0.0.1',port:0,fetch(request){const path=new URL(request.url).pathname;return path==='/truss.js'?new Response(truss,{headers:{'content-type':'text/javascript'}}):path==='/producer.js'?new Response(producer,{headers:{'content-type':'text/javascript'}}):new Response('<!doctype html><title>Original UMF ingress</title>');}});
let browser;
try{
 browser=await chromium.launch({headless:true,...(process.env.UMF_CHROMIUM_PATH?{executablePath:process.env.UMF_CHROMIUM_PATH}:{})});
 const page=await browser.newPage();await page.goto('http://127.0.0.1:'+server.port);
 const inventory=JSON.parse(await readFile(new URL('../docs/helix/04-build/evidence/inert-assembly/umf-check-inventory.json',import.meta.url),'utf8'));
 const result=await page.evaluate(async({artifacts,expected,inventory}:any)=>{
  const trussPath='/truss.js',producerPath='/producer.js';const t=await import(trussPath),u=await import(producerPath);
  const limits={maxArtifacts:4,maxSingleBytes:65536,maxTotalBytes:262144};
  const verified=await t.verifyExactArtifacts(artifacts,limits);
  if(JSON.stringify(verified)!==JSON.stringify(artifacts))throw Error('Original bytes changed');
  const observations=verified.map((artifact:any)=>{
   const bytes=Uint8Array.from(atob(artifact.bytesBase64),char=>char.charCodeAt(0));const document=u.readDocument(new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes),'json');
   if(artifact.identity==='schema-unknown.umf.json'&&document['x-future-assertion']?.meaning!=='retained until supported')throw Error('Unknown assertion lost');
   const originalInventory=inventory.inventories.find((item:any)=>item.identity===artifact.identity);
   for(const entry of originalInventory.entries)if(JSON.stringify(u[entry.producer](document,entry.originalResult.identity))!==JSON.stringify(entry.originalResult))throw Error('Original inspection changed across runtimes');
   return {identity:artifact.identity,validation:u.validateDocument(document),originalInspectionsVerified:originalInventory.entries.length};
  });
  for(let i=0;i<observations.length;i++)if(JSON.stringify(observations[i].validation)!==JSON.stringify(expected.results[i].originalValidation))throw Error('Original diagnostics changed across runtimes');
  for(const [input,bounds] of [[[{...artifacts[0],sha256:'0'.repeat(64)}],limits],[artifacts,{...limits,maxTotalBytes:1}],[[{identity:'bad',bytesBase64:'YR==',sha256:artifacts[0].sha256}],limits]] as any){
   let refused=false;try{await t.verifyExactArtifacts(input,bounds);}catch{refused=true;}if(!refused)throw Error('Invalid ingress admitted');
  }
  if('process' in globalThis||'Buffer' in globalThis)throw Error('Host globals present');
  return {originalArtifactsPreserved:true,originalDiagnosticsPreserved:true,unknownAssertionPreserved:true,corruptDigestRefused:true,sharedByteOverflowRefused:true,noncanonicalBase64Refused:true,nodeGlobalsAbsent:true,observations};
 },{artifacts,expected,inventory});
 await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/umf-browser-ingress.json',import.meta.url),JSON.stringify({...result,browser:browser.version(),umfSourceRevision:expected.umfSourceRevision,producerBundleSha256:hash(producer),trussBundleSha256:hash(truss),qualification:'Real Chromium original UMF examples through built portable Truss integrity ingress and exact pinned UMF producer. All original validity/completeness/diagnostics agree with Bun; no native acceptance, installation, qualified validator isolation or source stream authority.'},null,2)+'\n');
 console.log('Real Chromium exact UMF ingress and original diagnostics passed: '+browser.version());
}finally{await browser?.close();server.stop(true);}
