/** Existing catalog facade composition; no accepted report/head or native admission. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
const root='docs/helix/02-design/contracts/';
for(const file of new Bun.Glob('*.schema.json').scanSync(root))ajv.addSchema(await Bun.file(root+file).json());
const id='urn:truss:proposal:catalog-capability-wires:0.1.0';
const pin={identity:'fixture',version:'0.1',sha256:'a'.repeat(64)};
const rejection={interfaceVersion:'truss-acceptance-rejection/0.1.0',reportProfile:pin,completeness:{state:'complete'},diagnostics:[]};
const cases:[string,string,unknown,boolean][]=[
 ['report request','reportRequest',{interfaceVersion:'truss-acceptance-report-request/0.1.0',revision:'1'},true],
 ['request no guessed scope member','reportRequest',{interfaceVersion:'truss-acceptance-report-request/0.1.0',revision:'1',transactionId:'caller'},false],
 ['rejected business result','acceptanceSemantic',{outcome:'rejected',rejection},true],
 ['rejection no accepted report','acceptanceSemantic',{outcome:'rejected',rejection,report:{}},false],
 ['accepted requires full report','acceptanceSemantic',{outcome:'accepted',disposition:'new'},false],
 ['malformed accepted branch','acceptanceSemantic',{outcome:'accepted',disposition:'reactivated',report:{}},false],
 ['rejection nested in success execution','acceptanceOutcome',{status:'ok',value:{outcome:'rejected',rejection}},true],
 ['rejection not execution error','acceptanceOutcome',{status:'error',error:{outcome:'rejected',rejection}},false],
 ['not found report','reportSemantic',{outcome:'not_found'},true],
 ['report unavailable','reportSemantic',{outcome:'unavailable',reason:'retention'},true],
 ['unavailable no report','reportSemantic',{outcome:'unavailable',reason:'retention',report:{}},false],
 ['available requires report','reportSemantic',{outcome:'available'},false],
 ['report nested return','reportOutcome',{status:'ok',value:{outcome:'not_found'}},true],
 ['report does not commit','reportOutcome',{status:'ok',value:{outcome:'not_found'},durability:'committed'},false]
];
for(const [name,member,value,wanted] of cases){const validate=ajv.getSchema(id+'#/$defs/'+member);if(!validate||Boolean(validate(value))!==wanted)throw Error(name);}
console.log(cases.length+' catalog composition controls passed. Empty complete rejection diagnostics are only shape evidence; semantic completeness and accepted publication remain unqualified.');
export {};
