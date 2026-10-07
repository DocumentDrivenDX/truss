/** Independent audit encoder/WebCrypto; no production/native model qualification. */
const {default:Ajv}=await import(process.argv[2]);
const root='docs/helix/02-design/contracts/';
const validate=new Ajv({strict:true}).addSchema(await Bun.file(root+'acceptance-input-v0.1.schema.json').json()).compile(await Bun.file(root+'bootstrap-bundle-v0.1.schema.json').json());
const fixture=await Bun.file(root+'bindings/truss-bootstrap-bundle-v0.1.vectors.json').json();
const utf8=new TextEncoder(),hex=(b:Uint8Array)=>Array.from(b,x=>x.toString(16).padStart(2,'0')).join('');
const text=(s:string)=>'"'+Array.from(s,c=>c==='"'?'\\"':c==='\\'?'\\\\':c.codePointAt(0)!<32?'\\u'+c.codePointAt(0)!.toString(16).padStart(4,'0'):c).join('')+'"';
const compare=(a:string,b:string)=>{const x=utf8.encode(a),y=utf8.encode(b);for(let i=0;i<Math.min(x.length,y.length);i++)if(x[i]!==y[i])return x[i]-y[i];return x.length-y.length;};
const encode=(v:any):string=>typeof v==='string'?text(v):Array.isArray(v)?'['+v.map(encode).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort(compare).map(k=>text(k)+':'+encode(v[k])).join(',')+'}':(()=>{throw Error('unexpected fixture scalar');})();
const digest=async(s:string)=>hex(new Uint8Array(await crypto.subtle.digest('SHA-256',utf8.encode(s))));
const failures:string[]=[];
for(const v of fixture.vectors){
 const tree=JSON.parse(v.canonicalUtf8),identity='truss-canonical/0.1.0\ntruss-bootstrap-bundle/0.1.0\n'+v.canonicalUtf8;
 if(!validate(tree)||encode(tree)!==v.canonicalUtf8||hex(utf8.encode(v.canonicalUtf8))!==v.preimageHex||await digest(v.canonicalUtf8)!==v.bundleSha256||hex(utf8.encode(identity))!==v.separateIdentityPreimageHex||await digest(identity)!==v.separateIdentitySha256||v.bundleSha256===v.separateIdentitySha256)failures.push(v.name);
}
const receipt={scope:'Four independent complete bundle shape/canonical byte/content-vs-identity hash probes; no UMF/native/profile qualification',cases:fixture.vectors.length,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/bootstrap-bundle-vectors.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
