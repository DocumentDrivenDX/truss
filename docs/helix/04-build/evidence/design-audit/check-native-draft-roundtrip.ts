/** UMF owner source round-trip, not installed SQL/native behavior qualification. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {importPostgresqlSql,exportPostgresqlSql,getPostgresqlSource} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {getPostgresqlDdlDeclarations} from '/Users/erik/Projects/umf/src/adapters/postgresql/declarations';
import {writeDocument,readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const names=['key-bucket-layout','key-bucket-observation','migration-admission-layout','migration-admission-statements','migration-receipt-layout','migration-receipt-statements','write-head-admission','key-bucket-integrity-metadata','key-bucket-integrity-chunk','key-bucket-integrity-locator','relationship-lineage-layout','migration-head-admission','catalog-admission-prelude','catalog-id-high-water'];
const drafts=names.map(name=>({name,path:'docs/helix/02-design/contracts/'+name+'-v0.1.draft.sql'}));
drafts.push({name:'direct-page-observation',path:'docs/helix/02-design/contracts/direct-page-observation-v0.1.proposal.sql'});
drafts.push({name:'direct-lookup-observation',path:'docs/helix/02-design/contracts/direct-lookup-observation-v0.1.proposal.sql'});
drafts.push({name:'catalog-definition-source',path:'docs/helix/02-design/contracts/catalog-definition-source-v0.1.proposal.sql'});
const ownerRoot='/Users/erik/Projects/umf';
function ownerGit(args:string[]){
 const result=Bun.spawnSync(['git','-C',ownerRoot,...args]);
 if(result.exitCode!==0)throw Error('owner provenance observation unavailable');
 return new TextDecoder().decode(result.stdout).trim();
}
const ownerCommit=ownerGit(['rev-parse','HEAD']),ownerStatus=ownerGit(['status','--porcelain']);
const pinnedOwnerFiles=['native/postgresql/runtime.ts','src/adapters/postgresql/index.ts','src/adapters/postgresql/declarations.ts','src/model/document.ts','spec/extensions/postgresql/native-ast.schema.json','bun.lock'];
async function ownerHashes(){return Promise.all(pinnedOwnerFiles.map(async path=>({path,sha256:new Bun.CryptoHasher('sha256').update(await Bun.file(ownerRoot+'/'+path).arrayBuffer()).digest('hex')})));}
const ownerFilesBefore=await ownerHashes();
const results:any[]=[],failures:{path:string;error:string}[]=[];
for(const {name,path} of drafts){
 const source=await Bun.file(path).text();
 try{
  const document=await importPostgresqlSql(source,backend,{id:'truss-'+name+'-draft'}),output=await exportPostgresqlSql(document,backend);
  const serialized=writeDocument(document,'json'),reloaded=readDocument(serialized,'json');
  if(getPostgresqlSource(document)!==source||getPostgresqlSource(reloaded)!==source)throw Error('original source archive changed');
  if(await exportPostgresqlSql(reloaded,backend)!==output)throw Error('reloaded export differs');
  let savedUmfArtifact:undefined|{path:string;sha256:string;sourceArchiveExact:true;exportExact:true};
  if(name==='catalog-definition-source'){
   const artifactPath='docs/helix/02-design/contracts/catalog-definition-source-v0.1.proposal.umf.json';
   await Bun.write(artifactPath,serialized);
   const saved=await Bun.file(artifactPath).text(),diskDocument=readDocument(saved,'json');
   if(saved!==serialized||getPostgresqlSource(diskDocument)!==source||await exportPostgresqlSql(diskDocument,backend)!==output)throw Error('saved UMF artifact correspondence failed');
   savedUmfArtifact={path:artifactPath,sha256:new Bun.CryptoHasher('sha256').update(saved).digest('hex'),sourceArchiveExact:true,exportExact:true};
  }
  const declarations=getPostgresqlDdlDeclarations(document);
  if(declarations.complete!==false)throw Error('partial declarations overclaim completeness');
  // Owner observations only: ALTER column observations include type changes, not just additions.
  // Preserve unresolved families; this is neither a catalog replay nor a Truss type resolver.
  const declarationInventory=name==='catalog-definition-source'?declarations.declarations.map(d=>({
   path:d.path,statementIndex:d.statementIndex,kind:d.kind,requiresCatalogExpansion:d.requiresCatalogExpansion,
   relation:JSON.parse(renderTree(d.relation)),
   commands:JSON.parse(renderTree(d.nativeStatement)).cmds.map((entry:any,index:number)=>({path:d.path+'/cmds/'+index+'/AlterTableCmd',subtype:entry.AlterTableCmd.subtype})),
   columns:d.columns.map(c=>({path:c.path,name:c.element.name,typeResolution:c.typeResolution,...(c.element.scalarType?{syntacticScalarFamily:c.element.scalarType}:{})}))
  })):undefined;
  await Bun.write('docs/helix/04-build/evidence/design-audit/'+name+'.owner-export.sql',output);
  results.push({path,...(savedUmfArtifact?{savedUmfArtifact}:{}),...(declarationInventory?{declarationInventory}:{}),sourceSha256:new Bun.CryptoHasher('sha256').update(source).digest('hex'),exportSha256:new Bun.CryptoHasher('sha256').update(output).digest('hex'),sourceArchiveExact:true,jsonReload:true,reloadedExportExact:true,declarationStatus:declarations.status,complete:false,declarations:declarations.declarations.length,unhandled:declarations.unhandled.length,diagnostics:declarations.diagnostics.map(d=>({code:d.code,path:d.path,severity:d.severity}))});
 }catch(error){failures.push({path,error:String(error)});}
}
const ownerFilesAfter=await ownerHashes();
if(ownerGit(['rev-parse','HEAD'])!==ownerCommit||ownerGit(['status','--porcelain'])!==ownerStatus||JSON.stringify(ownerFilesBefore)!==JSON.stringify(ownerFilesAfter))failures.push({path:ownerRoot,error:'owner source changed during evidence run'});
const ownerSource={root:ownerRoot,commit:ownerCommit,workingTreeClean:ownerStatus==='',workingTreeStatus:ownerStatus,observedFiles:ownerFilesBefore,stableThroughRun:JSON.stringify(ownerFilesBefore)===JSON.stringify(ownerFilesAfter),scope:'selected source entrypoints/schema/lock hashes and git observations; not full dependency/build attestation or native qualification'};
const receipt={ownerSource,scope:'Seventeen native candidate drafts: existing pinned UMF parser/codec/AST reparse/source archive/JSON reload only; no PLpgSQL body compilation, native database/catalog/privilege or complete exporter correspondence',backend:backend.identity,results,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/native-draft-roundtrip.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({results:results.map(r=>({path:r.path,declarations:r.declarations,unhandled:r.unhandled})),failures}));if(failures.length)process.exit(1);
