/** Existing owner API composition across two candidate source captures, not installation. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {getPostgresqlNode,proposePostgresqlNodeEdit,exportPostgresqlSql,importPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const hash=(x:string|ArrayBuffer)=>new Bun.CryptoHasher('sha256').update(x).digest('hex');
const ownerRoot='/Users/erik/Projects/umf';
async function owner(){
 const git=(args:string[])=>{const r=Bun.spawnSync(['git','-C',ownerRoot,...args]);if(r.exitCode)throw Error('owner observation failed');return new TextDecoder().decode(r.stdout).trim();};
 const paths=['native/postgresql/runtime.ts','src/adapters/postgresql/index.ts','src/model/document.ts','src/model/native-json.ts','bun.lock'];
 return {root:ownerRoot,commit:git(['rev-parse','HEAD']),status:git(['status','--porcelain']),files:await Promise.all(paths.map(async path=>({path,sha256:hash(await Bun.file(ownerRoot+'/'+path).arrayBuffer())})))};
}
const includeUnfinishedUnique=process.argv.includes('--include-unfinished-unique');
const includeEdgeLimits=includeUnfinishedUnique||process.argv.includes('--include-edge-limits');
const includeGuards=includeEdgeLimits||process.argv.includes('--include-guards');
const includeInitialization=includeGuards||process.argv.includes('--include-initialization');
const includeCapacity=includeInitialization||process.argv.includes('--include-capacity');
const receiptStem=includeUnfinishedUnique?'row-home-unfinished-unique-guard-statement-composition':includeEdgeLimits?'row-home-edge-limit-guard-statement-composition':includeGuards?'row-home-native-guard-statement-composition':includeInitialization?'row-home-initialized-statement-composition':includeCapacity?'row-home-protected-statement-composition':'row-home-guard-statement-composition';
const before=await owner();const inputs:any[]=[];const statements:any[]=[];const fullExports:string[]=[];
for(const stem of ['row-home-tree','row-home-scalar','row-home-touch',...(includeCapacity?['row-home-capacity']:[]),...(includeGuards?['row-home-operation']:[]),...(includeUnfinishedUnique?['row-operation-unfinished-unique']:[]),...(includeGuards?['row-home-triggers']:[]),...(includeEdgeLimits?['edge-limit-triggers']:[]),...(includeInitialization?['row-home-capacity-initialization']:[])]){
 const modelPath='docs/helix/02-design/contracts/'+stem+'-v0.1.proposal.umf.json';
 const sourcePath='docs/helix/02-design/contracts/'+stem+'-v0.1.proposal.sql';
 const original=await Bun.file(modelPath).text(),source=await Bun.file(sourcePath).text();
 inputs.push({modelPath,modelSha256:hash(original),sourcePath,sourceSha256:hash(source)});
 const d=readDocument(original,'json');const s=getPostgresqlNode(d,'/stmts');if(s.kind!=='array')throw Error('statement array missing');
 fullExports.push(await exportPostgresqlSql(d,backend));
 for(const [index,node] of s.items.entries()){
  const one=proposePostgresqlNodeEdit(d,'/stmts','['+renderTree(node)+']').document;
  const sql=await exportPostgresqlSql(one,backend);
  statements.push({ordinal:String(statements.length),modelPath,sourceStatementIndex:String(index),sourcePath:'/stmts/'+index,executionKind:stem==='row-home-capacity-initialization'?'parameterized-initialization':(stem==='row-home-triggers'||stem==='edge-limit-triggers')?'guard-declaration':'ddl',parameterPositions:stem==='row-home-capacity-initialization'?['1','2']:[],sql,sha256:hash(sql)});
 }
}
const joins=['',...statements.slice(1).map(()=>';\n'),';'];
const joined=statements.map(x=>x.sql).join(';\n')+';';
const reloaded=await importPostgresqlSql(joined,backend,{id:'truss-row-home-guard-statement-composition-proposal'});
const output=await exportPostgresqlSql(reloaded,backend);
const expected=fullExports.join('; ');
if(output!==expected)throw Error('original three-capture exporter composition mismatch');
for(const input of inputs){if(hash(await Bun.file(input.modelPath).text())!==input.modelSha256||hash(await Bun.file(input.sourcePath).text())!==input.sourceSha256)throw Error('input changed');}
if(JSON.stringify(before)!==JSON.stringify(await owner()))throw Error('owner changed');
await Bun.write('docs/helix/04-build/evidence/design-audit/'+receiptStem+'.proposal.sql',joined);
await Bun.write('docs/helix/04-build/evidence/design-audit/'+receiptStem+'.json',JSON.stringify({scope:'Original existing-UMF guarded per-statement export and ordered selected-capture composition/re-import only; no baseline conversion, native installation, implicit-effect completeness or accepted Weft binding',owner:before,backend:backend.identity,bunVersion:Bun.version,inputs,statements,joins,joinedSqlSha256:hash(joined),joinedOwnerReexportExact:true,physicalCoverageComplete:false,nativeExecution:false,installable:false,blockedDependencies:includeGuards?['native routine bodies and complete original dependency/type/security/role/grant/registry/codec profiles']:[]},null,2)+'\n');
console.log(JSON.stringify({statements:statements.length,joinedOwnerReexportExact:true,physicalCoverageComplete:false,nativeExecution:false}));
