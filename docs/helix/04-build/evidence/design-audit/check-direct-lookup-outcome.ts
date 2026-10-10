/** Existing nested public outcome, not native admission or termination evidence. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
const root='docs/helix/02-design/contracts/';
for(const n of ['exact-value-v0.1','history-record-v0.1','direct-cursor-v0.1','direct-page-result-v0.1','direct-lookup-result-v0.1','execution-failure-v0.1'])
 ajv.addSchema(await Bun.file(root+n+'.schema.json').json());
const validate=ajv.compile(await Bun.file(root+'direct-lookup-execution-outcome-v0.1.proposal.schema.json').json());
const cases:[string,unknown,boolean][]=[
 ['nested not found',{status:'ok',value:{outcome:'not_found'}},true],
 ['nested business unavailable',{status:'ok',value:{outcome:'unavailable',reason:'resource'}},true],
 ['execution retry',{status:'error',error:{code:'retry',retryScope:'whole_transaction',message:'fixture'}},true],
 ['flattened result',{outcome:'not_found'},false],
 ['business error masquerades as execution failure',{status:'error',error:{outcome:'unavailable',reason:'resource'}},false],
 ['forbidden record',{status:'ok',value:{outcome:'not_found',record:{}}},false],
 ['lookup does not prove commit',{status:'ok',value:{outcome:'not_found'},durability:'committed'},false],
 ['execution error has no success value',{status:'error',error:{code:'retry',retryScope:'whole_transaction',message:'fixture'},value:{outcome:'not_found'}},false]
];
for(const [name,value,wanted] of cases)if(Boolean(validate(value))!==wanted)throw Error(name+': '+JSON.stringify(validate.errors));
console.log(cases.length+' nested lookup outcome shape controls passed; business unavailable is shape-valid but fails the missing-object case. No native termination evidence.');
export {};
