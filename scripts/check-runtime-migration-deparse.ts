// SPDX-License-Identifier: MIT OR Apache-2.0
/** Qualify only exact native deparse alternatives observed in logical restores. */
const root=process.env.UMF_NATIVE_ROOT;
if(!root)throw Error('Set UMF_NATIVE_ROOT to the qualified UMF checkout');
const {backend}=await import(root+'/native/postgresql/runtime.ts');
const owner=await import(root+'/src/adapters/postgresql/index.ts');
const path=process.argv[process.argv.indexOf('--artifacts')+1];
if(!process.argv.includes('--artifacts')||!path)throw Error('--artifacts directory required');
const manifest=JSON.parse(await Bun.file(path+'/manifest.json').text());
const profiles=await Promise.all([...manifest.sources,manifest.target].map(async (id:string)=>JSON.parse(await Bun.file(path+'/'+id+'.json').text())));
const rules=profiles[0].definitionAlternatives;
if(rules.length!==2)throw Error('Exactly the two reviewed native deparse differences required');
for(const profile of profiles)if(JSON.stringify(profile.definitionAlternatives)!==JSON.stringify(rules))throw Error('Different source/target equivalence rules require review');
function normalized(value:any):any{
 if(Array.isArray(value))return value.map(normalized);
 if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().filter(k=>!['location','stmt_location','stmt_len'].includes(k)).map(k=>[k,normalized(value[k])]));
 return value;
}
const hash=(value:string)=>new Bun.CryptoHasher('sha256').update(value).digest('hex');
const proofs=[];
for(const [index,rule] of rules.entries()){
 const documents=[];const trees=[];
 for(const [version,definition] of rule.definitions.entries()){
  const sql=rule.surface==='constraints'?`CREATE TABLE truss.__migration_deparse_probe (CONSTRAINT __check ${definition})`:definition;
  const document=await owner.importPostgresqlSql(sql,backend,{id:`truss-migration-deparse-${index}-${version}`});
  if(document.umf!=='0.10.0')throw Error('UMF0.10 owner required');
  documents.push(document);
  // Native parser equality, not a handwritten Boolean rewrite or SQL text cleanup.
  trees.push(JSON.stringify(normalized(await backend.parse(await owner.exportPostgresqlSql(document,backend)))));
 }
 if(trees[0]!==trees[1])throw Error('Native parse trees differ beyond source positions: '+rule.identity.join('.'));
 proofs.push({surface:rule.surface,identity:rule.identity,canonicalTreeSha256:hash(trees[0]),documents});
}
const result={scope:'Two exact PG18.6 logical-restore deparse spellings; pinned UMF0.10 PostgreSQL import/export and raw AST equality excluding source positions only',backend:backend.identity,rules,proofs,passed:true};
const out=path+'/native-deparse-equivalence-0.1.json';await Bun.write(out,JSON.stringify(result)+'\n');
console.log(JSON.stringify({passed:true,rules:rules.map((r:any)=>r.identity),sha256:hash(JSON.stringify(result)+'\n')}));
