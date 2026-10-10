/** Closed shape probes only; independent native membership remains open. */
const {default:Ajv}=await import(process.argv[2]);
const ajv=new Ajv({strict:true});
for(const name of ['acceptance-input','exact-value','history-record','import-report'])ajv.addSchema(await Bun.file(`docs/helix/02-design/contracts/${name}-v0.1.schema.json`).json());
const validate=ajv.compile(await Bun.file('docs/helix/02-design/contracts/seed-baseline-inventory-v0.1.schema.json').json());
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)},artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const attempt={interfaceVersion:'truss-seed-activation/0.1.0',seedId:'seed',worker:{context:{sourceEpoch:'epoch',feedProfile:'draft',scopeIdentity:'scope'},consumerId:'consumer',registrationId:'registration',generation:'1'},activationProfile:pin};
const typed={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'doc',moduleId:'module'}};
const entry={ordinal:'0',identity:{kind:'record',entityKind:'object',identity:typed},payloadSha256:'a'.repeat(64),retainedOwnerEvidence:artifact};
const fixture={interfaceVersion:'truss-seed-baseline-inventory/0.1.0',attempt,inventoryProfile:pin,baselineSha256:'b'.repeat(64),visibilityManifestSha256:'c'.repeat(64),entries:[entry],extractionObservation:artifact};
const cases:[string,unknown,boolean][]=[['record',fixture,true],['empty needs independent enumeration',{...fixture,entries:[]},true],['missing owner',{...fixture,entries:[{...entry,retainedOwnerEvidence:undefined}]},false],['numeric ordinal',{...fixture,entries:[{...entry,ordinal:0}]},false],['unknown family',{...fixture,entries:[{...entry,identity:{kind:'future'}}]},false],['abbreviated identity',{...fixture,entries:[{...entry,identity:{kind:'record',entityKind:'object',identity:{id:'1'}}}]},false],['duplicate needs semantic refusal',{...fixture,entries:[entry,entry]},true],['wrong ordinal needs semantic refusal',{...fixture,entries:[{...entry,ordinal:'7'}]},true]];
const withIdentity=(identity:unknown)=>({...fixture,entries:[{...entry,identity}]});
const objectReservation={interfaceVersion:'truss-feed-reservation/0.1.0',priorIdentity:typed,priorVersion:'2',createdCatalogRevision:'1',reservation:{kind:'object_key',keyNumber:'1',keyDefinitionPin:'key',keyEncodingProfile:pin,encodedKey:'exact'}};
const edgeReservation={...objectReservation,reservation:{kind:'edge_endpoints',relationshipDefinitionPin:'relationship',source:typed,target:{...typed,id:'2'},keyNumber:'0',keyEncodingProfile:pin,encodedKey:'exact-endpoints'}};
const configuration={sourceEpoch:'epoch',installationId:'installation',generation:'1',keyReuse:'forbid',journalMode:'engine',configurationProfile:pin,installedProducerInventorySha256:'d'.repeat(64)};
cases.push(
 ['edge record',withIdentity({kind:'record',entityKind:'edge',identity:typed}),true],
 ['source',withIdentity({kind:'source',entityKind:'object',identity:typed}),true],
 ['revision',withIdentity({kind:'revision',revision:'1'}),true],
 ['object reservation',withIdentity({kind:'reservation',reservation:objectReservation}),true],
 ['edge reservation',withIdentity({kind:'reservation',reservation:edgeReservation}),true],
 ['configuration',withIdentity({kind:'configuration',configuration}),true],
 ['archive',withIdentity({kind:'retained_archive',archiveProfile:pin,artifactIdentity:'archive'}),true],
 ['edge wrong key number',withIdentity({kind:'reservation',reservation:{...edgeReservation,reservation:{...edgeReservation.reservation,keyNumber:'1'}}}),false],
 ['reservation missing original version',withIdentity({kind:'reservation',reservation:{...objectReservation,priorVersion:undefined}}),false],
 ['configuration missing producer',withIdentity({kind:'configuration',configuration:{...configuration,installedProducerInventorySha256:undefined}}),false],
 ['archive missing profile',withIdentity({kind:'retained_archive',artifactIdentity:'archive'}),false],
 ['configuration wrong epoch needs semantic refusal',withIdentity({kind:'configuration',configuration:{...configuration,sourceEpoch:'other'}}),true]
);
const failures=cases.filter(([,v,e])=>Boolean(validate(v))!==e).map(([n])=>n);
const receipt={scope:'Baseline inventory shape only; no correspondence, completeness, native identity or authority qualification',cases:cases.length,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/seed-inventory.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
