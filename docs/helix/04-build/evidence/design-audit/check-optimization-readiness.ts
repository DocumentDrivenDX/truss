/** Readiness metadata shapes only; native readiness/performance unqualified. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});a.addSchema(await Bun.file('docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json').json());
const index=a.compile(await Bun.file('docs/helix/02-design/contracts/index-readiness-v0.1.schema.json').json());const stats=a.compile(await Bun.file('docs/helix/02-design/contracts/statistics-readiness-v0.1.schema.json').json());
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)},artifact={identity:'fixture',bytesBase64:'e30=',sha256:'b'.repeat(64)};
const job={interfaceVersion:'truss-index-job/0.1.0',installationId:'install',acceptedCatalogRevision:'1',layoutProfile:pin,bindingProfile:pin,declarationIdentity:'declaration',definition:artifact,target:{schema:'s',relation:'r',index:'i'}};
const attempt={job,attemptId:'attempt',generation:'1',dispatcherProfile:pin};const ready={state:'ready',attempt,observedAt:'fixture',installedInventory:artifact,verificationProfile:pin};
const statJob={...job,interfaceVersion:'truss-statistics-job/0.1.0',target:{schema:'s',relation:'r',statistics:'st'},collectionProfile:pin};const statAttempt={...attempt,job:statJob};
const defined={state:'defined',attempt:statAttempt,observedAt:'fixture',installedInventory:artifact,collection:'not_confirmed'};
const collected={state:'collected',attempt:statAttempt,observedAt:'fixture',installedInventory:artifact,collectionEvidence:artifact,collectionOutcome:'empty_qualified'};
const cases:[any,string,unknown,boolean][]=[
 [index,'ready',ready,true],[index,'declared',{state:'declared',job},true],
 [index,'queued needs committed basis',{state:'queued',attempt},false],
 [index,'ready not performance evidence',{...ready,p95Ratio:'1.2'},false],
 [index,'unknown physical failure',{state:'failed',attempt,code:'failure',outcomeEvidence:artifact,physicalOutcome:'unknown'},true],
 [index,'forged inventory needs native refusal',{...ready,installedInventory:{...artifact,identity:'forged'}},true],
 [stats,'defined uncollected',defined,true],[stats,'qualified empty collection',collected,true],
 [stats,'defined cannot claim collected',{...defined,collection:'confirmed'},false],
 [stats,'collected requires evidence',Object.fromEntries(Object.entries(collected).filter(([k])=>k!=='collectionEvidence')),false],
 [stats,'statistics cannot be index ready',{...ready,attempt:statAttempt},false],
 [stats,'collected not latency proof',{...collected,p95:'1'},false],
 [stats,'stale collection profile',{state:'stale',job:statJob,reason:'collection_profile'},true]
 ];
a.addSchema(await Bun.file('docs/helix/02-design/contracts/physical-optimization-request-v0.1.schema.json').json());
const physical=a.compile(await Bun.file('docs/helix/02-design/contracts/physical-optimization-result-v0.1.schema.json').json());
const request={interfaceVersion:'truss-physical-optimization/0.1.0',kind:'index',declaration:artifact,declarationProfile:pin,expectedInstalledInventory:artifact,budget:{profile:pin,maxIndexCount:'2',maxIndexBytes:'1000'}};
const pending={outcome:'pending',durability:'pending',originalRequest:request,admittedPlan:artifact,ownedObjectInventory:artifact,resultingInventory:artifact,budgetObservation:{interfaceVersion:'truss-physical-index-budget/0.1.0',profile:pin,countedInventory:artifact,before:{indexCount:'1',measuredBytes:'100',observation:artifact},admission:{proposedCount:'1',totalByteUpperBound:'200',method:pin,evidence:artifact},after:{indexCount:'2',measuredBytes:'200',observation:artifact},scope:'supplied_transaction'}};
cases.push([physical,'pending native plan',pending,true],
 [physical,'no hidden commit',{...pending,durability:'committed'},false],
 [physical,'refusal no partial plan',{outcome:'refused',reason:'budget',admittedPlan:artifact},false],
 [physical,'budget uses exact integers',{...pending,budgetObservation:{...pending.budgetObservation,after:{...pending.budgetObservation.after,indexCount:2}}},false],
 [physical,'budget overrun needs semantic refusal',{...pending,budgetObservation:{...pending.budgetObservation,after:{...pending.budgetObservation.after,measuredBytes:'1001'}}},true],
 [physical,'inventory substitution needs native refusal',{...pending,resultingInventory:{...artifact,identity:'substitute'}},true]);
const admission=a.compile(await Bun.file('docs/helix/02-design/contracts/physical-job-admission-v0.1.schema.json').json());
const pendingAdmission={interfaceVersion:'truss-physical-job-admission/0.1.0',kind:'index',durability:'pending',attempt,evidence:artifact};
const committedAdmission={interfaceVersion:pendingAdmission.interfaceVersion,kind:'index',durability:'committed',attempt,observation:artifact};
cases.push([admission,'pending admission metadata',pendingAdmission,true],
 [admission,'committed admission metadata',committedAdmission,true],
 [admission,'statistics committed metadata',{...committedAdmission,kind:'statistics',attempt:statAttempt},true],
 [admission,'pending cannot supply commit observation',{...pendingAdmission,observation:artifact},false],
 [admission,'committed needs actual observation',{...pendingAdmission,durability:'committed'},false],
 [admission,'kind cannot substitute attempt',{...committedAdmission,kind:'statistics'},false],
 [admission,'metadata cannot mint lease',{...committedAdmission,lease:{}},false],
 [admission,'forged queue observation native refusal',{...committedAdmission,observation:{...artifact,identity:'forged'}},true]);
const jobResult=a.compile(await Bun.file('docs/helix/02-design/contracts/physical-job-result-v0.1.schema.json').json());
const envelope={interfaceVersion:'truss-physical-job-result/0.1.0',kind:'index',operation:'admit',result:{outcome:'admitted',admission:pendingAdmission}};
cases.push([jobResult,'operation-bound pending admission',envelope,true],
 [jobResult,'admit cannot claim committed',{...envelope,result:{outcome:'admitted',admission:committedAdmission}},false],
 [jobResult,'observe admission committed',{...envelope,operation:'observe_admission',result:{outcome:'admitted',admission:committedAdmission}},true],
 [jobResult,'run yields original readiness',{...envelope,operation:'run',result:{outcome:'observed',readiness:ready}},true],
 [jobResult,'run cannot return admission',{...envelope,operation:'run'},false],
 [jobResult,'unavailable cannot disclose readiness',{...envelope,operation:'run',result:{outcome:'unavailable',reason:'authority',readiness:ready}},false],
 [jobResult,'execution failure not successful result',{...envelope,result:{outcome:'execution_failed',error:{}}},false]);
const failures=cases.filter(([c,,v,e])=>Boolean(c(v))!==e).map(([,n])=>n);console.log(JSON.stringify({scope:'index/statistics metadata shapes, not native readiness or performance',cases:cases.length,failures},null,2));if(failures.length)process.exit(1);export {};
