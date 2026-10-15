/** Real Chromium worker/IndexedDB test. Supply a package.json resolving playwright. */
import {createRequire} from 'node:module';
import {join} from 'node:path';
const {chromium}=createRequire(Bun.argv[2]??import.meta.path)('playwright');
const built=await Bun.build({entrypoints:[new URL('./test-worker.ts',import.meta.url).pathname],target:'browser',
  plugins:[{name:'original-pglite',setup(build){build.onResolve({filter:/^@electric-sql\/pglite$/},()=>({path:'/pglite/index.js',external:true}));}}]});
if(!built.success)throw Error(String(built.logs));
const dist=new URL('./node_modules/@electric-sql/pglite/dist/',import.meta.url).pathname;
const server=Bun.serve({hostname:'127.0.0.1',port:0,async fetch(request){
  const path=new URL(request.url).pathname;
  if(path==='/')return new Response('<!doctype html><title>Truss lifecycle</title>',{headers:{'content-type':'text/html'}});
  if(path==='/worker.js')return new Response(await built.outputs[0]!.text(),{headers:{'content-type':'text/javascript'}});
  if(path==='/layout.sql')return new Response(Bun.file(new URL('../python/src/truss/_catalog_runtime/layout.sql',import.meta.url)));
  if(path.startsWith('/pglite/')&&!path.includes('..'))return new Response(Bun.file(join(dist,path.slice(8))));
  return new Response('Missing',{status:404});
}});
const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext();
  const a=await context.newPage(),b=await context.newPage();
  const origin=`http://127.0.0.1:${server.port}`;
  async function prepare(page:any){await page.goto(origin);await page.evaluate(()=>{
    (window as any).worker=new Worker('/worker.js',{type:'module'});
    (window as any).call=(data:any)=>new Promise((resolve,reject)=>{
      const worker=(window as any).worker;worker.onmessage=(event:any)=>resolve(event.data);worker.onerror=reject;worker.postMessage(data);
    });
  });}
  const call=(page:any,data:any)=>page.evaluate((data:any)=>(window as any).call(data),data);
  await prepare(a);await prepare(b);
  const first=await call(a,{command:'open',name:'lifecycle-basic'});
  if(first.outcome!=='available')throw Error(JSON.stringify(first));
  const forged=await call(a,{command:'forged'});
  if(forged.outcome!=='refused')throw Error(JSON.stringify(forged));
  const second=await call(b,{command:'open',name:'lifecycle-basic'});
  if(second.outcome!=='unavailable'||second.reason!=='store_in_use')throw Error(JSON.stringify(second));
  const closed=await call(a,{command:'close'});
  if(closed.outcome!=='closed')throw Error(JSON.stringify(closed));
  const takeover=await call(b,{command:'open',name:'lifecycle-basic'});
  if(takeover.outcome!=='available'||JSON.stringify(first.info)!==JSON.stringify(takeover.info))throw Error(JSON.stringify(takeover));
  await call(b,{command:'close'});
  await prepare(a);
  const reopened=await call(a,{command:'open',name:'lifecycle-basic'});
  if(reopened.outcome!=='available'||JSON.stringify(first.info)!==JSON.stringify(reopened.info))throw Error(JSON.stringify(reopened));
  await call(a,{command:'close'});
  const receipt={scope:'Chromium worker lifecycle and IndexedDB reopen only',chromium:browser.version(),first,forged,second,takeover,reopened,
    actionExecution:false,selectionReadGrant:false,crashRecovery:false};
  const encoded=JSON.stringify(receipt,null,2)+'\n';if(Bun.argv[3])await Bun.write(Bun.argv[3],encoded);console.log(encoded);
}finally{await browser.close();server.stop(true);}
