/** Published byte/tree/preimage/hash correspondence; not production codec or native custody. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
for(const n of ['direct-cursor','direct-traversal-request','traversal-query','traversal-private-state','traversal-resource-ledger'])a.addSchema(await Bun.file(`docs/helix/02-design/contracts/${n}-v0.1.schema.json`).json());
const corpus=await Bun.file('docs/helix/02-design/contracts/bindings/traversal-canonical-v0.1.vectors.json').json();const failures:string[]=[];
for(const v of corpus.vectors){
 const id=v.name==='query'?'traversal-query':v.name==='ledger'?'traversal-resource-ledger':'traversal-private-state';
 if(!a.getSchema(`urn:truss:draft:${id}:0.1.0`)!(v.input))failures.push(v.name+':shape');
 if(!Bun.deepEquals(JSON.parse(v.canonicalUtf8),v.input))failures.push(v.name+':tree');
 const pre=new TextEncoder().encode(corpus.canonicalProfile+'\n'+v.domain+'\n'+v.canonicalUtf8);
 if(Buffer.from(pre).toString('hex')!==v.preimageHex)failures.push(v.name+':preimage');
 if(new Bun.CryptoHasher('sha256').update(pre).digest('hex')!==v.sha256)failures.push(v.name+':sha256');
 const wrong=new TextEncoder().encode(corpus.canonicalProfile+'\ntruss-group-input/0.1.0\n'+v.canonicalUtf8);
 if(new Bun.CryptoHasher('sha256').update(wrong).digest('hex')===v.sha256)failures.push(v.name+':domain');
}
console.log(JSON.stringify({scope:'published traversal canonical tree/preimage/hash correspondence only',vectors:corpus.vectors.length,failures},null,2));if(failures.length)process.exit(1);export {};
