/** Row-home candidate source capture only; no installed storage or scalar domain/token parity qualification. */
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
const path='docs/helix/02-design/contracts/row-home-capacity-v0.1.proposal.sql';
const source=await Bun.file(path).text();
const model=await importPostgresqlSql(source,backend,{id:'truss-row-home-capacity-proposal'});
const serialized=writeDocument(model,'json'),reloaded=readDocument(serialized,'json');
const output=await exportPostgresqlSql(model,backend);
if(getPostgresqlSource(model)!==source||getPostgresqlSource(reloaded)!==source||await exportPostgresqlSql(reloaded,backend)!==output)throw Error('source/reload/export correspondence failed');
const declarations=getPostgresqlDdlDeclarations(model);
if(declarations.complete!==false)throw Error('partial declaration extractor overclaimed completeness');
const artifactPath='docs/helix/02-design/contracts/row-home-capacity-v0.1.proposal.umf.json';
await Bun.write(artifactPath,serialized);
const disk=readDocument(await Bun.file(artifactPath).text(),'json');
if(getPostgresqlSource(disk)!==source||await exportPostgresqlSql(disk,backend)!==output)throw Error('saved artifact correspondence failed');
const after=await ownerObservation();
if(JSON.stringify(before)!==JSON.stringify(after)||await Bun.file(path).text()!==source)throw Error('source changed during run');
await Bun.write('docs/helix/04-build/evidence/design-audit/row-home-capacity-source.owner-export.sql',output);
const receipt={scope:'Existing UMF parser/source archive/reload/export and partial declaration observation only; no native capacity/reservation/retained-parity/lock/privilege or complete installer qualification',ownerSource:before,backend:backend.identity,path,sourceSha256:hash(source),artifactPath,artifactSha256:hash(serialized),exportSha256:hash(output),sourceArchiveExact:true,reloadedExportExact:true,complete:false,declarations:declarations.declarations.map(d=>({kind:d.kind,path:d.path,requiresCatalogExpansion:d.requiresCatalogExpansion,columns:d.columns.map(c=>({path:c.path,name:c.element.name,typeResolution:c.typeResolution,...(c.element.scalarType?{syntacticScalarFamily:c.element.scalarType}:{})}))})),unhandled:declarations.unhandled.map(u=>({path:u.path})),diagnostics:declarations.diagnostics};
await Bun.write('docs/helix/04-build/evidence/design-audit/row-home-capacity-source.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({sourceArchiveExact:true,reloadedExportExact:true,declarations:receipt.declarations.length,unhandled:receipt.unhandled.length,complete:false}));
