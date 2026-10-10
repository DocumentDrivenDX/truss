import {createRequire} from 'node:module';
import {loadUmfValueProducer} from '../packages/umf-bun/src/index';
const directory=process.env.TRUSS_UMF_VALUE_PRODUCER;if(!directory)throw Error('Original UMF value build required');
const producer=await loadUmfValueProducer(directory);
const library=await Bun.file(directory+'/producer.js').text();
const hash=(v:string)=>new Bun.CryptoHasher('sha256').update(v).digest('hex');
if(hash(library)!==producer.bundleSha256)throw Error('Original browser bundle mismatch');
const fixtureText=await Bun.file('tests/umf-fixtures/value-key.json').text();const fixture=JSON.parse(fixtureText);
const require=createRequire(process.env.TRUSS_PLAYWRIGHT_PACKAGE??'/Users/erik/Projects/umf/package.json');const {chromium}=require('playwright');
const server=Bun.serve({hostname:'127.0.0.1',port:0,fetch(req){return new URL(req.url).pathname==='/owner.js'?new Response(library,{headers:{'content-type':'text/javascript'}}):new Response('<!doctype html><title>Truss UMF value owner verification</title>')}});
let browser;
try{
 browser=await chromium.launch({headless:true});const page=await browser.newPage();await page.goto('http://127.0.0.1:'+server.port);
 const observations=await page.evaluate(async fixture=>{
  const path='/owner.js';const owner=await import(path);const {model,identity,values}=fixture;
  const valid=owner.validateCoreFieldValue(model,{module:'m',element:'amount'},values[0]);
  const scale=owner.validateCoreFieldValue(model,{module:'m',element:'amount'},{decimalToken:'12.3401'});
  const width=owner.validateCoreFieldValue(model,{module:'m',element:'count'},{integerToken:'18446744073709551616'});
  const receipt=owner.encodeCoreKeyTuple(model,identity,values);owner.verifyCoreKeyTuple(receipt,model);
  let forgedRefused=false,staleRefused=false;
  try{owner.verifyCoreKeyTuple({...receipt,bytesHex:'00'},model)}catch{forgedRefused=true}
  try{owner.verifyCoreKeyTuple(receipt,{...model,id:'changed'})}catch{staleRefused=true}
  return {valid,scale,width,receipt,forgedRefused,staleRefused};
 },fixture);
 if(!observations.valid.valid||!observations.valid.complete||observations.scale.valid||observations.width.valid||!observations.forgedRefused||!observations.staleRefused
     ||observations.receipt.bytesHex!==fixture.expectedHex||observations.receipt.version!=='3.0.0'||JSON.stringify(observations.receipt.values)!==JSON.stringify(fixture.values))throw Error('Original browser value/tuple mismatch');
 const receipt={sourceRevision:producer.sourceRevision,bundleSha256:producer.bundleSha256,fixtureSha256:hash(fixtureText),browser:browser.version(),observations,
  qualification:'Actual Chromium original current-core Field validation and ordered UMFK1 v3 tuple encoding/verification. Exact source and value carriers retained; no native uniqueness/comparator/storage/resource/installed runtime qualification.'};
 await Bun.write('docs/helix/04-build/evidence/umf-value-browser.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({browser:receipt.browser,tuple:observations.receipt.version}));
}finally{if(browser)await browser.close();server.stop(true)}
