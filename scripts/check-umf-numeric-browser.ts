import {createRequire} from 'node:module';
import {loadUmfNumericProducer} from '../packages/umf-bun/src/index';
const directory=process.env.TRUSS_UMF_NUMERIC_PRODUCER;if(!directory)throw Error('Original UMF numeric build required');
const producer=await loadUmfNumericProducer(directory);
const library=await Bun.file(directory+'/producer.js').text();
const hash=(value:string)=>new Bun.CryptoHasher('sha256').update(value).digest('hex');
if(hash(library)!==producer.bundleSha256)throw Error('Original browser source differs from registered bundle');
const corpusText=await Bun.file('tests/umf-fixtures/numeric-browser.json').text();const cases=JSON.parse(corpusText);
const require=createRequire(process.env.TRUSS_PLAYWRIGHT_PACKAGE??'/Users/erik/Projects/umf/package.json');
const {chromium}=require('playwright');
const server=Bun.serve({hostname:'127.0.0.1',port:0,fetch(req){
 return new URL(req.url).pathname==='/owner.js'?new Response(library,{headers:{'content-type':'text/javascript'}}):new Response('<!doctype html><title>Truss UMF numeric owner verification</title>');
}});
let browser;
try{
 browser=await chromium.launch({headless:true});const page=await browser.newPage();await page.goto('http://127.0.0.1:'+server.port);
 const observations=await page.evaluate(async cases=>{
  const path='/owner.js';const owner=await import(path);
  const context={document:{umf:'0.8.0',id:'truss-numeric-context',vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[{id:'amount',name:'amount',kind:'field',scalarType:'decimal',nullability:'required',cardinality:'one',facets:{precision:21,scale:3},extensions:{}}]}]},field:{module:'m',element:'amount'}};
  return cases.map(c=>{
   let value,error;
   try{
    switch(c.action){
     case 'admit-number':value=owner.admitJavascriptNumber(Number(c.numberToken),c.family);break;
     case 'exact-decimal':value=owner.exactDecimal(c.token,c.fieldContext?context:undefined);break;
     case 'to-number':value=owner.numericToNumberLossless(c.literal);break;
     case 'from-bigint':value=owner.integerFromBigInt(BigInt(c.token));break;
     case 'to-bigint':value=owner.integerToBigInt(c.literal).toString();break;
     default:throw Error('Unknown corpus action');
    }
   }catch(e){error=e.code??'unclassified';}
   return {name:c.name,...(error?{error}:{value})};
  });
 },cases);
 for(let i=0;i<cases.length;i++){
  const expected=cases[i].error?{name:cases[i].name,error:cases[i].error}:{name:cases[i].name,value:cases[i].expected};
  if(JSON.stringify(observations[i])!==JSON.stringify(expected))throw Error('Original browser owner mismatch: '+cases[i].name);
 }
 const receipt={sourceRevision:producer.sourceRevision,bundleSha256:producer.bundleSha256,corpusSha256:hash(corpusText),browser:browser.version(),observations,
  qualification:'Actual Chromium executes the isolated committed UMF numeric producer. Explicit JavaScript number input fixtures and safe number outputs are conveniences; exact carriers remain strings/bigint. No native codec, database, Record/dataset, containment, resource or installed runtime qualification.'};
 await Bun.write('docs/helix/04-build/evidence/umf-numeric-browser.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({browser:receipt.browser,cases:observations.length}));
}finally{if(browser)await browser.close();server.stop(true)}
