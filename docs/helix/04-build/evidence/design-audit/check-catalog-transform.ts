/** Callback wire shapes; not purity/totality/native candidate admission. */
const {default:Ajv}=await import(process.argv[2]);const a=new Ajv({strict:true});
for(const n of ['acceptance-input','exact-value','history-record'])a.addSchema(await Bun.file(`docs/helix/02-design/contracts/${n}-v0.1.schema.json`).json());
const input=a.compile(await Bun.file('docs/helix/02-design/contracts/catalog-transform-input-v0.1.schema.json').json());const result=a.compile(await Bun.file('docs/helix/02-design/contracts/catalog-transform-result-v0.1.schema.json').json());
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const v={interfaceVersion:'truss-catalog-transform/0.1.0',registration:pin,dependencyProfile:pin,targetDefinitionIdentity:'target',beforeDefinitionPin:'old',afterDefinitionPin:'new',priorCatalogRevision:'1',candidateCatalogRevision:'2',record:{id:'1',typeId:'1',definitionPin:'old-type',owner:{documentId:'doc',moduleId:'module'}},propertyId:'field',before:{present:false},dependencies:[],parameters:null};
const dep={propertyId:'other',definitionPin:'old',before:{present:true,value:{kind:'null'}}};
const cases:[any,string,unknown,boolean][]=[
 [input,'absent input',v,true],[input,'null preserved',{...v,before:{present:true,value:{kind:'null'}},dependencies:[dep]},true],
 [input,'parameters no host numbers',{...v,parameters:1},false],[input,'absence no value',{...v,before:{present:false,value:{kind:'null'}}},false],
 [input,'no candidate dependency access',{...v,dependencies:[{...dep,after:{present:false}}]},false],
 [input,'no callback source code',{...v,source:'return null'},false],
 [input,'duplicate dependencies semantic refusal',{...v,dependencies:[dep,dep]},true],
 [input,'wrong candidate revision semantic refusal',{...v,candidateCatalogRevision:'1'},true],
 [result,'candidate null',{outcome:'candidate',after:{present:true,value:{kind:'null'}}},true],
 [result,'candidate absence',{outcome:'candidate',after:{present:false}},true],
 [result,'rejected',{outcome:'rejected',code:'unsupported',path:[]},true],
 [result,'rejected no partial output',{outcome:'rejected',code:'unsupported',path:[],after:{present:false}},false],
 [result,'candidate no native commit',{outcome:'candidate',after:{present:false},committed:true},false]
];
const manifest=a.compile(await Bun.file('docs/helix/02-design/contracts/catalog-transform-manifest-v0.1.schema.json').json());
const metadata={interfaceVersion:'truss-catalog-transform-manifest/0.1.0',implementationProfile:pin,resourceProfile:pin,execution:{kind:'trusted_cooperative'},inputValueProfile:pin,outputValueProfile:pin,dependencyProfile:pin,declaredDependencies:[],supportedDefinitionPairs:[{beforeDefinitionPin:'old',afterDefinitionPin:'new'}]};
cases.push([manifest,'registration manifest',metadata,true],
 [manifest,'isolated needs execution profile',{...metadata,execution:{kind:'isolated'}},false],
 [manifest,'manifest requires implementation',Object.fromEntries(Object.entries(metadata).filter(([k])=>k!=='implementationProfile')),false],
 [manifest,'empty supported pairs rejects',{...metadata,supportedDefinitionPairs:[]},false],
 [manifest,'no executable source manifest',{...metadata,source:'return null'},false],
 [manifest,'duplicate pair needs semantic refusal',{...metadata,supportedDefinitionPairs:[...metadata.supportedDefinitionPairs,...metadata.supportedDefinitionPairs]},true]);
const failures=cases.filter(([c,,v,e])=>Boolean(c(v))!==e).map(([,n])=>n);console.log(JSON.stringify({scope:'transform callback wire shapes, not semantic/purity evidence',cases:cases.length,failures},null,2));if(failures.length)process.exit(1);export {};
