/** Shape probes only; no scope/native watermark qualification. */
const {default:Ajv}=await import(process.argv[2]);
const base=await Bun.file('docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json').json();
const schema=await Bun.file('docs/helix/02-design/contracts/journal-page-request-v0.1.schema.json').json();
const validate=new Ajv({strict:true}).addSchema(base).compile(schema);
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const context={sourceEpoch:'epoch',scopeIdentity:'scope',journalProfile:pin,observationProfile:pin,snapshot:{state:'statement'}};
const first={interfaceVersion:'truss-journal-page/0.1.0',context,continuation:{state:'first'},limits:{rows:'10',encodedBytes:'10000'}};
const cursor={interfaceVersion:'truss-journal-cursor/0.1.0',context,after:{xid:'1',seq:'2'}};
const cases:[string,unknown,boolean][]=[
 ['first',first,true],['continuation',{...first,continuation:{state:'after',cursor}},true],
 ['zero limit',{...first,limits:{rows:'0',encodedBytes:'10000'}},false],
 ['numeric position',{...first,continuation:{state:'after',cursor:{...cursor,after:{xid:1,seq:2}}}},false],
 ['leading zero',{...first,continuation:{state:'after',cursor:{...cursor,after:{xid:'01',seq:'2'}}}},false],
 ['held missing identity',{...first,context:{...context,snapshot:{state:'held'}}},false],
 ['unknown authority',{...first,authorized:true},false],
 ['forged scope needs semantic admission',{...first,context:{...context,scopeIdentity:'forged'}},true],
 ['cross context needs semantic admission',{...first,continuation:{state:'after',cursor:{...cursor,context:{...context,sourceEpoch:'other'}}}},true]
];
const failures=cases.filter(([,v,e])=>Boolean(validate(v))!==e).map(([n])=>n);
const receipt={scope:'Draft journal request/cursor shape only; no native bounds, authority, horizon, snapshot or ordering qualification',cases:cases.length,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/journal-page.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
const resultAjv=new Ajv({strict:true}).addSchema(base).addSchema(schema);
for(const name of ['exact-value','history-record','history-event'])resultAjv.addSchema(await Bun.file(`docs/helix/02-design/contracts/${name}-v0.1.schema.json`).json());
const resultValidate=resultAjv.compile(await Bun.file('docs/helix/02-design/contracts/journal-page-result-v0.1.schema.json').json());
const result={outcome:'page',context,events:[],safeWatermarkXid:'10',continuation:{state:'end'},observation:{identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)}};
const event={interfaceVersion:'truss-history-event/0.1.0',sourceEpoch:'epoch',historyProfile:'draft',xid:'1',seq:'2',identity:{id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'doc',moduleId:'module'}},eventVersion:'2',eventCatalogRevision:'1',mutationGroup:{profile:'truss-history-group/0.1.0',eventCount:'1',orderedEventDigest:'0'.repeat(64)},origin:{asserted:{kind:'null'},databaseRole:'fixture'},operation:'property',propertyId:'1',definitionPin:'fixture',before:{present:false},after:{present:true,value:{kind:'decimal',text:'1.00'}}};
const resultCases:[string,unknown,boolean][]=[
 ['exact property event',{...result,events:[event]},true],
 ['more names returned event',{...result,events:[event],continuation:{state:'more',cursor}},true],
 ['event at watermark needs semantic refusal',{...result,events:[{...event,xid:'10'}]},true],
 ['event wrong epoch needs semantic refusal',{...result,events:[{...event,sourceEpoch:'other'}]},true],
 ['out of order needs semantic refusal',{...result,events:[{...event,seq:'3'},event]},true],
 ['wrong last cursor needs semantic refusal',{...result,events:[event],continuation:{state:'more',cursor:{...cursor,after:{xid:'1',seq:'99'}}}},true],
 ['empty observed page',result,true],['unavailable',{outcome:'unavailable',reason:'retention'},true],
 ['unavailable payload',{outcome:'unavailable',reason:'authorization',events:[]},false],
 ['missing evidence',{...result,observation:undefined},false],
 ['more missing cursor',{...result,continuation:{state:'more'}},false],
 ['end carries cursor',{...result,continuation:{state:'end',cursor}},false],
 ['numeric watermark',{...result,safeWatermarkXid:10},false],
 ['unknown event',{...result,events:[{operation:'future'}]},false],
 ['forged context remains semantic',{...result,context:{...context,sourceEpoch:'forged'}},true],
 ['empty more needs semantic refusal',{...result,continuation:{state:'more',cursor}},true]
];
const resultFailures=resultCases.filter(([,v,e])=>Boolean(resultValidate(v))!==e).map(([n])=>n);
const resultReceipt={scope:'Journal result shape only; ordering, watermark, cursor, epoch and empty-more require semantic refusal; no native qualification',cases:resultCases.length,failures:resultFailures};
await Bun.write('docs/helix/04-build/evidence/design-audit/journal-page-result.json',JSON.stringify(resultReceipt,null,2)+'\n');
console.log(JSON.stringify(resultReceipt));if(resultFailures.length)process.exit(1);
