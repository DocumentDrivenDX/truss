import {createRequire} from 'node:module';
const {chromium}=createRequire('/Users/erik/Projects/umf/package.json')('playwright');
const source='packages/postgresql/src/canonical-wire-tree.ts';
const build=await Bun.build({entrypoints:[source],target:'browser',format:'esm'});
if(!build.success)throw Error('Canonical handoff browser build failed');
const bundle=await build.outputs[0].text();
const server=Bun.serve({hostname:'127.0.0.1',port:0,fetch(req){return new URL(req.url).pathname==='/codec.js'?new Response(bundle,{headers:{'content-type':'text/javascript'}}):new Response('<!doctype html><title>Canonical wire handoff</title>')}});
const browser=await chromium.launch({headless:true});
try{
 const page=await browser.newPage();await page.goto('http://127.0.0.1:'+server.port);
 const observations=await page.evaluate(async()=>{
  const {prepareCanonicalWireTree}=await import('/codec.js');const encode=(s:string)=>new TextEncoder().encode(s);
  const original=' \n{"z":[null,true,"\\u0000😀"],"a":"9007199254740993"}\n';
  const expected={kind:'object',members:[{keyUtf8Hex:'7a',node:{kind:'array',items:[{kind:'null'},{kind:'boolean',value:true},{kind:'string',utf8Hex:'00f09f9880'}]}},{keyUtf8Hex:'61',node:{kind:'string',utf8Hex:'39303037313939323534373430393933'}}]};
  const bytes=encode(original),result=prepareCanonicalWireTree(bytes);
  if(JSON.stringify(JSON.parse(result.nativeTreeText))!==JSON.stringify(expected)||result.nativeTaskCount!=='17')throw Error('Independent tagged-tree oracle mismatch');
  const recovered=Uint8Array.from(result.originalUtf8Hex.match(/../g),(h:string)=>parseInt(h,16));
  if(new TextDecoder().decode(recovered)!==original)throw Error('Original wire changed');
  bytes.fill(0);if(new TextDecoder().decode(recovered)!==original)throw Error('Original wire snapshot lost');
  const cases=['{"x":1}','{"a":null,"\\u0061":true}','"\\ud800"',JSON.stringify(Array.from({length:4096},()=>[null,null,null]))];
  for(const text of cases){let refused=false;try{prepareCanonicalWireTree(encode(text))}catch{refused=true}if(!refused)throw Error('Invalid/capacity wire admitted');}
  return ['independent UTF-8 tagged-tree oracle','original whitespace and exact integer string custody','snapshot survives caller mutation','numeric-node refusal','decoded duplicate refusal','unpaired surrogate refusal','native task ceiling refusal'];
 });
 const hash=async(path:string)=>new Bun.CryptoHasher('sha256').update(await Bun.file(path).arrayBuffer()).digest('hex');
 const receipt={browser:browser.version(),sourceSha256:await hash(source),decoderSha256:await hash('packages/postgresql/src/acceptance-json.ts'),bundleSha256:new Bun.CryptoHasher('sha256').update(bundle).digest('hex'),observations,scope:'Actual Chromium original-wire to tagged native codec carrier only. No native encoding, semantic report admission, shared resource accounting or accepted publication.'};
 await Bun.write('docs/helix/04-build/evidence/design-audit/canonical-wire-browser.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
}finally{await browser.close();server.stop(true)}
