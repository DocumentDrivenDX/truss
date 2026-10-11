/** Portable custody/codec execution only; no installed backend admission. */
const {chromium}=await import(Bun.env.UMF_PLAYWRIGHT_MODULE??'playwright');
const sources=['original-byte-custody','acceptance-json','canonical-wire-tree','asserted-origin-map','captured-origin-context'].map(n=>'packages/postgresql/src/'+n+'.ts');
const build=await Bun.build({entrypoints:sources,target:'browser',format:'esm',splitting:true});if(!build.success)throw Error('browser build');
const outputs=new Map(await Promise.all(build.outputs.map(async o=>[o.path.split('/').at(-1)!,await o.text()] as const)));
const headers={'Cross-Origin-Opener-Policy':'same-origin','Cross-Origin-Embedder-Policy':'require-corp'};
const server=Bun.serve({hostname:'127.0.0.1',port:0,fetch:r=>{const code=outputs.get(new URL(r.url).pathname.slice(1));return code===undefined?new Response('<!doctype html>',{headers}):new Response(code,{headers:{...headers,'Content-Type':'text/javascript'}})}});
let browser;
try{
 browser=await chromium.launch({headless:true});const page=await browser.newPage();let external=0;
 await page.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(external++,r.abort()));await page.goto('http://127.0.0.1:'+server.port);
 const observed=await page.evaluate(async()=>{
  const load=(name:string)=>import('/'+name+'.js');const {copyOriginalByteCustody}=await load('original-byte-custody'),{prepareCanonicalWireTree}=await load('canonical-wire-tree'),{indexSourceJsonOccurrences,originalSourceOccurrenceBytes}=await load('acceptance-json'),{mapAssertedOrigin}=await load('asserted-origin-map'),{decodeCapturedOriginContext}=await load('captured-origin-context');
  const encode=(s:string)=>new TextEncoder().encode(s),hex=(b:Uint8Array)=>Array.from(b,n=>n.toString(16).padStart(2,'0')).join(''),checks:{id:string;expected:unknown;observed:unknown}[]=[];
  const check=(id:string,observed:unknown,expected:unknown)=>{if(JSON.stringify(observed)!==JSON.stringify(expected))throw Error(id);checks.push({id,expected,observed})};
  const context={interfaceVersion:'truss-native-operation-context/0.3',xid:'1',ordinal:'0',sessionUser:'login',actingUser:'reader',database:'fixture',backendPid:'1',actorRoleOid:'2',sessionRoleOid:'3',assertedOriginUtf8Hex:'6e756c6c',assertedOriginCaptureProfileHex:'01'};
  const routes=[['tree','{"flag":true}',prepareCanonicalWireTree],['origin','{"flag":true}',(b:Uint8Array)=>mapAssertedOrigin(b,'reader')],['context',JSON.stringify(context),(b:Uint8Array)=>{const r=decodeCapturedOriginContext(b);return {...r,originalUtf8Hex:r.originalContextUtf8Hex}}]] as const;
  for(const [name,source,prepare] of routes){const original=encode(source);let calls=0;const callback=()=>{calls++;throw Error('hook')};
   for(const key of ['length','buffer','slice','constructor'])Object.defineProperty(original,key,{get:callback});Object.defineProperty(original,Symbol.iterator,{value:callback});Object.defineProperty(original,Symbol.toStringTag,{get:callback});
   const result=prepare(original);check(name+' exact source',result.originalUtf8Hex,hex(encode(source)));check(name+' zero callbacks',calls,0);original.fill(0);check(name+' immutable result',result.originalUtf8Hex,hex(encode(source)));
   const shared=new Uint8Array(new SharedArrayBuffer(encode(source).length));shared.set(encode(source));Object.defineProperty(shared,'buffer',{get:callback});let refusal=false;try{prepare(shared)}catch{refusal=true}check(name+' actual shared refusal',refusal,true);check(name+' shared callback count',calls,0);
  }
  const tree=prepareCanonicalWireTree(encode('{"z":"\\u0000é","a":[true,null]}'));check('independent tree',JSON.parse(tree.nativeTreeText),{kind:'object',members:[{keyUtf8Hex:'7a',node:{kind:'string',utf8Hex:'00c3a9'}},{keyUtf8Hex:'61',node:{kind:'array',items:[{kind:'boolean',value:true},{kind:'null'}]}}]});
  const i=indexSourceJsonOccurrences(encode('{"n":9007199254740993}'));check('original numeric lexeme',new TextDecoder().decode(originalSourceOccurrenceBytes(i,1)),'9007199254740993');
  const iframe=document.createElement('iframe');document.body.append(iframe);const foreign=new iframe.contentWindow!.Uint8Array([110,117,108,108]);check('cross-realm ordinary source',prepareCanonicalWireTree(foreign).originalUtf8Hex,'6e756c6c');iframe.remove();
  const detached=encode('null');structuredClone(detached.buffer,{transfer:[detached.buffer]});let detachedRefused=false;try{copyOriginalByteCustody(detached,true)}catch{detachedRefused=true}check('detached carrier refusal',detachedRefused,true);
  check('exact byte cap',copyOriginalByteCustody(new Uint8Array(1048576)).length,1048576);let capRefused=false;try{copyOriginalByteCustody(new Uint8Array(1048577))}catch{capRefused=true}check('over byte cap',capRefused,true);
  const hostGlobals=['Bun','process','Buffer'].filter(n=>n in globalThis);check('no host globals',hostGlobals,[]);return {checks,crossOriginIsolated,hostGlobals};
 });
 if(external||!observed.crossOriginIsolated)throw Error('browser isolation');
 const digest=async(p:string)=>new Bun.CryptoHasher('sha256').update(await Bun.file(p).arrayBuffer()).digest('hex');
 const receipt={status:'passed',browser:browser.version(),...observed,externalRequests:external,sourceDigests:Object.fromEntries(await Promise.all([...sources,'scripts/check-original-byte-browser.ts'].map(async p=>[p,await digest(p)]))),bundleDigests:Object.fromEntries([...outputs].map(([name,text])=>[name,new Bun.CryptoHasher('sha256').update(text).digest('hex')])),scope:'Actual Chromium portable byte custody, JSON scanner, codec and origin/context mapping only; no native backend admission'};
 await Bun.write(Bun.env.TRUSS_CANONICAL_BROWSER_EVIDENCE!,JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({status:'passed',checks:observed.checks.length,browser:receipt.browser}));
}finally{await browser?.close();server.stop(true)}
