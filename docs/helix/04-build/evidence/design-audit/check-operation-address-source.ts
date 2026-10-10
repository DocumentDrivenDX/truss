/** Original address routine archive/export only; no protected authority or installer. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {importPostgresqlSql,exportPostgresqlSql,getPostgresqlSource} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {getPostgresqlDdlDeclarations} from '/Users/erik/Projects/umf/src/adapters/postgresql/declarations';
import {writeDocument,readDocument} from '/Users/erik/Projects/umf/src/model/document';
const root='/Users/erik/Projects/umf';
const paths=['native/postgresql/runtime.ts','src/adapters/postgresql/index.ts','src/adapters/postgresql/declarations.ts','src/model/document.ts','spec/extensions/postgresql/native-ast.schema.json','bun.lock'];
const hash=(v:string|ArrayBuffer)=>new Bun.CryptoHasher('sha256').update(v).digest('hex');
async function owner(){
 const r=Bun.spawnSync(['git','-C',root,'rev-parse','HEAD']);if(r.exitCode)throw Error('Owner unavailable');
 return {root,commit:new TextDecoder().decode(r.stdout).trim(),files:await Promise.all(paths.map(async path=>({path,sha256:hash(await Bun.file(root+'/'+path).arrayBuffer())})))};
}
const before=await owner();
const sourcePath='packages/postgresql/native/operation-address/encoder.sql';
const artifactPath='docs/helix/02-design/contracts/operation-address-v0.1.proposal.umf.json';
const exportPath='docs/helix/04-build/evidence/design-audit/operation-address-source.owner-export.sql';
const receiptPath='docs/helix/04-build/evidence/design-audit/operation-address-source.json';
for(const p of [artifactPath,exportPath,receiptPath])if(await Bun.file(p).exists())throw Error('Original output already exists');
const source=await Bun.file(sourcePath).text();
const model=await importPostgresqlSql(source,backend,{id:'truss-operation-address-proposal'});
const serialized=writeDocument(model,'json'),reloaded=readDocument(serialized,'json');
const output=await exportPostgresqlSql(model,backend);
if(getPostgresqlSource(model)!==source||getPostgresqlSource(reloaded)!==source||await exportPostgresqlSql(reloaded,backend)!==output)throw Error('Original archive/reload/export mismatch');
const declarations=getPostgresqlDdlDeclarations(model);
if(declarations.complete!==false)throw Error('Partial declaration support overclaimed');
if(JSON.stringify(before)!==JSON.stringify(await owner())||await Bun.file(sourcePath).text()!==source)throw Error('Original source drift');
await Bun.write(artifactPath,serialized);await Bun.write(exportPath,output);
const receipt={scope:'Original UMF PostgreSQL extension archive/reload/export; not core structural declaration coverage, address authority semantics or installation',ownerSource:before,backend:backend.identity,sourcePath,sourceSha256:hash(source),artifactPath,artifactSha256:hash(serialized),exportPath,exportSha256:hash(output),producerSha256:hash(await Bun.file(import.meta.path).arrayBuffer()),sourceArchiveExact:true,reloadedExportExact:true,complete:false,declarations:declarations.declarations.length,unhandled:declarations.unhandled.map(v=>({path:v.path})),diagnostics:declarations.diagnostics,installerReady:false};
await Bun.write(receiptPath,JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({sourceArchiveExact:true,reloadedExportExact:true,complete:false,declarations:receipt.declarations,unhandled:receipt.unhandled.length}));
