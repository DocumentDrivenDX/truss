/** Shape only; no native model/inventory/identifier or resource admission. */
const {default:Ajv}=await import(process.argv[2]);
const root='docs/helix/02-design/contracts/';
const validate=new Ajv({strict:true}).addSchema(await Bun.file(root+'acceptance-input-v0.1.schema.json').json()).compile(await Bun.file(root+'bootstrap-bundle-v0.1.schema.json').json());
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)},artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const fixture={interfaceVersion:'truss-bootstrap-bundle/0.1.0',layoutVersion:'draft',model:{document:artifact,coreVersion:'0.7.0',vocabularies:[pin],nativeProfile:pin},generator:{operation:pin,backend:pin},target:{postgresqlVersion:'17.4',encoding:'UTF8',localeProfile:pin,settings:artifact},names:{schema:'truss',identifierMap:artifact,profile:pin},initialization:{profile:pin,orderedInput:artifact},expectedCatalog:{profile:pin,inventory:artifact},canonicalizationProfile:pin};
const cases:[string,unknown,boolean][]=[
 ['complete',fixture,true],['unknown layout field',{...fixture,ready:true},false],
 ['missing inventory',{...fixture,expectedCatalog:undefined},false],
 ['unversioned generator',{...fixture,generator:{operation:'exportPostgresqlSql',backend:pin}},false],
 ['wrong root version',{...fixture,interfaceVersion:'truss-bootstrap-bundle/9.0.0'},false],
 ['connection string field',{...fixture,target:{...fixture.target,connectionString:'fixture'}},false],
 ['unknown nested selected meaning',{...fixture,initialization:{...fixture.initialization,execute:true}},false],
 ['forged artifact digest needs semantic refusal',{...fixture,model:{...fixture.model,document:{...artifact,sha256:'b'.repeat(64)}}},true],
 ['unsupported version needs semantic refusal',{...fixture,target:{...fixture.target,postgresqlVersion:'999.0'}},true],
 ['empty native bytes need semantic refusal',{...fixture,model:{...fixture.model,document:{...artifact,bytesBase64:''}}},true]
];
const failures=cases.filter(([,v,e])=>Boolean(validate(v))!==e).map(([n])=>n);
const receipt={scope:'Bootstrap bundle shape only; no native model/artifact/profile/inventory admission',cases:cases.length,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/bootstrap-bundle.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
