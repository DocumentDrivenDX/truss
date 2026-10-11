/** Closed shape controls only; fixtures confer no original native authority. */
const {default:Ajv}=await import(process.argv[2]);
const base='docs/helix/02-design/contracts/';
const ajv=new Ajv({strict:true});
ajv.addSchema(await Bun.file(base+'acceptance-input-v0.1.schema.json').json());
const schema=await Bun.file(base+'existing-root-string-replacement-v0.1.proposal.schema.json').json();
const validate=ajv.compile(schema);
const bytes=Buffer.from('{"shapeOnly":true}');
const artifact={identity:'shape-only',bytesBase64:bytes.toString('base64'),sha256:new Bun.CryptoHasher('sha256').update(bytes).digest('hex')};
function fixture(kind:string):any {
 const rule=schema.$defs[kind==='planned-effects'?'plannedEffects':kind];
 function fill(rule:any):any {
  if(rule.$ref?.startsWith('#/'))return fill(schema.$defs[rule.$ref.split('/').at(-1)]);
  if(rule.$ref?.endsWith('/exactArtifact'))return structuredClone(artifact);
  if(rule.$ref?.endsWith('/profilePin'))return {identity:'shape-only-profile',version:'0.1.0',sha256:artifact.sha256};
  if(rule.const!==undefined)return rule.const;
  if(rule.type==='object')return Object.fromEntries(Object.entries(rule.properties).map(([k,v])=>[k,fill(v)]));
  return '1';
 }
 return fill(rule);
}
let checks=0;
for(const kind of ['prestate','candidate','planned-effects']){
 const good=fixture(kind);if(!validate(good))throw Error(JSON.stringify(validate.errors));checks++;
 for(const name of Object.keys(good)){
  const bad=structuredClone(good);delete bad[name];if(validate(bad))throw Error('accepted omission '+kind+'/'+name);checks++;
 }
 const extra=structuredClone(good);extra.ready=true;if(validate(extra))throw Error('accepted ready flag');checks++;
 const wrong=structuredClone(good);wrong.touch.ownerId=9007199254740992;if(validate(wrong))throw Error('accepted numeric owner');checks++;
}
console.log(JSON.stringify({checks,scope:'closed-shape-only; no semantics, authority or native effect evidence'}));
