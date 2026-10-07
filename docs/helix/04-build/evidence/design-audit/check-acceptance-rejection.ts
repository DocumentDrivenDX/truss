/** Structural design evidence only. */
const {default:Ajv}=await import(process.argv[2]);
const input=await Bun.file('docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json').json();
const schema=await Bun.file('docs/helix/02-design/contracts/acceptance-rejection-v0.1.schema.json').json();
const validate=new Ajv({strict:true}).addSchema(input).compile(schema);
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const artifact={identity:'diagnostic',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const diagnostic={classification:'truss_admission',source:{kind:'input'},diagnosticProfile:pin,diagnostic:artifact};
const report={interfaceVersion:'truss-acceptance-rejection/0.1.0',reportProfile:pin,completeness:{state:'complete'},diagnostics:[diagnostic]};
const cases:[string,unknown,boolean][]=[
 ['complete',report,true],
 ['incomplete',{...report,completeness:{state:'incomplete',reason:'resource'}},true],
 ['document',{...report,diagnostics:[{...diagnostic,source:{kind:'document',artifact,sourcePointer:'/types/0'}}]},true],
 ['accepted revision',{...report,acceptedRevision:'2'},false],
 ['incomplete without reason',{...report,completeness:{state:'incomplete'}},false],
 ['complete with reason',{...report,completeness:{state:'complete',reason:'resource'}},false],
 ['unknown source',{...report,diagnostics:[{...diagnostic,source:{kind:'other'}}]},false],
 ['missing diagnostic bytes',{...report,diagnostics:[{...diagnostic,diagnostic:{identity:'diagnostic',sha256:'a'.repeat(64)}}]},false],
 ['empty refusal remains semantic',{...report,diagnostics:[]},true],
 ['forged artifact remains semantic',report,true]
];
const failures=cases.filter(([,value,expected])=>Boolean(validate(value))!==expected).map(([name])=>name);
console.log(JSON.stringify({scope:'rejection shape only; no completeness/provenance/rollback evidence',cases:cases.length,failures},null,2));
if(failures.length)process.exit(1);
export {};
