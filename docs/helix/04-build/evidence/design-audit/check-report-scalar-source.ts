/** Original UMF source archive/reload/export; not native installation authority. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {importPostgresqlSql,exportPostgresqlSql,getPostgresqlSource} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {getPostgresqlDdlDeclarations} from '/Users/erik/Projects/umf/src/adapters/postgresql/declarations';
import {writeDocument,readDocument} from '/Users/erik/Projects/umf/src/model/document';
const root='/Users/erik/Projects/umf';
const hash=(bytes:string|ArrayBuffer)=>new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
const paths=['native/postgresql/runtime.ts','src/adapters/postgresql/index.ts','src/adapters/postgresql/declarations.ts','src/model/document.ts','spec/extensions/postgresql/native-ast.schema.json','bun.lock'];
async function observe(){
 const git=(args:string[])=>{const result=Bun.spawnSync(['git','-C',root,...args]);if(result.exitCode)throw Error('Original owner observation failed');return new TextDecoder().decode(result.stdout).trim()};
 return {revision:git(['rev-parse','HEAD']),status:git(['status','--porcelain']),files:await Promise.all(paths.map(async path=>({path,sha256:hash(await Bun.file(root+'/'+path).arrayBuffer())})))};
}
const before=await observe();
if(before.revision!=='16c35e8d943769ccfa7bb57d16785aa7159abe65')throw Error('Original loaded owner revision required');
const currentOwnerRevision='1f7b5f5d2a355c4b476e3a96b289b9048f03f567';
for(const path of paths){
 const committed=Bun.spawnSync(['git','-C',root,'show',currentOwnerRevision+':'+path]);
 if(committed.exitCode||hash(new Uint8Array(committed.stdout).buffer)!==hash(await Bun.file(root+'/'+path).arrayBuffer()))throw Error('Changed current owner source subset: '+path);
}
if(process.argv.slice(2).some(value=>value!=='--tree'))throw Error('Closed source capture selection required');
const family=process.argv.includes('--tree')?'tree':'scalar';
const path=`docs/helix/02-design/contracts/report-${family}-bytes-v0.2.proposal.sql`,source=await Bun.file(path).text();
const model=await importPostgresqlSql(source,backend,{id:`truss-report-${family}-bytes-v0.2-proposal`});
const artifactPath=path.replace(/\.sql$/,'.umf.json'),serialized=writeDocument(model,'json');
await Bun.write(artifactPath,serialized);
const disk=readDocument(await Bun.file(artifactPath).text(),'json'),output=await exportPostgresqlSql(disk,backend);
if(getPostgresqlSource(model)!==source||getPostgresqlSource(disk)!==source||await exportPostgresqlSql(model,backend)!==output)throw Error('Original source/archive/export correspondence');
const declarations=getPostgresqlDdlDeclarations(disk),exportPath=`docs/helix/04-build/evidence/design-audit/report-${family}-bytes.owner-export.sql`;
await Bun.write(exportPath,output);
if(JSON.stringify(before)!==JSON.stringify(await observe())||await Bun.file(path).text()!==source)throw Error('Original owner/source changed');
const receipt={owner:before,currentOwnerRevision,currentListedSourceSubsetMatches:true,backend:backend.identity,path,sourceSha256:hash(source),artifactPath,artifactSha256:hash(serialized),exportPath,exportSha256:hash(output),sourceArchiveExact:true,reloadedExportExact:true,declarations,
 checkerSha256:hash(await Bun.file(import.meta.path).arrayBuffer()),scope:'Existing owner parser/native source archive, JSON reload and stable export only. Native scalar receipt remains separate; no complete required inventory, resource profile, routine grants or report installation qualification.'};
await Bun.write(`docs/helix/04-build/evidence/design-audit/report-${family}-source.json`,JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({sourceArchiveExact:true,reloadedExportExact:true,declarations:declarations.declarations.length,complete:declarations.complete}));
