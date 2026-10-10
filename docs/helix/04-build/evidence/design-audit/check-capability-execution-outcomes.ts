/** Composition controls only; no native capability or complete business-result evidence. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
const root='docs/helix/02-design/contracts/';
for(const file of new Bun.Glob('*.schema.json').scanSync(root))ajv.addSchema(await Bun.file(root+file).json());
const identity='urn:truss:proposal:capability-execution-outcomes:0.1.0';
const names=['directPage','traversal','traversalRelease','journalPage','compiledExecution','feedDiscovery','feedFragment','feedFreshness','feedAcknowledgment','catalogView'];
let count=0;
for(const name of names){
 const validate=ajv.getSchema(identity+'#/$defs/'+name);if(!validate)throw Error('Missing '+name);
 const controls:[string,unknown,boolean][]=[
  ['outer retry',{status:'error',error:{code:'retry',retryScope:'whole_transaction',message:'fixture'}},true],
  ['missing inner result',{status:'ok'},false],
  ['both branches',{status:'error',error:{code:'retry',retryScope:'whole_transaction',message:'fixture'},value:{}},false],
  ['invented commit fact',{status:'error',error:{code:'retry',retryScope:'whole_transaction',message:'fixture'},durability:'committed'},false],
  ['inner unavailable is not an execution failure',{status:'error',error:{outcome:'unavailable',reason:'resource'}},false]
 ];
 for(const [label,value,wanted] of controls){if(Boolean(validate(value))!==wanted)throw Error(name+' '+label+': '+JSON.stringify(validate.errors));count++;}
}
if(ajv.getSchema(identity)!({status:'ok',value:{}}))throw Error('Definitions-only root must refuse all wires');count++;
const catalog=ajv.getSchema(identity+'#/$defs/catalogViewResult');if(!catalog)throw Error('Missing catalog view result');
for(const [value,wanted] of [[{outcome:'unavailable',reason:'closure'},true],[{outcome:'unavailable',reason:'closure',view:{}},false],[{outcome:'available'},false],[{outcome:'not_found'},false]] as const){if(Boolean(catalog(value))!==wanted)throw Error('Catalog view result');count++;}
console.log(count+' composition controls passed across ten existing result definitions; native effects and complete inner outcomes remain unqualified.');
export {};
