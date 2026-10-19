// SPDX-License-Identifier: MIT OR Apache-2.0
// Test-only original UMF literal evaluator; never a runtime JS sidecar.
const root=process.env.UMF_OWNER_ROOT;
if(!root)throw new Error('UMF_OWNER_ROOT must select the current UMF source checkout');
const owner=await import(root+'/src/model/schema-literals.ts');
const cases=JSON.parse(await Bun.stdin.text());
console.log(JSON.stringify(cases.map((c:any)=>{try{owner.checkSchemaLiteral({modules:[]},c.field,c.literal);return true;}catch{return false;}})));
