/** Catalog lexical wire shape only; native bounds/provenance/profile admission separate. */
const {default:Ajv}=await import(process.argv[2]);
const ajv=new Ajv({strict:true});
for(const file of new Bun.Glob('*.schema.json').scanSync('docs/helix/02-design/contracts'))ajv.addSchema(await Bun.file('docs/helix/02-design/contracts/'+file).json());
const inventory=await Bun.file('docs/helix/04-build/evidence/design-audit/signed-catalog-wire-inventory.json').json();
const inputs:[string|number,boolean][]=[['0',true],['1',true],['-1',true],['-0',false],['+1',false],['01',false],['-01',false],[-1,false],['2147483648',true]];
const failures:any[]=[],results:any[]=[];
for(const item of inventory.changes){
 const schema=await Bun.file(item.file).json();
 for(const path of item.catalogFields){
  const validate=ajv.getSchema(schema.$id+'#'+path);
  if(!validate)throw Error('missing exact field validator '+path);
  for(const [input,expected] of inputs){const actual=validate(input);const row={file:item.file,path,input,expected,actual};results.push(row);if(actual!==expected)failures.push(row);}
 }
}
const receipt={scope:'Named changed catalog fields across the exact authored draft inventory: lexical text shape only. Out-of-native-range canonical text remains shape-valid and requires semantic refusal; no native capability inferred.',cases:results.length,failures,results};
await Bun.write('docs/helix/04-build/evidence/design-audit/signed-catalog-wire-check.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({scope:receipt.scope,cases:receipt.cases,failures}));if(failures.length)process.exit(1);export {};
