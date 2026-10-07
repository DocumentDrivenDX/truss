/** Independent admission-wire witnesses; native membership/lookahead/authority remain unqualified. */
const {default:Ajv}=await import(process.argv[2]);
const a=new Ajv({strict:true});
for(const n of ['exact-value','history-record','direct-cursor'])a.addSchema(await Bun.file(`docs/helix/02-design/contracts/${n}-v0.1.schema.json`).json());
const check=a.compile(await Bun.file('docs/helix/02-design/contracts/direct-page-result-v0.1.schema.json').json());
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const owner={documentId:'doc',moduleId:'module'};
const context={catalogRevision:'2',layoutProfile:pin,readProfile:pin,authorizedScopeIdentity:'scope',consistency:{kind:'live'}};
const identity={id:'9007199254740993',typeId:'1',definitionPin:'fixture',owner};
const record={view:'current',readCatalogRevision:'2',record:{interfaceVersion:'truss-history-record/0.1.0',kind:'object',identity,recordVersion:'1',catalogRevision:'1',createdAt:'fixture',updatedAt:'fixture',properties:[],retained:[],ownership:{state:'rootless'}}};
const cursor={interfaceVersion:'truss-direct-cursor/0.1.0',context,selection:{operation:'objects',type:{typeId:'1',definitionPin:'fixture',owner}},after:{id:identity.id}};
const end={outcome:'page',page:{context,records:[record],continuation:{state:'end'}}};
const more={...end,page:{...end.page,continuation:{state:'more',cursor}}};
const invalid={outcome:'invalid',code:'cursor',path:['continuation']};
const unavailable={outcome:'unavailable',reason:'resource'};
const cases:[string,unknown,boolean][]=[
 ['complete end',end,true],['complete more',more,true],
 ['empty end',{...end,page:{...end.page,records:[]}},true],
 ['invalid',invalid,true],['unavailable',unavailable,true],
 ['end cannot retain cursor',{...end,page:{...end.page,continuation:{state:'end',cursor}}},false],
 ['more needs cursor',{...end,page:{...end.page,continuation:{state:'more'}}},false],
 ['failure cannot disclose partial page',{...unavailable,page:end.page},false],
 ['invalid cannot disclose records',{...invalid,records:[record]},false],
 ['unavailable needs selected reason',{outcome:'unavailable',reason:'timeout'},false],
 ['current wrapper required',{...end,page:{...end.page,records:[record.record]}},false],
 ['host number revision rejects',{...end,page:{...end.page,records:[{...record,readCatalogRevision:2}]}},false],
 ['extra commit assertion rejects',{...end,committed:true},false],
 ['wrong current revision needs semantic refusal',{...end,page:{...end.page,records:[{...record,readCatalogRevision:'3'}]}},true],
 ['cursor past lookahead needs semantic refusal',{...more,page:{...more.page,continuation:{state:'more',cursor:{...cursor,after:{id:'9007199254740994'}}}}},true],
 ['duplicate membership needs semantic refusal',{...end,page:{...end.page,records:[record,record]}},true],
 ['empty more needs semantic refusal',{...more,page:{...more.page,records:[]}},true],
 ['forged scope needs native refusal',{...end,page:{...end.page,context:{...context,authorizedScopeIdentity:'forged'}}},true]
];
const failures=cases.filter(([,v,want])=>Boolean(check(v))!==want).map(([n])=>n);
console.log(JSON.stringify({scope:'direct page result shapes; semantic counterexamples deliberately shape-valid',cases:cases.length,failures},null,2));
if(failures.length)process.exit(1);
export {};
