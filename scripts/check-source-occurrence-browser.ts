/** Scoped portable source-index check; not semantic assertion admission. */
const {chromium}=await import(Bun.env.UMF_PLAYWRIGHT_MODULE ?? 'playwright');
import {createHash} from 'node:crypto';
const source='packages/postgresql/src/acceptance-json.ts';
const build=await Bun.build({entrypoints:[source],target:'browser',format:'esm'});if(!build.success)throw Error('build');
const js=await build.outputs[0]!.text();
const server=Bun.serve({hostname:'127.0.0.1',port:0,fetch:r=>new URL(r.url).pathname==='/index.js'?new Response(js,{headers:{'content-type':'text/javascript'}}):new Response('<!doctype html>')});
let browser;
try{
 browser=await chromium.launch({headless:true});const page=await browser.newPage();let external=0;
 await page.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(external++,r.abort()));
 await page.goto(`http://127.0.0.1:${server.port}`);
 const observed=await page.evaluate(async()=>{
  const m=await import('/index.js'),enc=new TextEncoder(),dec=new TextDecoder();
  const input=enc.encode('{"a/b":[9007199254740993,-0,"é"],"~":{}}'),i=m.indexSourceJsonOccurrences(input);input.fill(0);
  const values=i.occurrences.map((o:any,n:number)=>[o.pointer,o.kind,dec.decode(m.originalSourceOccurrenceBytes(i,n))]);
  let copied=false;try{m.originalSourceOccurrenceBytes({...i},0)}catch{copied=true}
  const refusals=['{"a":1,"a":2}','[01]','[1,]'].map(s=>{try{m.indexSourceJsonOccurrences(enc.encode(s));return false}catch{return true}});
  return {values,copied,refusals,hostGlobals:['Bun','process','Buffer'].filter(k=>k in globalThis)};
 });
 const expected=[['','object','{"a/b":[9007199254740993,-0,"é"],"~":{}}'],['/a~1b','array','[9007199254740993,-0,"é"]'],['/a~1b/0','number','9007199254740993'],['/a~1b/1','number','-0'],['/a~1b/2','string','"é"'],['/~0','object','{}']];
 if(JSON.stringify(observed.values)!==JSON.stringify(expected)||!observed.copied||observed.refusals.some(v=>!v)||observed.hostGlobals.length||external)throw Error('browser correspondence');
 const digest=async(p:string)=>createHash('sha256').update(new Uint8Array(await Bun.file(p).arrayBuffer())).digest('hex');
 const receipt={status:'passed',browser:browser.version(),observed,externalRequests:external,sourceDigests:Object.fromEntries(await Promise.all([source,'tests/source-occurrence-index.test.ts','scripts/check-source-occurrence-browser.ts'].map(async p=>[p,await digest(p)]))),scope:'Original JSON value indexing only; no semantic assertion coverage or native enforcement',runtimePremise:'Local Bun and Playwright installation; not hermetic'};
 console.log(JSON.stringify(receipt,null,2));
}finally{await browser?.close();server.stop(true)}
