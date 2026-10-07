/** Published byte/preimage/hash and input-schema correspondence, not canonicalizer/native qualification. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
for(const n of ['acceptance-input','exact-value','history-record','group-input'])a.addSchema(await Bun.file('docs/helix/02-design/contracts/'+n+'-v0.1.schema.json').json());
const check=a.getSchema('urn:truss:draft:group-input:0.1.0')!;
const corpus=await Bun.file('docs/helix/02-design/contracts/bindings/group-canonical-v0.1.vectors.json').json();
const failures:string[]=[];const encoder=new TextEncoder();let original='';
/** Audit-only reference spelling, independent of the Python fixture generator. */
function spelling(value:any):string {
 if(value===null)return 'null';
 if(typeof value==='boolean')return value?'true':'false';
 if(typeof value==='string'){
  if(!value.isWellFormed())throw Error('unpaired surrogate');
  let result='"';for(const c of value){const n=c.codePointAt(0)!;
   result+=c==='"'?'\\"':c==='\\'?'\\\\':n<32?'\\u'+n.toString(16).padStart(4,'0'):c;
  }return result+'"';
 }
 if(Array.isArray(value))return '['+value.map(spelling).join(',')+']';
 if(typeof value==='object'){
  const keys=Object.keys(value).sort((left,right)=>{const l=encoder.encode(left),r=encoder.encode(right);for(let i=0;i<Math.min(l.length,r.length);i++)if(l[i]!==r[i])return l[i]-r[i];return l.length-r.length;});
  return '{'+keys.map(k=>spelling(k)+':'+spelling(value[k])).join(',')+'}';
 }
 throw Error('unsupported host value');
}
for(const v of corpus.vectors){
 if(spelling(v.input)!==v.canonicalUtf8)failures.push(v.name+':canonical spelling');
 if(!check(v.input))failures.push(v.name+':input shape');
 if(!Bun.deepEquals(JSON.parse(v.canonicalUtf8),v.input))failures.push(v.name+':input byte-tree correspondence');
 const raw=encoder.encode(corpus.canonicalProfile+'\n'+corpus.semanticDomain+'\n'+v.canonicalUtf8);
 if(Buffer.from(raw).toString('base64')!==v.preimageBase64)failures.push(v.name+':preimage');
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),x=>x.toString(16).padStart(2,'0')).join('');
 if(digest!==v.sha256)failures.push(v.name+':digest');
 if(v.relation==='original')original=digest;
 else if(v.relation==='same_as_original' ? digest!==original : digest===original)failures.push(v.name+':relation');
}
let rejectionControls=0;
for(const [value,alternate] of [[{b:'second',a:'first'},'{"b":"second","a":"first"}'],['line\n','"line\\n"'],['slash/','"slash\\/"']] as const){
 rejectionControls++;if(spelling(value)===alternate)failures.push('alternate spelling wrongly accepted');
}
try{spelling(1);failures.push('host number wrongly accepted');}catch{}rejectionControls++;
try{spelling('\ud800');failures.push('unpaired surrogate wrongly accepted');}catch{}rejectionControls++;
const receipt={scope:'Published group canonical spelling/byte/hash/input-shape correspondence only; no production/native/authority qualification',vectors:corpus.vectors.length,rejectionControls,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/group-canonical.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
