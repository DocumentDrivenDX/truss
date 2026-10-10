/** Shape witnesses only; never authorization/snapshot/native cursor evidence. */
const {default: Ajv} = await import(process.argv[2]);
const schema = await Bun.file('docs/helix/02-design/contracts/direct-cursor-v0.1.schema.json').json();
const validate = new Ajv({strict: true}).compile(schema);
const pin = {identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const owner = {documentId:'document',moduleId:'module'};
const context = {catalogRevision:'1',layoutProfile:pin,readProfile:pin,authorizedScopeIdentity:'scope',consistency:{kind:'live'}};
const object = {interfaceVersion:'truss-direct-cursor/0.1.0',context,selection:{operation:'objects',type:{typeId:'1',definitionPin:'definition',owner}},after:{id:'10'}};
const edge = {interfaceVersion:object.interfaceVersion,context,selection:{operation:'edges',object:{id:'1',typeId:'1',definitionPin:'definition',owner},direction:'both',relationships:[]},after:{id:'10',orderKey:{state:'null'}}};
const cases: [string,unknown,boolean][] = [
  ['object',object,true],['edge null',edge,true],
  ['edge empty text',{...edge,after:{id:'10',orderKey:{state:'text',text:''}}},true],
  ['held snapshot',{...object,context:{...context,consistency:{kind:'held_snapshot',snapshotIdentity:'snapshot'}}},true],
  ['wrong version',{...object,interfaceVersion:'other'},false],
  ['unknown member',{...object,authority:true},false],
  ['missing position',{...object,after:{}},false],
  ['missing edge order',{...edge,after:{id:'10'}},false],
  ['null plus text',{...edge,after:{id:'10',orderKey:{state:'null',text:''}}},false],
  ['snapshot missing handle',{...object,context:{...context,consistency:{kind:'held_snapshot'}}},false],
  ['fake scope remains semantic',{...object,context:{...context,authorizedScopeIdentity:'forged'}},true],
  ['unsupported identity remains semantic',{...object,after:{id:'not-native-id'}},true]
];
const failures = cases.filter(([,value,expected]) => Boolean(validate(value)) !== expected).map(([name])=>name);
const requestSchema = await Bun.file('docs/helix/02-design/contracts/direct-page-request-v0.1.schema.json').json();
const requestValidator = new Ajv({strict:true}).addSchema(schema).compile(requestSchema);
const request = {interfaceVersion:'truss-direct-page-request/0.1.0',context,selection:object.selection,limit:'50',continuation:{state:'first'}};
const requestCases: [string,unknown,boolean][] = [
  ['first request',request,true],
  ['after request',{...request,continuation:{state:'after',cursor:object}},true],
  ['limit host number',{...request,limit:50},false],
  ['limit zero',{...request,limit:'0'},false],
  ['limit alias',{...request,limit:'050'},false],
  ['missing limit',Object.fromEntries(Object.entries(request).filter(([key])=>key!=='limit')),false],
  ['first with cursor',{...request,continuation:{state:'first',cursor:object}},false],
  ['mismatched cursor selection remains semantic',{...request,continuation:{state:'after',cursor:edge}},true],
  ['deployment maximum remains semantic',{...request,limit:'999999999999999999999'},true]
];
failures.push(...requestCases.filter(([,value,expected])=>Boolean(requestValidator(value))!==expected).map(([name])=>name));
console.log(JSON.stringify({scope:'closed cursor and request shapes only',cursorCases:cases.length,requestCases:requestCases.length,failures},null,2));
if(failures.length)process.exit(1);
export {};
