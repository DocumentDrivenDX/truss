/** Browser component qualification with original pinned compiler response. */
import {createRequire} from 'node:module';
import {createQueryEngine,WEFT_SOURCE} from '../packages/weft/src/index';
import {loadCompiler} from '../packages/weft-bun/src/index';
import request from '../tests/weft/fixtures/qualified-count.request.json';
const input={...request.target,modules:request.modules as any};
const compiler=await loadCompiler('/private/tmp/truss-weft-f05f2df');
const seed=await createQueryEngine(compiler,input);
const original=(await seed.compile('SELECT COUNT(*) AS total FROM Customer c')).originalResponse;
const build=await Bun.build({entrypoints:['packages/weft/src/index.ts'],target:'browser',format:'esm'});
if(!build.success||build.outputs.length!==1)throw Error('Browser module build failed');
const script=await build.outputs[0]!.text();
const server=Bun.serve({hostname:'127.0.0.1',port:0,fetch(req){
 if(new URL(req.url).pathname==='/wrapper.js')return new Response(script,{headers:{'content-type':'text/javascript'}});
 return new Response('<!doctype html><title>Truss browser admission probe</title>',{headers:{'content-type':'text/html'}});
}});
const {chromium}=createRequire('/Users/erik/Projects/umf/package.json')('playwright');
const browser=await chromium.launch({headless:true});
try{
 const page=await browser.newPage();
 await page.goto(`http://127.0.0.1:${server.port}`);
 const result=await page.evaluate(async({input,original}:any)=>{
  const module=await import('/wrapper.js');let acquired=0;const outcomes=[];
  const host={handlers:{'weft.output.positioned':{accepts:()=>true,async check(){}}},
   async withReadContext(){acquired++;throw Error('Unexpected native context')},async decode(){throw Error('Unexpected decode')}};
  const baseline=await module.createQueryEngine({compileJson:()=>original},input);
  const plan=await baseline.compile('SELECT COUNT(*) AS total FROM Customer c');
  if(!Object.isFrozen(plan.artifact))throw Error('Baseline artifact not frozen');
  for(const mutation of ['carrier','null-carrier','obligation','version']){
   const value=JSON.parse(original);
   if(mutation==='carrier')value.columns[0].carrierName='_weft_output_1';
   else if(mutation==='null-carrier')value.columns[0].carrierName=null;
   else if(mutation==='obligation')value.obligations.push({id:'weft.output.positioned',owner:'host',failureCode:'WFT-OBLIGATION',parameters:{profile:'weft-positioned-output/0.3.0'}});
   else {value.interfaceVersion='weft-compile/0.3.0';value.dialect='weft-sql/0.3.0'}
   const engine=await module.createQueryEngine({compileJson:()=>JSON.stringify(value)},input,host);
   let code:string|undefined;
   try{await engine.compile('SELECT COUNT(*) AS total FROM Customer c')}catch(error:any){code=error.code}
   const expected=mutation==='version'?'artifact_pin':'artifact_version';
   if(code!==expected)throw Error('Browser refusal mismatch: '+mutation);
   outcomes.push({mutation,code});
  }
  if(acquired!==0)throw Error('Native context acquired');
  return {baselineAdmitted:true,baselineFrozen:true,outcomes,nativeContexts:acquired};
 },{input,original});
 const receipt={scope:'Chromium wrapper admission component only; original compiler response replayed as test input, no browser Rust rebuild/native SQL/publication qualification',browserVersion:browser.version(),weftBuildRevision:WEFT_SOURCE,
  originalResponseSha256:new Bun.CryptoHasher('sha256').update(original).digest('hex'),browserBundleSha256:new Bun.CryptoHasher('sha256').update(script).digest('hex'),result,
  sourceSha256:Object.fromEntries(await Promise.all(['scripts/check-weft-admission-browser.ts','packages/weft/src/index.ts','tests/weft/fixtures/qualified-count.request.json'].map(async path=>[path,new Bun.CryptoHasher('sha256').update(await Bun.file(path).arrayBuffer()).digest('hex')])))};
 await Bun.write('docs/helix/04-build/evidence/design-audit/weft-v02-admission-browser.json',JSON.stringify(receipt,null,2)+'\n');
 console.log(JSON.stringify({browser:receipt.browserVersion,...result}));
}finally{await browser.close();server.stop(true)}
