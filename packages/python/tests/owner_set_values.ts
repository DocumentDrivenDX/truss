// Test-only original UMF literal evaluator; never a runtime JS sidecar.
const root=process.env.UMF_OWNER_ROOT??'/Users/erik/.codex/worktrees/0ede/umf';
const owner=await import(root+'/src/model/schema-literals.ts');
const cases=JSON.parse(await Bun.stdin.text());
console.log(JSON.stringify(cases.map((c:any)=>{try{owner.checkSchemaLiteral({modules:[]},c.field,c.literal);return true;}catch{return false;}})));
