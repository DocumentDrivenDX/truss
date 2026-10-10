/** Wire shape only; native commit/fence/source evidence not qualified. */
const {default:Ajv}=await import(process.argv[2]);
const root='docs/helix/02-design/contracts/';
const base=await Bun.file(root+'acceptance-input-v0.1.schema.json').json();
const schema=await Bun.file(root+'feed-committed-application-v0.1.schema.json').json();
const validate=new Ajv({strict:true}).addSchema(base).compile(schema);
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const context={sourceEpoch:'epoch',feedProfile:'draft',scopeIdentity:'scope'};
const tx={domain:'complete-feed-transaction/0.1.0',context,xid:'10',manifestSha256:'a'.repeat(64)};
const coverage={domain:'complete-feed-coverage/0.1.0',context,throughExclusiveXid:'20',coverageEvidenceSha256:'a'.repeat(64)};
const fixture={interfaceVersion:'truss-feed-committed-application/0.1.0',applicationIdentity:'application',worker:{context,consumerId:'consumer',registrationId:'registration',generation:'1'},downstreamIdentity:'downstream',downstreamProfile:pin,applicationProfile:pin,evidenceProfile:pin,prior:{state:'seed',context,seedId:'seed',activationEvidenceSha256:'a'.repeat(64)},applied:tx,operation:{kind:'transaction',manifest:artifact},intervalEvidence:artifact,admissionEvidence:artifact,durableTransitionInventory:artifact,commitObservation:{profile:pin,evidence:artifact}};
const cases:[string,unknown,boolean][]=[
 ['transaction',fixture,true],
 ['coverage',{...fixture,prior:{state:'transaction',boundary:tx},applied:coverage,operation:{kind:'coverage',coverage:artifact}},true],
 ['coverage prior',{...fixture,prior:{state:'coverage',boundary:coverage}},true],
 ['missing inventory',{...fixture,durableTransitionInventory:undefined},false],
 ['commit flag',{...fixture,commitObservation:true},false],
 ['extra authority',{...fixture,verified:true},false],
 ['numeric xid',{...fixture,applied:{...tx,xid:10}},false],
 ['unknown prior',{...fixture,prior:{state:'current'}},false],
 ['missing manifest',{...fixture,operation:{kind:'transaction'}},false],
 ['mixed operation',{...fixture,operation:{kind:'coverage',coverage:artifact,manifest:artifact}},false],
 ['missing registration',{...fixture,worker:{...fixture.worker,registrationId:undefined}},false],
 ['conflicting context needs semantic refusal',{...fixture,applied:{...tx,context:{...context,sourceEpoch:'other'}}},true],
 ['wrong operation-result domain needs semantic refusal',{...fixture,applied:coverage},true],
 ['forged native commit needs semantic refusal',{...fixture,commitObservation:{profile:pin,evidence:{...artifact,identity:'forged'}}},true]
];
const failures=cases.filter(([,v,e])=>Boolean(validate(v))!==e).map(([n])=>n);
const receipt={scope:'Committed application wire shape only; no source completeness/native fence/commit/custody proof',cases:cases.length,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/feed-application-evidence.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
