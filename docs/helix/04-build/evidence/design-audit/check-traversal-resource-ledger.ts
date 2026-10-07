/** Private ledger shapes only; independent arithmetic/custody checks remain required. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
for(const n of ['direct-cursor','direct-traversal-request'])a.addSchema(await Bun.file(`docs/helix/02-design/contracts/${n}-v0.1.schema.json`).json());
const check=a.compile(await Bun.file('docs/helix/02-design/contracts/traversal-resource-ledger-v0.1.schema.json').json());
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};const reference={identity:'original',sha256:'b'.repeat(64)};
const context={catalogRevision:'2',layoutProfile:pin,readProfile:pin,authorizedScopeIdentity:'scope',consistency:{kind:'held_snapshot',snapshotIdentity:'snapshot'}};
const zero={examinedEdges:'0',pathStates:'0',activeWorkMilliseconds:'0'};
const maximum={examinedEdges:'10',pathStates:'10',activeWorkMilliseconds:'100'};
const permit={permitIdentity:'permit',admittedAccountingVersion:'1',maximumIncrements:maximum,maximumReservationBytes:'4096',originalAdmission:reference,state:'reserved'};
const ledger={interfaceVersion:'truss-traversal-resource-ledger/0.1.0',assemblyId:'assembly',handle:{stageIdentity:'stage',generation:'0',querySha256:'b'.repeat(64),context},storeProfile:pin,resourceProfile:pin,accountingVersion:'1',originalQuery:reference,originalCreation:reference,initialWork:zero,actualWork:zero,outstandingMaximumWork:maximum,retainedBytes:'1000',chargedReservationBytes:'4096',permits:[permit]};
const settled={...permit,state:'settled',settledAccountingVersion:'2',actualIncrements:{examinedEdges:'8',pathStates:'6',activeWorkMilliseconds:'80'},originalCompletion:reference};
const cases:[string,unknown,boolean][]=[
 ['reserved ledger',ledger,true],['settled ledger',{...ledger,accountingVersion:'2',actualWork:settled.actualIncrements,outstandingMaximumWork:zero,permits:[settled]},true],
 ['reserved cannot claim completion',{...ledger,permits:[{...permit,originalCompletion:reference}]},false],
 ['settled requires original completion',{...ledger,permits:[Object.fromEntries(Object.entries(settled).filter(([k])=>k!=='originalCompletion'))]},false],
 ['no public frontier payload',{...ledger,records:[]},false],
 ['host numeric charge rejects',{...ledger,chargedReservationBytes:4096},false],
 ['no negative work',{...ledger,actualWork:{...zero,examinedEdges:'-1'}},false],
 ['duplicate permit needs semantic refusal',{...ledger,permits:[permit,permit]},true],
 ['false outstanding total needs semantic refusal',{...ledger,outstandingMaximumWork:zero},true],
 ['settled above reservation needs semantic refusal',{...ledger,permits:[{...settled,actualIncrements:{...zero,examinedEdges:'11'}}]},true],
 ['unbacked refund needs physical refusal',{...ledger,chargedReservationBytes:'0'},true],
 ['forged completion needs issuer refusal',{...ledger,permits:[{...settled,originalCompletion:{...reference,identity:'forged'}}]},true]
];
const failures=cases.filter(([,v,e])=>Boolean(check(v))!==e).map(([n])=>n);console.log(JSON.stringify({scope:'private ledger shapes, not arithmetic or issuer/physical validation',cases:cases.length,failures},null,2));if(failures.length)process.exit(1);export {};
