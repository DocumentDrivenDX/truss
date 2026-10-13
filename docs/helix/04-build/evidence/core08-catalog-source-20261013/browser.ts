import {writeFile} from 'node:fs/promises';
const root='/private/tmp/truss-security-main-integration';const base=root+'/packages/python/src/truss/_umf_core08';
const expected=await Bun.file('/private/tmp/truss-core08-catalog-full-observations.json').json();const bundle=await Bun.file(base+'/producer.js').text();
const server=Bun.serve({hostname:'127.0.0.1',port:0,fetch(req){return new URL(req.url).pathname==='/producer.js'?new Response(bundle,{headers:{'content-type':'text/javascript'}}):new Response('<!doctype html><title>Original core0.8 packaged producer</title>')}});
const {chromium}=await import('/Users/erik/.codex/worktrees/security-main-integration/umf/node_modules/playwright/index.mjs');let browser;
try{
 browser=await chromium.launch({headless:true});const page=await browser.newPage();const requests:string[]=[];page.on('request',r=>requests.push(r.url()));await page.goto('http://127.0.0.1:'+server.port);
 const observations=await page.evaluate(async packet=>{const owner=await import('/producer.js');const source=owner.readDocument(packet.originalDocumentJson,'json');return packet.observations.map((original:any)=>({operation:original.operation,identity:original.identity,result:owner[original.operation](source,original.identity)}))},expected);
 if(JSON.stringify(observations)!==JSON.stringify(expected.observations))throw Error('Original full observation correspondence failed');
 if(requests.some(url=>!url.startsWith('http://127.0.0.1:'+server.port)))throw Error('External request');
 const receipt={browser:browser.version(),ownerBundleSha256:new Bun.CryptoHasher('sha256').update(bundle).digest('hex'),sourceSha256:expected.sourceSha256,observationCount:observations.length,observationsSha256:new Bun.CryptoHasher('sha256').update(JSON.stringify(observations)).digest('hex'),requests,scope:'Genuine packaged original owner executes every retained observation in Chromium and matches the Python/Bun source factory. No browser version of Bun receiver/Python capture or native profile admission.'};
 await writeFile('/private/tmp/truss-core08-packaged-browser.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({browser:receipt.browser,observations:observations.length}));
}finally{await browser?.close();server.stop(true)}
