/** Independent shape controls, not native receipt/visibility qualification. */
const {default:Ajv}=await import(process.argv[2]);
const validator=new Ajv({strict:true});
for(const file of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts')){
 validator.addSchema(await Bun.file('docs/helix/02-design/contracts/'+file).json());
}
const request=validator.getSchema('urn:truss:draft:receipt-visibility-request:0.1.0')!;
const result=validator.getSchema('urn:truss:draft:receipt-visibility-result:0.1.0')!;
const validRequest={interfaceVersion:'truss-receipt-visibility-request/0.1.0',token:'opaque_candidate',limits:{tokenBytes:'16384',evidenceBytes:'1024',retainedBytes:'2048',workUnits:'1000',nativeStatements:'4'}};
const available={interfaceVersion:'truss-receipt-visibility-result/0.1.0',outcome:'available',included:false,comparisonProfile:{identity:'fixture-only',version:'0.1.0',sha256:'a'.repeat(64)}};
const unavailable={interfaceVersion:'truss-receipt-visibility-result/0.1.0',outcome:'unavailable',reason:'observation_integrity'};
const controls:[string,any,any,boolean][]=[
 ['request',request,validRequest,true],['false-is-available',result,available,true],
 ['true-is-available',result,{...available,included:true},true],['unavailable',result,unavailable,true],
 ['unavailable-false',result,{...unavailable,included:false},false],
 ['unavailable-true',result,{...unavailable,included:true},false],
 ['missing-profile',result,{interfaceVersion:available.interfaceVersion,outcome:'available',included:false},false],
 ['unknown-reason',result,{...unavailable,reason:'not_found'},false],
 ['unknown-field',request,{...validRequest,actor:'caller'},false],
 ['padded-token',request,{...validRequest,token:'opaque='},false],
 ['numeric-limit',request,{...validRequest,limits:{...validRequest.limits,workUnits:1000}},false],
 ['zero-limit',request,{...validRequest,limits:{...validRequest.limits,workUnits:'0'}},false],
 ['leading-zero',request,{...validRequest,limits:{...validRequest.limits,workUnits:'01'}},false],
 ['unknown-limit',request,{...validRequest,limits:{...validRequest.limits,timeout:'1'}},false],
];
for(const [name,validate,input,expected] of controls)if(validate(input)!==expected)throw Error('Wire expectation mismatch: '+name);
console.log(JSON.stringify({controls:controls.length,scope:'shape only; no numeric byte/account/original authority/native qualification'}));
export {};
