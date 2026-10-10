/** Combined contract schema integration; no semantic/native support inference. */
const {default:Ajv}=await import(process.argv[2]);
const a=new Ajv({strict:true});const files=[...new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts')].sort();const errors:any[]=[];const schemas:any[]=[];const sourceInventory:any[]=[];const ids=new Set<string>();
for(const file of files){try{const raw=await Bun.file('docs/helix/02-design/contracts/'+file).text();const schema=JSON.parse(raw);if(typeof schema.$id!=='string'||!schema.$id.length||ids.has(schema.$id))throw Error('missing/duplicate schema identity');ids.add(schema.$id);a.addSchema(schema);schemas.push([file,schema.$id]);sourceInventory.push({file,id:schema.$id,sha256:new Bun.CryptoHasher('sha256').update(raw).digest('hex')});}catch(e){errors.push({file,stage:'registration',message:String(e)});}}
for(const [file,id] of schemas){try{if(typeof a.getSchema(id)!=='function')throw Error('missing compiled schema');}catch(e){errors.push({file,stage:'compile',message:String(e)});}}
const receipt={checkedAt:new Date().toISOString(),bunVersion:Bun.version,scope:'combined schema registration/reference/strict compilation only',files:files.length,errors,sourceInventory};
const output=process.argv[3]??'docs/helix/04-build/evidence/design-audit/schema-inventory.json';
await Bun.write(output,JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({scope:receipt.scope,files:receipt.files,errors},null,2));if(errors.length)process.exit(1);export {};
