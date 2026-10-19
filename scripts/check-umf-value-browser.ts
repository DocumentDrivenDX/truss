// SPDX-License-Identifier: MIT OR Apache-2.0
import {createRequire} from 'node:module';
import {loadCurrentNumericOwner} from '../packages/umf-bun/src/index';
const directory=process.env.TRUSS_UMF_NUMERIC_PRODUCER;if(!directory)throw Error('Original UMF value build required');
const producer=await loadCurrentNumericOwner(directory);
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
  const validation=owner.validateSemanticTypesDocument(model);
  if(!validation.valid||model.umf!=='0.10.0')throw Error('Current source required');
  const original=JSON.stringify(model),literals=JSON.stringify(values);
  const encoded=owner.encodeCoreKeyTupleBody(model,identity,values,validation);
  const refuses=(selected:unknown[])=>{try{owner.encodeCoreKeyTupleBody(model,identity,selected,validation);return false}catch{return true}};
  return {sourceValid:validation.valid,bytesHex:encoded.bytesHex,
   scaleRefused:refuses([{decimalToken:'12.3401'},values[1],values[2]]),
   precisionRefused:refuses([{decimalToken:'1000000000000000000'},values[1],values[2]]),
   widthRefused:refuses([values[0],values[1],{integerToken:'18446744073709551616'}]),
   orderRefused:refuses([values[1],values[0],values[2]]),
   originalUnchanged:JSON.stringify(model)===original,valuesUnchanged:JSON.stringify(values)===literals};
 },fixture);
 if(!observations.sourceValid||!observations.scaleRefused||!observations.precisionRefused||!observations.widthRefused||!observations.orderRefused
   ||!observations.originalUnchanged||!observations.valuesUnchanged||observations.bytesHex!==fixture.expectedHex)throw Error('Current browser canonical tuple mismatch');
 const receipt={sourceRevision:producer.sourceRevision,bundleSha256:producer.bundleSha256,fixtureSha256:hash(fixtureText),browser:browser.version(),observations,
  qualification:'Actual Chromium current 0.10 validation and shared UMFK1 body primitive; no public UMF 0.10 receipt verification claim. Exact source and value carriers retained; no native uniqueness/comparator/storage/resource/installed runtime qualification.'};
 await Bun.write('docs/helix/04-build/evidence/umf-current010-key-browser.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({browser:receipt.browser,tuple:observations.bytesHex}));
}finally{if(browser)await browser.close();server.stop(true)}
