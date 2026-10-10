import {createRequire} from 'node:module';
const build=process.env.TRUSS_WEFT_WASM;if(!build)throw Error('TRUSS_WEFT_WASM directory required');
const require=createRequire(process.env.TRUSS_PLAYWRIGHT_PACKAGE ?? '/Users/erik/Projects/umf/package.json');
const {chromium}=require('playwright');
const bundled=await Bun.build({entrypoints:['packages/weft/src/index.ts'],target:'browser',format:'esm'});
if(!bundled.success)throw Error('Portable build failed');const library=await bundled.outputs[0].text();
const request=await Bun.file('tests/weft/fixtures/qualified-count.request.json').json();
const server=Bun.serve({hostname:'127.0.0.1',port:0,fetch(req){const path=new URL(req.url).pathname;
 if(path==='/truss.js')return new Response(library,{headers:{'content-type':'text/javascript'}});
 if(path==='/weft_wasm.js')return new Response(Bun.file(build+'/weft_wasm.js'),{headers:{'content-type':'text/javascript'}});
 if(path==='/weft_wasm_bg.wasm')return new Response(Bun.file(build+'/weft_wasm_bg.wasm'),{headers:{'content-type':'application/wasm'}});
 return new Response('<!doctype html><title>Truss Weft integration</title>');}});
const browser=await chromium.launch({headless:true});
try {
 const page=await browser.newPage();await page.goto('http://127.0.0.1:'+server.port);
 const results=await page.evaluate(async request=>{
  const wasmPath='/weft_wasm.js',libraryPath='/truss.js';const wasm=await import(wasmPath);await wasm.default();const truss=await import(libraryPath);
  const engine=await truss.createQueryEngine({compileJson:wasm.compile_json},{...request.target,modules:request.modules});
  const sql=['SELECT COUNT(*) AS total FROM Customer c','SELECT SUM(o.total) AS total FROM Orders o','SELECT c.* FROM Customer c ORDER BY c.id LIMIT 10'];
  const out=[];for(const query of sql){const p=await engine.compile(query);out.push({query,response:p.originalResponse});
   try{await engine.execute(p);throw Error('Unavailable runtime executed')}catch(e){if(e.code!=='runtime_unavailable')throw e}}
  engine.dispose();try{await engine.compile(sql[0]);throw Error('Disposed engine compiled')}catch(e){if(e.code!=='disposed')throw e}
  return out;
 },request);
 const receipt={sourceRevision:'2744531735c2a771fbe7ed24a7f67e3afc851b25',browser:browser.version(),cases:results,disposedCompilationRefused:true,
  qualification:'Real Chromium WASM compiler plus portable Truss API. Synthetic upstream binding only; no native execution/installed Truss qualification.'};
 await Bun.write('docs/helix/04-build/evidence/weft-integration-browser.json',JSON.stringify(receipt,null,2)+'\n');
 console.log(JSON.stringify({browser:receipt.browser,compiled:results.length,nativeHost:'unavailable'}));
} finally {await browser.close();server.stop(true)}
