/** Case-only argument shapes; original artifacts, live scopes and signals remain host admission. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
const root='docs/helix/02-design/contracts/';
for(const file of new Bun.Glob('*.schema.json').scanSync(root))ajv.addSchema(await Bun.file(root+file).json());
const id='urn:truss:proposal:conformance-capability-arguments:0.1.0';
const pin={identity:'fixture',version:'0.1',sha256:'a'.repeat(64)},artifact={identity:'fixture',bytesBase64:'e30=',sha256:pin.sha256};
const accept={interfaceVersion:'truss-acceptance-input/0.1.0',layoutProfile:pin,acceptanceProfile:pin,validatorProfile:pin,supportProfile:pin,documents:[{documentId:'d',documentRevision:'1',artifact,umfProfile:pin,ingress:{kind:'native'}}],binding:{state:'absent'},policy:{unknownEndpoint:'reject',loss:'strict',profile:pin},transforms:[]};
const identity={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'d',moduleId:'m'}};
const group={interfaceVersion:'truss-group-input/0.1.0',layoutProfile:pin,mutationProfile:pin,valueProfile:pin,catalog:{selection:'current'},assertedOrigin:{kind:'null'},operations:[{operation:'delete_object',target:{state:'stored',identity}}]};
const imported={interfaceVersion:'truss-import-input/0.1.0',layoutProfile:pin,importProfile:pin,valueProfile:pin,catalog:{revision:'1',modelBundleSha256:pin.sha256},loadId:'fixture',assertedOrigin:{kind:'null'},records:[]};
const batches={input:imported,options:{isolation:'read_committed',accessMode:'read_write'},cancellation:{kind:'none'}};
const requested={state:'present',identity:{interfaceVersion:'truss-request-identity/0.1.0',authorizedScopeIdentity:'fixture',requestId:'fixture',inputProfile:'truss-group-input/0.1.0'}};
const cases:[string,string,unknown,boolean][]=[
 ['separate origin','catalogAcceptance',{input:accept,assertedOrigin:{integer:'9007199254740993'}},true],
 ['host number origin refused','catalogAcceptance',{input:accept,assertedOrigin:{integer:42}},false],
 ['origin cannot enter public input','catalogAcceptance',{input:{...accept,assertedOrigin:{}},assertedOrigin:{}},false],
 ['no serialized transaction','catalogAcceptance',{input:accept,assertedOrigin:{},transactionId:'caller'},false],
 ['request-free argument','requestFreeGroup',{input:group,request:{state:'none'}},true],
 ['request-bearing argument','requestBearingGroup',{input:group,request:requested},true],
 ['request-free forbids present','requestFreeGroup',{input:group,request:requested},false],
 ['wrong overload','requestBearingGroup',{input:group,request:{state:'none'}},false],
 ['request cannot enter semantic input','requestFreeGroup',{input:{...group,request:{state:'none'}},request:{state:'none'}},false],
 ['explicit batch options','importBatches',batches,true],
 ['read-only import refused','importBatches',{...batches,options:{isolation:'read_committed',accessMode:'read_only'}},false],
 ['explicit cancellation required','importBatches',{input:imported,options:batches.options},false],
 ['original harness reference shape','importBatches',{...batches,cancellation:{kind:'harness',reference:'original-signal'}},true],
 ['signal cannot be serialized','importBatches',{...batches,cancellation:{kind:'harness',reference:'original-signal',signal:{}}},false],
 ['public options cannot contain fake signal','importBatches',{...batches,options:{...batches.options,cancellation:{signal:{}}}},false]
];
for(const [name,member,value,wanted] of cases){const validate=ajv.getSchema(id+'#/$defs/'+member);if(!validate||Boolean(validate(value))!==wanted)throw Error(name+': '+JSON.stringify(validate?.errors));}
console.log(cases.length+' case-only argument shape controls passed. No public wire change, live handle issuance, signal authority or native admission.');
export {};
