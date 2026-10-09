/** Original retained-history carrier shapes only; no reconstruction/source truth. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
const root='docs/helix/02-design/contracts/';
for(const file of new Bun.Glob('*.schema.json').scanSync(root))ajv.addSchema(await Bun.file(root+file).json());
const id='urn:truss:proposal:retained-history-capability-wires:0.1.0';
const hash='a'.repeat(64),pin={identity:'fixture',version:'0.1',sha256:hash};
const identity={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'d',moduleId:'m'}};
const request={interfaceVersion:'truss-history-reconstruction/0.1.0',sourceEpoch:'fixture',historyProfile:pin,identity,version:'1'};
const evidence={baselineSha256:hash,eventInventorySha256:hash,definitionInventorySha256:hash,procedureProfile:pin,observationEvidenceSha256:hash};
const record={interfaceVersion:'truss-history-record/0.1.0',kind:'object',identity,recordVersion:'1',catalogRevision:'1',createdAt:'fixture',updatedAt:'fixture',properties:[],retained:[],ownership:{state:'rootless'}};
const sourceRequest={interfaceVersion:'truss-historical-source/0.1.0',sourceEpoch:'fixture',identity,sourceProfile:pin};
const sourceEvidence={creationInventorySha256:hash,retainedOwnerInventorySha256:hash,currentAuthorityObservationSha256:hash,observationProcedure:pin};
const fact={interfaceVersion:'truss-feed-source/0.1.0',identity,loadId:'fixture',createdCatalogRevision:'1',source:{author:null,at:'opaque source text',extensions:[]},endpoints:{kind:'object'}};
const cases:[string,string,unknown,boolean][]=[
 ['original request','reconstructionRequest',request,true],
 ['no current reinterpretation member','reconstructionRequest',{...request,currentCatalogRevision:'2'},false],
 ['exact version string','reconstructionRequest',{...request,version:1},false],
 ['reconstructed original record','reconstructionResult',{outcome:'reconstructed',request,record,evidence},true],
 ['reconstruction requires evidence','reconstructionResult',{outcome:'reconstructed',request,record},false],
 ['deleted evidence','reconstructionResult',{outcome:'deleted',request,deletionVersion:'2',evidence},true],
 ['deleted no record','reconstructionResult',{outcome:'deleted',request,deletionVersion:'2',evidence,record:{}},false],
 ['unwritten evidence','reconstructionResult',{outcome:'unwritten',request,nonexistenceEvidenceSha256:hash},true],
 ['unwritten needs proof','reconstructionResult',{outcome:'unwritten',request},false],
 ['not found nondisclosure','reconstructionResult',{outcome:'not_found'},true],
 ['not found no request','reconstructionResult',{outcome:'not_found',request},false],
 ['retention unavailable','reconstructionResult',{outcome:'history_unavailable',reason:'retention'},true],
 ['unsupported meaning','reconstructionResult',{outcome:'unsupported',requiredMeaning:'fixture'},true],
 ['source request','sourceRequest',sourceRequest,true],
 ['found original fact','sourceResult',{outcome:'found',request:sourceRequest,fact,evidence:sourceEvidence},true],
 ['absent original evidence','sourceResult',{outcome:'absent',request:sourceRequest,evidence:sourceEvidence},true],
 ['absence needs evidence','sourceResult',{outcome:'absent',request:sourceRequest},false],
 ['absence no fact','sourceResult',{outcome:'absent',request:sourceRequest,evidence:sourceEvidence,fact},false],
 ['source non-disclosure','sourceResult',{outcome:'not_found'},true],
 ['source hidden request','sourceResult',{outcome:'not_found',request:sourceRequest},false],
 ['creation unavailable','sourceResult',{outcome:'unavailable',reason:'creation_inventory'},true],
 ['found requires current authority evidence','sourceResult',{outcome:'found',request:sourceRequest,fact,evidence:{creationInventorySha256:hash,retainedOwnerInventorySha256:hash,observationProcedure:pin}},false],
 ['nested historical source','sourceOutcome',{status:'ok',value:{outcome:'found',request:sourceRequest,fact,evidence:sourceEvidence}},true],
 ['nested unavailable reconstruction','reconstructionOutcome',{status:'ok',value:{outcome:'history_unavailable',reason:'retention'}},true]
];
for(const [name,member,value,wanted] of cases){const validate=ajv.getSchema(id+'#/$defs/'+member);if(!validate||Boolean(validate(value))!==wanted)throw Error(name+': '+JSON.stringify(validate?.errors));}
console.log(cases.length+' retained-history composition controls passed. Original horizons, fact/evidence correspondence and current native authority remain unqualified.');
export {};
