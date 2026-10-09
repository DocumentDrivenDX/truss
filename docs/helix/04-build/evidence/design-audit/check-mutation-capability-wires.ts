/** Existing standalone restrictions; no installed mutation or native validation evidence. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
const root='docs/helix/02-design/contracts/';
for(const file of new Bun.Glob('*.schema.json').scanSync(root))ajv.addSchema(await Bun.file(root+file).json());
const id='urn:truss:proposal:mutation-capability-wires:0.1.0';
const pin={identity:'fixture',version:'0.1',sha256:'a'.repeat(64)};
const identity={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'d',moduleId:'m'}};
const stored={state:'stored',identity},alias={state:'alias',alias:'x'};
const input={interfaceVersion:'truss-mutation-input/0.1.0',layoutProfile:pin,mutationProfile:pin,valueProfile:pin,catalog:{selection:'current'},assertedOrigin:{kind:'string',text:'fixture'},operation:{operation:'update_object',target:stored,set:[],unset:[]}};
const result={outcome:'success',result:{operation:'update_object',outcome:'unchanged',identity,version:'1',events:[]},executedCatalogRevision:'1',layoutProfile:pin,mutationProfile:pin,durability:'pending'};
const cases:[string,string,unknown,boolean][]=[
 ['existing standalone input','input',input,true],
 ['no operations array','input',{...input,operations:[]},false],
 ['no group input version','input',{...input,interfaceVersion:'truss-group-input/0.1.0'},false],
 ['stored target required','input',{...input,operation:{...input.operation,target:alias}},false],
 ['stored root required','input',{...input,operation:{...input.operation,ownershipChange:{state:'owned',root:alias}}},false],
 ['rootless change','input',{...input,operation:{...input.operation,ownershipChange:{state:'rootless'}}},true],
 ['create object no alias','operation',{operation:'create_object',typeDefinitionPin:'fixture',values:[],ownership:{state:'rootless'},alias:'x'},false],
 ['create object','operation',{operation:'create_object',typeDefinitionPin:'fixture',values:[],ownership:{state:'rootless'}},true],
 ['create edge stored endpoints','operation',{operation:'create_edge',relationshipDefinitionPin:'fixture',source:stored,target:stored,values:[],orderKey:{state:'null'}},true],
 ['create edge alias endpoint','operation',{operation:'create_edge',relationshipDefinitionPin:'fixture',source:alias,target:stored,values:[],orderKey:{state:'null'}},false],
 ['update edge stored change','operation',{operation:'update_edge',target:stored,set:[],unset:[],endpointChange:{source:stored,target:stored}},true],
 ['update edge alias change','operation',{operation:'update_edge',target:stored,set:[],unset:[],endpointChange:{source:stored,target:alias}},false],
 ['delete stored object','operation',{operation:'delete_object',target:stored},true],
 ['delete stored edge','operation',{operation:'delete_edge',target:stored},true],
 ['delete alias refuses','operation',{operation:'delete_edge',target:alias},false],
 ['pending result','result',result,true],
 ['standalone result no alias','result',{...result,result:{...result.result,alias:'x'}},false],
 ['pending not committed','result',{...result,durability:'committed'},false],
 ['nested result','outcome',{status:'ok',value:result},true]
];
for(const [name,member,value,wanted] of cases){const validate=ajv.getSchema(id+'#/$defs/'+member);if(!validate||Boolean(validate(value))!==wanted)throw Error(name+': '+JSON.stringify(validate?.errors));}
console.log(cases.length+' standalone mutation composition controls passed; exact native reference/ownership/value/current-authority admission remains unqualified.');
export {};
