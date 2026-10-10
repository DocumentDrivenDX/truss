/** Public conformance result shapes only; no run/assessor/native support proof. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
for(const file of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+file).json());
const run=ajv.getSchema('urn:truss:draft:conformance-run-result:0.1.0')!;
const assess=ajv.getSchema('urn:truss:draft:conformance-assessment:0.1.0')!;
const artifact={identity:'original',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const pin={identity:'qualification',version:'0.1.0',sha256:'b'.repeat(64)};
const recorded={outcome:'recorded',receipt:artifact};
const interrupted={outcome:'interrupted',originalRunEvidence:artifact,recoveryReference:'original-run'};
const qualified={state:'qualified',receipt:artifact,requiredManifest:artifact,qualificationProfile:pin,assessmentEvidence:artifact};
const {assessmentEvidence:omitted,...noEvidence}=qualified;
const cases:[string,'run'|'assessment',unknown,boolean][]=[
 ['recorded complete wrapper','run',recorded,true],['interrupted original wrapper','run',interrupted,true],['runner resource unavailable','run',{outcome:'unavailable',reason:'resource'},true],['unavailable has no receipt','run',{outcome:'unavailable',reason:'resource',receipt:artifact},false],['no empty recovery reference','run',{...interrupted,recoveryReference:''},false],['recorded is not qualified','run',{...recorded,state:'qualified'},false],
 ['complete assessment wrapper','assessment',qualified,true],['complete unqualified diagnostic','assessment',{state:'unqualified',diagnostics:artifact},true],['assessment resource unavailable','assessment',{state:'unavailable',reason:'resource'},true],['qualified needs assessment evidence','assessment',noEvidence,false],['unavailable cannot carry cached pass','assessment',{state:'unavailable',reason:'resource',receipt:artifact},false],['false receipt needs original admission','assessment',{...qualified,receipt:{...artifact,identity:'forged'}},true],['false native run needs original admission','run',recorded,true]
];
const failures=cases.filter(([,kind,value,expected])=>Boolean((kind==='run'?run:assess)(value))!==expected).map(([name])=>name);
console.log(JSON.stringify({scope:'conformance run/assessment result wrapper shape only; no original execution or qualification proof',cases:cases.length,failures},null,2));if(failures.length)process.exit(1);void omitted;export {};
