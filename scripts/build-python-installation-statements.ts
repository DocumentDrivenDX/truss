/** Original owner-emitted statement units for provisional installer construction. */
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {getPostgresqlNode,proposePostgresqlNodeEdit,exportPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
const modelPath='docs/helix/02-design/models/truss-layout-source-epoch-0.16.proposal.umf.json';
const exportPath='docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql';
const hash=(value:string|Uint8Array)=>new Bun.CryptoHasher('sha256').update(value).digest('hex');
const model=await Bun.file(modelPath).text(),document=readDocument(model,'json');
const originalExport=await Bun.file(exportPath).text();
const sourceManifestPath='packages/python/src/truss/_installation/manifest.json';
const sourceManifest=await Bun.file(sourceManifestPath).text(),sourceDefinition=JSON.parse(sourceManifest);
if(sourceDefinition.qualified!==false||sourceDefinition.executable!==false
 ||sourceDefinition.resources.find((r:any)=>r.role==='model')?.sha256!==hash(model)
 ||sourceDefinition.resources.find((r:any)=>r.role==='owner_export')?.sha256!==hash(originalExport))
 throw Error('Original development source definition correspondence required');
if(await exportPostgresqlSql(document,backend)!==originalExport)throw Error('Original complete owner export correspondence required');
const nodes=JSON.parse(renderTree(getPostgresqlNode(document,'/stmts')));
const statements=[];
for(const [position,node] of nodes.entries()){
 const one=proposePostgresqlNodeEdit(document,'/stmts',JSON.stringify([node])).document;
 const sql=await exportPostgresqlSql(one,backend);
 statements.push({position:String(position),sql,byteLength:Buffer.byteLength(sql),sha256:hash(sql)});
}
if(statements.map(s=>s.sql).join('; ')!==originalExport)throw Error('Ordered owner statement projection must reproduce the complete export');
const revision=Bun.spawnSync(['git','rev-parse','HEAD'],{cwd:'/Users/erik/Projects/umf'});
if(revision.exitCode!==0)throw Error('Committed owner revision required');
const sources:Record<string,string>={};
for(const path of [modelPath,exportPath,sourceManifestPath,'scripts/build-python-installation-statements.ts',
 '/Users/erik/Projects/umf/src/adapters/postgresql/index.ts','/Users/erik/Projects/umf/src/model/native-json.ts',
 '/Users/erik/Projects/umf/native/postgresql/runtime.ts'])sources[path]=hash(new Uint8Array(await Bun.file(path).arrayBuffer()));
const asset=JSON.stringify({interfaceVersion:'truss-provisional-installation-statements/0.1.0',
 scope:'original_owner_statement_units_rollback_only_construction',ownerRevision:Buffer.from(revision.stdout).toString().trim(),
 modelSha256:hash(model),ownerExportSha256:hash(originalExport),sources,statements,
 completeInstalledProfile:false,installationReady:false},null,2)+'\n';
const path='packages/python/src/truss/_installation/statements.json';
await Bun.write(path,asset);
await Bun.write('packages/python/src/truss/_installation_statement_release.py',
 '"""Generated original construction statement pins; no installation authority."""\nSTATEMENTS_SHA256 = '+JSON.stringify(hash(asset))+'\nSOURCE_MANIFEST_SHA256 = '+JSON.stringify(hash(sourceManifest))+'\n');
console.log(JSON.stringify({statements:statements.length,bytes:Buffer.byteLength(asset),sha256:hash(asset)}));
