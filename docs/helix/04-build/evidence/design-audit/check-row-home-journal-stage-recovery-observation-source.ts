/** Existing UMF source capture only; no PostgreSQL execution or inventory proof. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {importPostgresqlSql,exportPostgresqlSql,getPostgresqlSource} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {getPostgresqlDdlDeclarations} from '/Users/erik/Projects/umf/src/adapters/postgresql/declarations';
import {writeDocument,readDocument} from '/Users/erik/Projects/umf/src/model/document';
const ownerRoot='/Users/erik/Projects/umf';
const ownerPaths=['native/postgresql/runtime.ts','src/adapters/postgresql/index.ts','src/adapters/postgresql/declarations.ts','src/model/document.ts','spec/extensions/postgresql/native-ast.schema.json','bun.lock'];
const hash=(value:string|ArrayBuffer)=>new Bun.CryptoHasher('sha256').update(value).digest('hex');
async function ownerObservation(){
  const git=(args:string[])=>{const r=Bun.spawnSync(['git','-C',ownerRoot,...args]);if(r.exitCode)throw Error('owner observation failed');return new TextDecoder().decode(r.stdout).trim();};
  return {root:ownerRoot,commit:git(['rev-parse','HEAD']),status:git(['status','--porcelain']),files:await Promise.all(ownerPaths.map(async path=>({path,sha256:hash(await Bun.file(ownerRoot+'/'+path).arrayBuffer())})))};
}
const before=await ownerObservation();
const observations=[];
for(const kind of ['row-home-journal-stage-recovery-observation']){
  const path=`docs/helix/02-design/contracts/${kind}-v0.2.proposal.sql`;
  const source=await Bun.file(path).text();
  const model=await importPostgresqlSql(source,backend,{id:`truss-${kind}-proposal`});
  const serialized=writeDocument(model,'json');
  const output=await exportPostgresqlSql(model,backend);
  const artifactPath=path.replace(/\.sql$/,'.umf.json');
  await Bun.write(artifactPath,serialized);
  const disk=readDocument(await Bun.file(artifactPath).text(),'json');
  if(getPostgresqlSource(model)!==source||getPostgresqlSource(disk)!==source||await exportPostgresqlSql(disk,backend)!==output)throw Error('source/reload/export mismatch');
  const declarations=getPostgresqlDdlDeclarations(model);
  const exportPath=`docs/helix/04-build/evidence/design-audit/${kind}.owner-export.sql`;
  await Bun.write(exportPath,output);
  observations.push({path,sourceSha256:hash(source),artifactPath,artifactSha256:hash(serialized),exportPath,exportSha256:hash(output),sourceArchiveExact:true,reloadedExportExact:true,complete:declarations.complete,declarationCount:declarations.declarations.length,unhandled:declarations.unhandled.map(u=>({path:u.path})),diagnostics:declarations.diagnostics});
  if(await Bun.file(path).text()!==source)throw Error('source changed during capture');
}
const after=await ownerObservation();
if(JSON.stringify(before)!==JSON.stringify(after))throw Error('owner source changed during capture');
for(const observation of observations){
  if(hash(await Bun.file(observation.path).text())!==observation.sourceSha256)throw Error('original query changed before final receipt');
}
await Bun.write('docs/helix/04-build/evidence/design-audit/row-home-journal-stage-recovery-observation-source.json',JSON.stringify({scope:'UMF parser/source archive/JSON reload/guarded export only; no PostgreSQL execution, complete native inventory/semantics, privileges, dependencies or installed parity',bunVersion:Bun.version,ownerSource:before,backend:backend.identity,observations},null,2)+'\n');
console.log(JSON.stringify({families:observations.length,declarations:observations[0].declarationCount,unhandled:observations[0].unhandled.length,sourceArchiveExact:true,reloadedExportExact:true,complete:observations[0].complete}));
