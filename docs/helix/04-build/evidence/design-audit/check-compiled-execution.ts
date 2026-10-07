/** Truss wrapper shape only; no Weft artifact ABI/native execution qualification. */
const {default:Ajv}=await import(process.argv[2]);
const ajv=new Ajv({strict:true});
for(const file of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+file).json());
const request=ajv.getSchema('urn:truss:draft:compiled-execution-request:0.1.0')!;
const result=ajv.getSchema('urn:truss:draft:compiled-execution-result:0.1.0')!;
const artifact={identity:'original',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const pin={identity:'bridge',version:'0.1.0',sha256:'b'.repeat(64)};
const input={interfaceVersion:'truss-compiled-execution/0.1.0',artifact,bridgeProfile:pin};
const executed={outcome:'executed',artifactSha256:'a'.repeat(64),bridgeProfile:pin,result:artifact,observation:artifact};
const refused={outcome:'refused',reason:'resource',diagnosticProfile:pin,diagnostic:artifact};
const {observation:omitted,...noObservation}=executed;
const cases:[string,'request'|'result',unknown,boolean][]=[
 ['original wrapper request','request',input,true],
 ['no replacement parameter bag','request',{...input,parameters:[]},false],
 ['no arbitrary sql','request',{...input,sql:'SELECT 1'},false],
 ['complete executed wrapper','result',executed,true],
 ['complete refusal','result',refused,true],
 ['refusal cannot disclose result','result',{...refused,result:artifact},false],
 ['execution needs original observation','result',noObservation,false],
 ['native uncertainty is outer error','result',{...refused,reason:'commit_unknown'},false],
 ['false digest needs semantic refusal','request',{...input,artifact:{...artifact,sha256:'c'.repeat(64)}},true],
 ['false observation needs native refusal','result',{...executed,observation:{...artifact,identity:'forged'}},true],
 ['unsupported nested abi needs owner admission','request',{...input,artifact:{...artifact,identity:'unknown-abi'}},true]
];
const failures=cases.filter(([,kind,value,expected])=>Boolean((kind==='request'?request:result)(value))!==expected).map(([name])=>name);
console.log(JSON.stringify({scope:'Truss compiled request/result wrapper fields only; no artifact custody/digest/native ABI proof',cases:cases.length,failures},null,2));
if(failures.length)process.exit(1);void omitted;export {};
