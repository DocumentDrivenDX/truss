/** Shape only; source completeness and downstream durability require native evidence. */
const {default:Ajv}=await import(process.argv[2]);
const root='docs/helix/02-design/contracts/';
const base=await Bun.file(root+'acceptance-input-v0.1.schema.json').json();
const schema=await Bun.file(root+'feed-interval-coverage-v0.1.schema.json').json();
const validate=new Ajv({strict:true}).addSchema(base).compile(schema);
const sha='a'.repeat(64),pin={identity:'fixture',version:'0.1.0',sha256:sha};
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:sha};
const represented={xid:'10',manifestSha256:sha,disposition:{kind:'represented',visibilityManifestSha256:sha}};
const applied={xid:'14',manifestSha256:sha,disposition:{kind:'applied',committedApplicationEvidenceSha256:sha}};
const fixture={interfaceVersion:'truss-feed-coverage/0.1.0',context:{sourceEpoch:'epoch',feedProfile:'draft',scopeIdentity:'scope'},fromInclusiveXid:'10',throughExclusiveXid:'20',observedSafeWatermarkXid:'20',sourceEnumerationEvidence:artifact,retentionProtectionEvidence:artifact,transactions:[represented,applied],coverageProfile:pin};
const cases:[string,unknown,boolean][]=[
 ['mixed',fixture,true],['empty protected interval',{...fixture,transactions:[]},true],
 ['missing source enumeration',{...fixture,sourceEnumerationEvidence:undefined},false],
 ['missing protection',{...fixture,retentionProtectionEvidence:undefined},false],
 ['numeric frontier',{...fixture,throughExclusiveXid:20},false],
 ['leading-zero xid',{...fixture,fromInclusiveXid:'010'},false],
 ['skip disposition',{...fixture,transactions:[{...applied,disposition:{kind:'skipped'}}]},false],
 ['missing application digest',{...fixture,transactions:[{...applied,disposition:{kind:'applied'}}]},false],
 ['mixed disposition',{...fixture,transactions:[{...represented,disposition:{...represented.disposition,committedApplicationEvidenceSha256:sha}}]},false],
 ['duplicate membership requires semantic refusal',{...fixture,transactions:[represented,represented]},true],
 ['unordered membership requires semantic refusal',{...fixture,transactions:[applied,represented]},true],
 ['out-of-interval membership requires semantic refusal',{...fixture,transactions:[{...applied,xid:'20'}]},true],
 ['beyond watermark requires semantic refusal',{...fixture,observedSafeWatermarkXid:'19'},true],
 ['reversed interval requires semantic refusal',{...fixture,fromInclusiveXid:'21'},true],
 ['forged protection requires semantic refusal',{...fixture,retentionProtectionEvidence:{...artifact,identity:'forged'}},true]
];
const failures=cases.filter(([,v,e])=>Boolean(validate(v))!==e).map(([n])=>n);
const receipt={scope:'Interval coverage shape only; no native complete membership/protection/effects proof',cases:cases.length,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/feed-interval-coverage.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
