/** Serialized request shape only; no metering/custody/native qualification. */
const {default:Ajv}=await import(process.argv[2]);
const root='docs/helix/02-design/contracts/';
const ajv=new Ajv({strict:true});
for(const n of ['acceptance-input','bootstrap-bundle'])ajv.addSchema(await Bun.file(root+n+'-v0.1.schema.json').json());
const validate=ajv.compile(await Bun.file(root+'bootstrap-generation-v0.1.schema.json').json());
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)},artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const bundle={interfaceVersion:'truss-bootstrap-bundle/0.1.0',layoutVersion:'draft',model:{document:artifact,coreVersion:'0.7.0',vocabularies:[pin],nativeProfile:pin},generator:{operation:pin,backend:pin},target:{postgresqlVersion:'17.4',encoding:'UTF8',localeProfile:pin,settings:artifact},names:{schema:'truss',identifierMap:artifact,profile:pin},initialization:{profile:pin,orderedInput:artifact},expectedCatalog:{profile:pin,inventory:artifact},canonicalizationProfile:pin};
const fixture={interfaceVersion:'truss-bootstrap-generation/0.1.0',bundle,resourceProfile:pin,qualification:{state:'absent'},limits:{inputBytes:'1000',outputBytes:'1000',statements:'10',workUnits:'100'}};
const supplied={state:'supplied',targetProfile:pin,evidence:artifact};
const cases:[string,unknown,boolean][]=[
 ['absent',fixture,true],['supplied',{...fixture,qualification:supplied},true],
 ['missing qualification',{...fixture,qualification:undefined},false],
 ['missing supplied evidence',{...fixture,qualification:{state:'supplied',targetProfile:pin}},false],
 ['qualification flag',{...fixture,qualification:{state:'qualified'}},false],
 ['numeric limit',{...fixture,limits:{...fixture.limits,outputBytes:1000}},false],
 ['zero limit',{...fixture,limits:{...fixture.limits,workUnits:'0'}},false],
 ['noncanonical limit',{...fixture,limits:{...fixture.limits,inputBytes:'01000'}},false],
 ['serialized signal',{...fixture,signal:{}},false],
 ['unsupported resource requires semantic refusal',{...fixture,resourceProfile:{...pin,identity:'unsupported'}},true],
 ['forged native evidence requires semantic refusal',{...fixture,qualification:{...supplied,evidence:{...artifact,identity:'forged'}}},true]
];
const failures=cases.filter(([,v,e])=>Boolean(validate(v))!==e).map(([n])=>n);
const receipt={scope:'Generation request wire shape only; no metering/native qualification/custody admission',cases:cases.length,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/bootstrap-generation.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
