/** Attempt record shape only; original issuer/transition/lease custody is independently verified. */
const {default:Ajv}=await import(process.argv[2]);
const ajv=new Ajv({strict:true});
for(const file of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+file).json());
const validate=ajv.getSchema('urn:truss:draft:operation-attempt:0.1.0')!;
const ref={identity:'original',sha256:'a'.repeat(64)};
const pin={identity:'profile',version:'0.1.0',sha256:'b'.repeat(64)};
const base={interfaceVersion:'truss-operation-attempt/0.1.0',registryIdentity:'registry',assemblyId:'assembly',executorIdentity:'executor',transactionIdentity:'transaction',transactionGeneration:'generation',attemptIdentity:'attempt',registryProfile:pin,resourceProfile:pin,originalComposition:ref,originalPreparation:ref};
const prepared={...base,phase:'prepared'};
const admitted={...base,phase:'admitted',leaseIdentity:'original-lease',originalAcquisition:ref};
const unresolved={...base,phase:'unresolved',lastConfirmedPhase:'admitted',originalLastConfirmed:ref,recoveryReferences:[ref]};
const {originalLastConfirmed:omitted,...lostHistory}=unresolved;
const cases:[string,unknown,boolean][]=[
 ['prepared record',prepared,true],
 ['admitted record',admitted,true],
 ['definitive refusal',{...base,phase:'refused',reason:'resource',originalDecision:ref},true],
 ['closed abandoned record',{...base,phase:'closed',closure:'abandoned',originalClosure:ref},true],
 ['uncertainty retains confirmed basis',unresolved,true],
 ['prepared cannot disclose lease',{...prepared,leaseIdentity:'lease'},false],
 ['closed cannot disclose lease',{...base,phase:'closed',closure:'released',originalClosure:ref,leaseIdentity:'lease'},false],
 ['uncertainty cannot drop history',lostHistory,false],
 ['uncertainty needs recovery',{...unresolved,recoveryReferences:[]},false],
 ['no future state hash',{...admitted,resultingStateSha256:'c'.repeat(64)},false],
 ['forged acquisition needs original custody refusal',{...admitted,originalAcquisition:{...ref,identity:'forged'}},true],
 ['false confirmed history needs original observation refusal',{...unresolved,lastConfirmedPhase:'closed'},true]
];
const failures=cases.filter(([,value,expected])=>Boolean(validate(value))!==expected).map(([name])=>name);
console.log(JSON.stringify({scope:'attempt state/closed-field shape only; no original custody or acquisition proof',cases:cases.length,failures},null,2));
if(failures.length)process.exit(1);void omitted;export {};
