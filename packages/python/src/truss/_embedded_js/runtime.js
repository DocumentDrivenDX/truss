// An isolated virtual host for the unchanged packaged owner modules.
// No filesystem, network, environment, or executable access is exposed.
class TextEncoder {
 encode(value='') {const out=[];for(const c of String(value)){let p=c.codePointAt(0);if(p>=0xd800&&p<=0xdfff)p=0xfffd;
 if(p<128)out.push(p);else if(p<2048)out.push(192|(p>>6),128|(p&63));else if(p<65536)out.push(224|(p>>12),128|((p>>6)&63),128|(p&63));else out.push(240|(p>>18),128|((p>>12)&63),128|((p>>6)&63),128|(p&63));}return Uint8Array.from(out);}
 get encoding(){return 'utf-8';}
}
class TextDecoder {
 constructor(label='utf-8',options={}) {this.label=label.toLowerCase();if(!['utf-8','utf8','latin1','utf-16le','utf-16be'].includes(this.label))throw Error('Unsupported encoding');this.fatal=!!options.fatal;this.ignoreBOM=!!options.ignoreBOM;}
 decode(input=new Uint8Array(),options={}){if(options.stream)throw Error('Streaming UTF-8 unsupported');const b=new Uint8Array(input.buffer||input,input.byteOffset||0,input.byteLength);let s='';
 if(this.label==='latin1'){const table=[8364,129,8218,402,8222,8230,8224,8225,710,8240,352,8249,338,141,381,143,144,8216,8217,8220,8221,8226,8211,8212,732,8482,353,8250,339,157,382,376];return Array.from(b,x=>String.fromCharCode(x>=128&&x<160?table[x-128]:x)).join('');}
 if(this.label.startsWith('utf-16')){const le=this.label==='utf-16le';for(let i=0;i<b.length;i+=2){if(i+1>=b.length){if(this.fatal)throw TypeError('Invalid UTF-16');s+='\ufffd';break;}let x=le?b[i]|b[i+1]<<8:b[i]<<8|b[i+1];if(x>=0xd800&&x<=0xdbff){const y=i+3<b.length?(le?b[i+2]|b[i+3]<<8:b[i+2]<<8|b[i+3]):-1;if(y>=0xdc00&&y<=0xdfff){s+=String.fromCharCode(x,y);i+=2;continue;}if(this.fatal)throw TypeError('Invalid UTF-16');s+='\ufffd';}else if(x>=0xdc00&&x<=0xdfff){if(this.fatal)throw TypeError('Invalid UTF-16');s+='\ufffd';}else s+=String.fromCharCode(x);}return !this.ignoreBOM&&s.charCodeAt(0)===0xfeff?s.slice(1):s;}
 for(let i=0;i<b.length;){const start=i,x=b[i++];let p=x,n=0,min=0;
 if(x>=0xc2&&x<=0xdf){p=x&31;n=1;min=128;}else if(x>=0xe0&&x<=0xef){p=x&15;n=2;min=2048;}else if(x>=0xf0&&x<=0xf4){p=x&7;n=3;min=65536;}else if(x>=128){if(this.fatal)throw TypeError('Invalid UTF-8');s+='\ufffd';continue;}
 let valid=true;for(let j=0;j<n;j++){const y=b[i];if(y===undefined||y<128||y>191||(j===0&&((x===0xe0&&y<160)||(x===0xed&&y>=160)||(x===0xf0&&y<144)||(x===0xf4&&y>=144)))){valid=false;break;}p=(p<<6)|(y&63);i++;}
 if(!valid||p<min||p>0x10ffff||(p>=0xd800&&p<=0xdfff)){if(this.fatal)throw TypeError('Invalid UTF-8');s+='\ufffd';continue;}s+=String.fromCodePoint(p);
 }return !this.ignoreBOM&&s.charCodeAt(0)===0xfeff?s.slice(1):s;}
 get encoding(){return 'utf-8';}
}
Object.assign(globalThis,{TextEncoder,TextDecoder});
function __install(archive, entry, inputHex, args, extra) {
 const modules=archive.modules,sources=archive.sources,cache=Object.create(null);
 const normalize=p=>{if(p instanceof URL)p=p.pathname;p=String(p).replace(/^file:\/\/\/truss\//,'/truss/');const parts=[];for(const part of p.split('/')){if(part==='..'){if(!parts.length)throw Error('Virtual path escape');parts.pop();}else if(part&&part!=='.')parts.push(part);}return '/'+parts.join('/');};
 const path=p=>normalize(p).replace(/^\/truss\//,'');
 const raw=p=>{const name=path(p);if(extra&&Object.hasOwn(extra,name))return Buffer.from(extra[name],'hex');if(!Object.hasOwn(sources,name))throw Error('Unpackaged asset '+name);return Buffer.from(sources[name],'base64');};
 const hash=()=>{let chunks=[];return {update(v,encoding){chunks.push(typeof v==='string'?Buffer.from(v,encoding):Buffer.from(v));return this;},digest(encoding){const out=Buffer.from(__sha256(Buffer.concat(chunks)));return encoding?out.toString(encoding):out;}};};
 const process={env:Object.freeze({}),exitCode:0,emitWarning(){},stdout:{write:v=>write(v)},stderr:{write:v=>error(v)}};
 let output=[],errors=[],written=0,reply=null;const maximum=64*1024*1024;
 function write(v){const b=Buffer.from(v);written+=b.length;if(written>maximum)throw Error('Output capacity');output.push(b);if(reply){const r=reply;reply=null;Promise.resolve().then(()=>r.resolve(Buffer.concat(output).toString('hex')));}return b.length;}
 function error(v){const b=Buffer.from(v);if(errors.reduce((n,b)=>n+b.length,0)+b.length>65536)throw Error('Error capacity');errors.push(b);if(reply){const r=reply;reply=null;r.reject(Error(b.toString('utf8')));}return b.length;}
 const stdin=Buffer.from(inputHex,'hex');let waiting=null,queued=[];
 const stream={ [Symbol.asyncIterator](){return this;},next(){if(queued.length)return Promise.resolve({value:queued.shift(),done:false});return new Promise(resolve=>{waiting=resolve;});}};
 const Bun={stdin:{text:async()=>stdin.toString('utf8'),json:async()=>JSON.parse(stdin.toString('utf8')),arrayBuffer:async()=>Uint8Array.from(stdin).buffer,stream:()=>stream},
 stdout:{},stderr:{},argv:['embedded',entry,...args],CryptoHasher:class{constructor(algorithm){if(algorithm!=='sha256')throw Error('Hash algorithm');this.h=hash();}update(v){this.h.update(v);return this;}digest(encoding){return this.h.digest(encoding);}},
 file:p=>({text:async()=>raw(p).toString('utf8'),json:async()=>JSON.parse(raw(p).toString('utf8')),arrayBuffer:async()=>Uint8Array.from(raw(p)).buffer}),
 write:async(target,v)=>target===Bun.stdout?write(v):target===Bun.stderr?error(v):Promise.reject(Error('Virtual write refused'))};
 const shims={crypto:{createHash:algorithm=>{if(algorithm!=='sha256')throw Error('Hash algorithm');return hash();}},path:{resolve:(...parts)=>normalize(parts.reduce((a,p)=>String(p).startsWith('/')?String(p):a+'/'+p,'/truss'))},
 'fs/promises':{readFile:async(p,encoding)=>encoding?raw(p).toString(encoding):raw(p)},module:{createRequire:parent=>makeRequire(path(parent))},buffer:{Buffer},process};
 function resolve(spec,parent){spec=String(spec).replace(/^node:/,'');if(Object.hasOwn(shims,spec))return spec;
 const base=parent.slice(0,parent.lastIndexOf('/'));const candidates=[];
 if(spec.startsWith('.')||spec.startsWith('/')||spec.startsWith('file:'))candidates.push(path(spec.startsWith('.')?'/truss/'+base+'/'+spec:spec));
 else {let d=base;while(d){candidates.push(d+'/node_modules/'+spec);d=d.slice(0,d.lastIndexOf('/'));}candidates.push('node_modules/'+spec);}
 for(const c of candidates)for(const suffix of ['','.js','.mjs','.json','/index.js'])if(Object.hasOwn(sources,c+suffix))return c+suffix;
 throw Error('Unpackaged module '+spec+' from '+parent);}
 function makeRequire(parent){return spec=>load(resolve(spec,parent));}
 function load(name){if(Object.hasOwn(shims,name))return shims[name];if(cache[name])return cache[name].exports;
 const module={exports:{}};cache[name]=module;if(name.endsWith('.json'))module.exports=JSON.parse(raw('/truss/'+name).toString('utf8'));
 else new Function('require','module','exports','__filename','__dirname','__main',modules[name])(makeRequire(name),module,module.exports,'/truss/'+name,'/truss/'+name.slice(0,name.lastIndexOf('/')),false);
 return module.exports;}
 Object.assign(globalThis,{Bun,process,console:{log:(...v)=>write(v.join(' ')+'\n'),error:(...v)=>error(v.join(' ')+'\n')}});
 const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
 const module={exports:{}};
 const run=new AsyncFunction('require','module','exports','__filename','__dirname','__main',modules[entry]);
 let failure=null,finished=false;
 const completion=run(makeRequire(entry),module,module.exports,'/truss/'+entry,'/truss/'+entry.slice(0,entry.lastIndexOf('/')),true).then(()=>{finished=true;},e=>{failure=String(e.stack||e);finished=true;});
 globalThis.__result=async()=>{await completion;if(failure)error(failure);return JSON.stringify({code:failure?1:process.exitCode,stdout:Buffer.concat(output).toString('hex'),stderr:Buffer.concat(errors).toString('hex')});};
 globalThis.__feed=hex=>{output=[];errors=[];written=0;if(finished||reply)throw Error(failure||'Session closed or concurrent exchange');
 const result=new Promise((resolve,reject)=>{reply={resolve,reject};});
 const chunk=Buffer.from(hex,'hex');if(waiting){const r=waiting;waiting=null;r({value:chunk,done:false});}else queued.push(chunk);
 return result;};
}
