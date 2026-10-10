/** Complete manifest wire shape only; approved coverage/custody/independence is semantic. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
for(const file of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+file).json());
const validate=ajv.getSchema('urn:truss:draft:conformance-manifest:0.1.0')!;
const artifact={identity:'original',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const pin={identity:'profile',version:'0.1.0',sha256:'b'.repeat(64)};
const common={id:'case',coverage:['US-028-AC1'],procedureProfile:pin,fixtures:artifact,inputs:artifact,expected:artifact,identityAliases:artifact,observer:{kind:'native',profile:pin},isolationProfile:pin,cleanupProfile:pin,producerProvenance:artifact,requiredSurfaces:['result','state','journal','report'],resourceRequirements:artifact};
const single={...common,mode:'single',implementationProfile:pin};
const cross={...common,mode:'interchange',implementationA:pin,implementationB:pin,independenceRequirements:artifact};
const base={interfaceVersion:'truss-conformance-manifest/0.1.0',qualificationProfile:pin,corpusProfile:pin,targetProfile:pin,contractInventory:artifact,inputInventory:artifact,resourceProfile:pin,cases:[single],explicitHostExtensionExclusions:artifact};
const {expected:omitted,...noExpected}=single;
const cases:[string,unknown,boolean][]=[
 ['complete single manifest',base,true],['complete interchange manifest',{...base,cases:[cross]},true],['approved component shape',{...base,cases:[{...single,observer:{kind:'component',profile:pin},requiredSurfaces:['result']}]},true],
 ['no empty manifest',{...base,cases:[]},false],['no executable command',{...base,cases:[{...single,command:'arbitrary'}]},false],['no missing expectations',{...base,cases:[noExpected]},false],['single cannot fabricate second implementation',{...base,cases:[{...single,implementationB:pin}]},false],['no unknown observation layer',{...base,cases:[{...single,observer:{kind:'caller_claim',profile:pin}}]},false],
 ['duplicate ids need semantic refusal',{...base,cases:[single,single]},true],['same implementation pair needs independence admission',{...base,cases:[cross]},true],['component interchange needs native refusal',{...base,cases:[{...cross,observer:{kind:'component',profile:pin}}]},true],['false coverage needs approved manifest refusal',{...base,cases:[{...single,coverage:['unrelated']}]},true]
];
const failures=cases.filter(([,value,expected])=>Boolean(validate(value))!==expected).map(([name])=>name);
console.log(JSON.stringify({scope:'required conformance manifest fields only; no completeness/custody/independent/native qualification',cases:cases.length,failures},null,2));if(failures.length)process.exit(1);void omitted;export {};
