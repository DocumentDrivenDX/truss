/** Envelope shape only; never decodes deferred payload. */
const {default:Ajv}=await import(process.argv[2]);
const ajv=new Ajv({strict:true});
for(const n of ['acceptance-input','exact-value','history-record','direct-cursor'])ajv.addSchema(await Bun.file(`docs/helix/02-design/contracts/${n}-v0.1.schema.json`).json());
const validate=ajv.compile(await Bun.file('docs/helix/02-design/contracts/import-input-v0.1.schema.json').json());
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const owner={documentId:'doc',moduleId:'module'};
const identity={id:'1',typeId:'1',definitionPin:'definition',owner};
const payload={identity:'payload',bytesBase64:'bm90IGpzb24=',sha256:'a'.repeat(64)};
const object={kind:'object',identity:{operation:'object_key',type:{typeId:'1',definitionPin:'definition',owner},keyNumber:'1',keyDefinitionPin:'key',keyEncodingProfile:pin,components:[{propertyId:'property',definitionPin:'property',value:{kind:'string',text:'key'}}]},payload,payloadProfile:pin};
const input={interfaceVersion:'truss-import-input/0.1.0',layoutProfile:pin,importProfile:pin,valueProfile:pin,catalog:{revision:'1',modelBundleSha256:pin.sha256},loadId:'load',assertedOrigin:{kind:'null'},records:[object]};
const cases:[string,unknown,boolean][]=[
 ['object envelope',input,true],['empty input',{...input,records:[]},true],
 ['typed edge',{...input,records:[{kind:'edge',identity:{relationshipDefinitionPin:'relationship',source:identity,target:identity},payload,payloadProfile:pin}]},true],
 ['empty key components',{...input,records:[{...object,identity:{...object.identity,components:[]}}]},false],
 ['unknown envelope member',{...input,execute:'SQL'},false],
 ['missing payload bytes',{...input,records:[{...object,payload:{identity:'payload',sha256:pin.sha256}}]},false],
 ['unsupported key number remains semantic',{...input,records:[{...object,identity:{...object.identity,keyNumber:'not-native'}}]},true],
 ['invalid deferred payload remains uninterpreted',input,true]
];
const failures=cases.filter(([,value,expected])=>Boolean(validate(value))!==expected).map(([name])=>name);
console.log(JSON.stringify({scope:'identity envelope shape only; no payload decoding',cases:cases.length,failures},null,2));
if(failures.length)process.exit(1);
export {};
