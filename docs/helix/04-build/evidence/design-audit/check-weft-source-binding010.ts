/** Source fixture schema/integrity check; not compiler or native execution. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
for(const f of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))ajv.addSchema(JSON.parse(await Bun.file('docs/helix/02-design/contracts/'+f).text()));
const root='docs/helix/04-build/evidence/weft-source-binding010/';
const bytes=await Bun.file(root+'binding.json').text(),binding=JSON.parse(bytes),nested=JSON.parse(await Bun.file(root+'nested-definitions.json').text());
const cases=[['binding','urn:truss:draft:postgresql-binding:0.1.0',binding],['home','urn:truss:draft:property-home:0.1.0',nested.home],['value','urn:truss:draft:value-definition:0.1.0',nested.value],['presence','urn:truss:draft:presence-definition:0.1.0',nested.presence],['codec','urn:truss:draft:jsonb-leaf-codec:0.1.0',nested.codec],['context','urn:truss:draft:read-context-definition:0.1.0',nested.context]] as const;
for(const [name,id,value] of cases){const check=ajv.getSchema(id);if(!check||!check(value))throw Error(name+': '+JSON.stringify(check?.errors));}
const {readDocument}=await import('/Users/erik/Projects/umf/src/model/document');
readDocument(await Bun.file(root+'original-model.json').text(),'json');
console.log(JSON.stringify({schemas:cases.length,originalUmfModelValid:true,bindingBytes:new TextEncoder().encode(bytes).length,nativeQualified:false,compilerExecuted:false}));
export {};
