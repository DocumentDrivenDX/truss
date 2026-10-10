/** Existing group overload composition only; no receipt or native durability evidence. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
const root='docs/helix/02-design/contracts/';
for(const file of new Bun.Glob('*.schema.json').scanSync(root))ajv.addSchema(await Bun.file(root+file).json());
const id='urn:truss:proposal:group-capability-wires:0.1.0';
const pin={identity:'fixture',version:'0.1',sha256:'a'.repeat(64)},artifact={identity:'fixture',bytesBase64:'',sha256:pin.sha256};
const identity={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'d',moduleId:'m'}};
const semantic={interfaceVersion:'truss-group-result/0.1.0',executedCatalogRevision:'1',layoutProfile:pin,mutationProfile:pin,results:[{operation:'update_object',outcome:'unchanged',identity,version:'1',events:[]}],aliases:[]};
const applied={semantic,disposition:'applied',durability:'pending'};
const replayed={semantic,disposition:'replayed',durability:'committed',replay:{basis:'committed_receipt',observationProfile:pin,evidence:artifact}};
let count=0;
for(const [name,bearing] of [['requestFree',false],['requestBearing',true]] as const){
 const validate=ajv.getSchema(id+'#/$defs/'+name+'Result');if(!validate)throw Error(name);
 const cases:[string,unknown,boolean][]=[
  ['pending application',{outcome:'success',response:applied},true],
  ['supplied scope cannot claim applied commit',{outcome:'success',response:{...applied,durability:'committed'}},false],
  ['receipt replay distinction',{outcome:'success',response:replayed},bearing],
  ['request conflict distinction',{outcome:'failed',failure:{code:'request_conflict',diagnosticProfile:pin,diagnostic:artifact}},bearing],
  ['receipt expiry distinction',{outcome:'unavailable',reason:'receipt_expired'},bearing],
  ['receipt absence distinction',{outcome:'unavailable',reason:'receipt'},bearing],
  ['ordinary invalid',{outcome:'failed',failure:{code:'invalid',diagnosticProfile:pin,diagnostic:artifact}},true],
  ['inner operation failure',{outcome:'failed',failure:{code:'group_failed',operationIndex:'0',errorProfile:pin,innerError:artifact}},true],
  ['failure cannot include response',{outcome:'failed',failure:{code:'invalid',diagnosticProfile:pin,diagnostic:artifact},response:applied},false],
  ['missing successful response',{outcome:'success'},false]
 ];
 for(const [label,value,wanted] of cases){if(Boolean(validate(value))!==wanted)throw Error(name+' '+label+': '+JSON.stringify(validate.errors));count++;}
 const outer=ajv.getSchema(id+'#/$defs/'+name+'Outcome');if(!outer)throw Error(name);
 if(!outer({status:'ok',value:{outcome:'success',response:applied}})||outer({outcome:'success',response:applied}))throw Error(name+' outer layering');count+=2;
}
console.log(count+' group overload composition controls passed. Receipt authority, semantic order and native commit/replay evidence remain unqualified.');
export {};
