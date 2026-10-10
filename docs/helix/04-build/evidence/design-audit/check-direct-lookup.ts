/** Lookup wire witnesses; original key/record/authority correspondence is independently required. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
for(const n of ['exact-value','history-record','direct-cursor','direct-page-result'])a.addSchema(await Bun.file(`docs/helix/02-design/contracts/${n}-v0.1.schema.json`).json());
const request=a.compile(await Bun.file('docs/helix/02-design/contracts/direct-lookup-request-v0.1.schema.json').json());
const result=a.compile(await Bun.file('docs/helix/02-design/contracts/direct-lookup-result-v0.1.schema.json').json());
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const owner={documentId:'doc',moduleId:'module'};const type={typeId:'1',definitionPin:'fixture',owner};
const context={catalogRevision:'2',layoutProfile:pin,readProfile:pin,authorizedScopeIdentity:'scope',consistency:{kind:'live'}};
const component={propertyId:'1',definitionPin:'fixture',value:{kind:'decimal',text:'1.00'}};
const key={context,selection:{operation:'object_key',type,keyNumber:'0',keyDefinitionPin:'fixture',keyEncodingProfile:pin,components:[component]}};
const record={view:'current',readCatalogRevision:'2',record:{interfaceVersion:'truss-history-record/0.1.0',kind:'object',identity:{id:'9007199254740993',...type},recordVersion:'1',catalogRevision:'1',createdAt:'fixture',updatedAt:'fixture',properties:[],retained:[],ownership:{state:'rootless'}}};
const found={outcome:'found',context,record};
const requests:[string,unknown,boolean][]=[
 ['object id',{context,selection:{operation:'object_id',type,id:'9007199254740993'}},true],
 ['edge id',{context,selection:{operation:'edge_id',id:'2'}},true],['ordered key',key,true],
 ['empty components',{...key,selection:{...key.selection,components:[]}},false],
 ['host key number',{...key,selection:{...key.selection,keyNumber:0}},false],
 ['key number alias',{...key,selection:{...key.selection,keyNumber:'00'}},false],
 ['presence wrapper is not exact value',{...key,selection:{...key.selection,components:[{...component,value:{present:true,value:component.value}}]}},false],
 ['edge cannot assert type',{context,selection:{operation:'edge_id',id:'2',type}},false],
 ['duplicate components needs semantic refusal',{...key,selection:{...key.selection,components:[component,component]}},true],
 ['forged encoding profile needs semantic refusal',{...key,selection:{...key.selection,keyEncodingProfile:{...pin,sha256:'b'.repeat(64)}}},true],
 ['native identity grammar remains semantic',{context,selection:{operation:'object_id',type,id:'unsupported'}},true]
];
const results:[string,unknown,boolean][]=[
 ['found',found,true],['not found',{outcome:'not_found'},true],
 ['invalid',{outcome:'invalid',code:'key',path:['selection','components']},true],
 ['resource',{outcome:'unavailable',reason:'resource'},true],
 ['not found no record',{outcome:'not_found',record},false],
 ['unavailable no record',{outcome:'unavailable',reason:'resource',record},false],
 ['invalid no hidden context',{outcome:'invalid',code:'key',path:[],context},false],
 ['found needs record',{outcome:'found',context},false],
 ['transport failure not admission',{outcome:'unavailable',reason:'connection_lost'},false],
 ['wrong read revision needs semantic refusal',{...found,record:{...record,readCatalogRevision:'3'}},true],
 ['wrong returned identity needs native refusal',{...found,record:{...record,record:{...record.record,identity:{...record.record.identity,id:'2'}}}},true]
];
const failures=[...requests.filter(([,v,e])=>Boolean(request(v))!==e),...results.filter(([,v,e])=>Boolean(result(v))!==e)].map(([n])=>n);
console.log(JSON.stringify({scope:'closed lookup shapes; semantic counterexamples intentionally shape-valid',requestCases:requests.length,resultCases:results.length,failures},null,2));if(failures.length)process.exit(1);export {};
