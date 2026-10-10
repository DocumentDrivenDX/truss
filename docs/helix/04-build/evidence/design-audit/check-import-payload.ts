/** Deferred payload shape only; no import/source/native behavior proof. */
const {default:Ajv}=await import(process.argv[2]);
const ajv=new Ajv({strict:true});
for(const name of ['exact-value','history-record'])ajv.addSchema(await Bun.file(`docs/helix/02-design/contracts/${name}-v0.1.schema.json`).json());
const validate=ajv.compile(await Bun.file('docs/helix/02-design/contracts/import-payload-v0.1.schema.json').json());
const object={interfaceVersion:'truss-import-payload/0.1.0',kind:'object',values:[],ownership:{state:'rootless'}};
const edge={interfaceVersion:object.interfaceVersion,kind:'edge',values:[],source:{kind:'map',entries:[]},orderKey:{state:'null'}};
const entry={name:'value',value:{kind:'string',text:'exact'}};
const cases:[string,unknown,boolean][]=[
 ['missing source default',object,true],['explicit empty source',{...object,source:{kind:'map',entries:[]}},true],
 ['edge null order',edge,true],['edge empty text',{...edge,orderKey:{state:'text',text:''}},true],
 ['ownership alias',{...object,ownership:{state:'owned',root:{state:'alias',alias:'other'}}},false],
 ['source native object',{...object,source:{}},false],
 ['edge no order',Object.fromEntries(Object.entries(edge).filter(([key])=>key!=='orderKey')),false],
 ['unknown member',{...object,execute:'SQL'},false],
 ['duplicate names need semantic refusal',{...object,values:[entry,entry]},true],
 ['known source wrong type needs semantic refusal',{...object,source:{kind:'map',entries:[{key:'author',value:{kind:'integer',text:'1'}}]}},true],
 ['identity agreement remains semantic',{...object,values:[entry]},true]
];
const failures=cases.filter(([,value,expected])=>Boolean(validate(value))!==expected).map(([name])=>name);
console.log(JSON.stringify({scope:'decoded payload shape only',cases:cases.length,failures},null,2));
if(failures.length)process.exit(1);
export {};
