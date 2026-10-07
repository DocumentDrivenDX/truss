/** Baseline shape only; no independent complete-cut/native extraction evidence. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
for(const name of ['acceptance-input','exact-value','history-record','import-report','seed-baseline-inventory'])ajv.addSchema(await Bun.file(`docs/helix/02-design/contracts/${name}-v0.1.schema.json`).json());
const validate=ajv.compile(await Bun.file('docs/helix/02-design/contracts/seed-baseline-v0.1.schema.json').json());
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)},artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const attempt={interfaceVersion:'truss-seed-activation/0.1.0',seedId:'seed',worker:{context:{sourceEpoch:'epoch',feedProfile:'draft',scopeIdentity:'scope'},consumerId:'consumer',registrationId:'registration',generation:'1'},activationProfile:pin};
const fixture={interfaceVersion:'truss-seed-baseline/0.1.0',attempt,baselineProfile:pin,layoutProfile:pin,valueProfile:pin,interpretationProfile:pin,catalogRevision:'1',snapshotEvidence:artifact,records:[],revisions:[],sources:[],reservations:[],configurations:[],retainedArchives:[]};
const typed={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'doc',moduleId:'module'}};
const source={interfaceVersion:'truss-feed-source/0.1.0',identity:typed,loadId:'load',createdCatalogRevision:'1',source:{author:null,at:'opaque',extensions:[{name:'unknown',value:{kind:'decimal',text:'1.00'}}]},endpoints:{kind:'object'}};
const cases:[string,unknown,boolean][]=[['empty needs independent completeness',fixture,true],['exact source',{...fixture,sources:[source]},true],['edge source',{...fixture,sources:[{...source,endpoints:{kind:'edge',source:typed,target:{...typed,id:'2'}}}]},true],['unknown root',{...fixture,partial:true},false],['missing snapshot',{...fixture,snapshotEvidence:undefined},false],['numeric source time',{...fixture,sources:[{...source,source:{...source.source,at:123}}]},false],['missing extensions',{...fixture,sources:[{...source,source:{author:null}}]},false],['duplicate source needs semantic refusal',{...fixture,sources:[source,source]},true]];
const input={interfaceVersion:'truss-acceptance-input/0.1.0',layoutProfile:pin,acceptanceProfile:pin,validatorProfile:pin,supportProfile:pin,documents:[{documentId:'doc',documentRevision:'r1',artifact,umfProfile:pin,ingress:{kind:'native'}}],binding:{state:'absent'},policy:{unknownEndpoint:'reject',loss:'strict',profile:pin},transforms:[]};
const record={interfaceVersion:'truss-history-record/0.1.0',identity:typed,recordVersion:'1',catalogRevision:'1',createdAt:'fixture',updatedAt:'fixture',properties:[{propertyId:'1',definitionPin:'fixture',value:{kind:'decimal',text:'1.00'}}],retained:[],kind:'object',ownership:{state:'rootless'}};
const revision={interfaceVersion:'truss-feed-revision/0.1.0',revision:'1',acceptedAt:'fixture',input,report:artifact,origin:{asserted:{kind:'null'},databaseRole:'role'}};
const reservation={interfaceVersion:'truss-feed-reservation/0.1.0',priorIdentity:typed,priorVersion:'1',createdCatalogRevision:'1',reservation:{kind:'object_key',keyNumber:'1',keyDefinitionPin:'key',keyEncodingProfile:pin,encodedKey:'exact'}};
const configuration={configuration:{sourceEpoch:'epoch',installationId:'installation',generation:'1',keyReuse:'forbid',journalMode:'engine',configurationProfile:pin,installedProducerInventorySha256:'d'.repeat(64)},artifact};
cases.push(
 ['live exact record',{...fixture,records:[record]},true],
 ['original revision input',{...fixture,revisions:[revision]},true],
 ['reservation',{...fixture,reservations:[reservation]},true],
 ['configuration',{...fixture,configurations:[configuration]},true],
 ['retained archive',{...fixture,retainedArchives:[{archiveProfile:pin,artifact}]},true],
 ['revision missing input',{...fixture,revisions:[{...revision,input:undefined}]},false],
 ['configuration missing bytes',{...fixture,configurations:[{configuration:configuration.configuration}]},false],
 ['archive missing profile',{...fixture,retainedArchives:[{artifact}]},false],
 ['record wrong catalog needs semantic refusal',{...fixture,records:[{...record,catalogRevision:'99'}]},true],
 ['snapshot artifact requires semantic byte admission',{...fixture,snapshotEvidence:{...artifact,identity:'forged'}},true]
);
const failures=cases.filter(([,v,e])=>Boolean(validate(v))!==e).map(([n])=>n);const receipt={scope:'Baseline closed shape only; no membership/canonical/native/authority qualification',cases:cases.length,failures};await Bun.write('docs/helix/04-build/evidence/design-audit/seed-baseline.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
