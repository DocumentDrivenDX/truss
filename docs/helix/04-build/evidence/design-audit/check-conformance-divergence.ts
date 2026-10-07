/** Divergence envelope only; comparison/oracle/reviewer/native custody remains semantic. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
for(const file of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+file).json());
const validate=ajv.getSchema('urn:truss:draft:conformance-divergence:0.1.0')!;
const artifact={identity:'original',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const pin={identity:'implementation',version:'0.1.0',sha256:'b'.repeat(64)};
const base={interfaceVersion:'truss-conformance-divergence/0.1.0',runIdentity:'run',caseIdentity:'case',requiredManifest:artifact};
const evidence={surface:'journal',comparatorProfile:pin,identityAliases:artifact,expected:artifact,nativeObservation:artifact,comparisonEvidence:artifact,attribution:'unresolved'};
const single={...base,...evidence,state:'observed',direction:'single_run',implementation:pin,observed:artifact};
const cross={...base,...evidence,state:'observed',direction:'a_write_b_read',implementationA:pin,implementationB:pin,observedA:artifact,observedB:artifact};
const reviewed={...base,state:'reviewed',originalMismatch:artifact,resolution:'implementation',reviewProfile:pin,originalReviewerRecognition:artifact,reviewEvidence:artifact};
const {originalReviewerRecognition:omitted,...noReviewer}=reviewed;
const cases:[string,unknown,boolean][]=[
 ['single complete mismatch',single,true],['cross complete mismatch',cross,true],['reverse direction',{...cross,direction:'b_write_a_read'},true],['reviewed attribution',reviewed,true],
 ['single cannot fabricate second implementation',{...single,implementationB:pin},false],['observed cannot assert reviewed blame',{...single,attribution:'contract'},false],['review needs original recognition',noReviewer,false],['review cannot rewrite observations',{...reviewed,expected:artifact},false],['no automatic majority attribution',{...reviewed,resolution:'majority_vote'},false],
 ['wrong mode attribution needs original mismatch admission',{...reviewed,resolution:'implementation_b'},true],['false reviewer needs original custody refusal',{...reviewed,originalReviewerRecognition:{...artifact,identity:'forged'}},true],['equal wrong outputs need independent expected comparison',cross,true]
];
const failures=cases.filter(([,value,expected])=>Boolean(validate(value))!==expected).map(([name])=>name);
console.log(JSON.stringify({scope:'divergence envelope fields only; no observed mismatch or reviewed attribution proof',cases:cases.length,failures},null,2));if(failures.length)process.exit(1);void omitted;export {};
