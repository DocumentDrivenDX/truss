/** Completion-wire boundaries only; native outcome/custody/inventory require independent admission. */
const {default:Ajv}=await import(process.argv[2]);
const ajv=new Ajv({strict:true});
for(const file of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+file).json());
const validate=ajv.getSchema('urn:truss:draft:operation-completion:0.1.0')!;
const ref={identity:'original',sha256:'a'.repeat(64)};
const pin={identity:'profile',version:'0.1.0',sha256:'b'.repeat(64)};
const base={interfaceVersion:'truss-operation-completion/0.1.0',registryIdentity:'registry',assemblyId:'assembly',executorIdentity:'executor',transactionIdentity:'transaction',transactionGeneration:'generation',attemptIdentity:'attempt',leaseIdentity:'lease',completionProfile:pin,resourceProfile:pin,originalComposition:ref,originalAdmission:ref,originalNativeLedger:ref,resources:[{identity:'call',kind:'native_call',finalObservation:ref}],boundaryRestoration:ref,outcomeEvidence:ref};
const caller={...base,completionClass:'caller_idle',outcome:'pending',originalActiveUsableObservation:ref};
const ended={...base,completionClass:'transaction_ended',outcome:'commit_unknown',originalTermination:ref};
const {originalTermination:omitted,...noTermination}=ended;
const cases:[string,unknown,boolean][]=[
 ['usable caller pending',caller,true],
 ['known caller operation-local failure',{...caller,outcome:'operation_failed'},true],
 ['terminated unknown commit',ended,true],
 ['terminated committed',{...ended,outcome:'committed'},true],
 ['terminated rolled back',{...ended,outcome:'rolled_back'},true],
 ['caller cannot claim committed',{...caller,outcome:'committed'},false],
 ['unknown commit needs termination field',noTermination,false],
 ['no future release hash',{...ended,releaseSha256:'c'.repeat(64)},false],
 ['unresolved completion cannot release',{...ended,completionClass:'unresolved'},false],
 ['foreign generation shape needs semantic refusal',{...caller,transactionGeneration:'later-generation'},true],
 ['omitted original resource shape needs semantic refusal',{...caller,resources:[]},true],
 ['forged termination shape needs native refusal',{...ended,originalTermination:{...ref,identity:'forged'}},true]
];
const failures=cases.filter(([,value,expected])=>Boolean(validate(value))!==expected).map(([name])=>name);
console.log(JSON.stringify({scope:'completion discriminants/closed fields only; no original inventory/native evidence proof',cases:cases.length,failures},null,2));
if(failures.length)process.exit(1);void omitted;export {};
