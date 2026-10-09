/** Extract existing UMF native declarations; no SQL generation or execution. */
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {getPostgresqlNode} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const models=[
 'docs/helix/02-design/models/truss-layout-source-epoch-0.16.proposal.umf.json',
 'docs/helix/02-design/contracts/operation-configuration-storage-v0.1.proposal.umf.json',
 'docs/helix/02-design/contracts/layout-migration-storage-v0.1.proposal.umf.json',
];
const hash=(value:string)=>new Bun.CryptoHasher('sha256').update(value).digest('hex');
const ownerSources=[];
for(const path of [
 '/Users/erik/Projects/umf/src/model/document.ts',
 '/Users/erik/Projects/umf/src/adapters/postgresql/index.ts',
 '/Users/erik/Projects/umf/src/model/native-json.ts',
]) ownerSources.push({path,sha256:hash(await Bun.file(path).text())});
const sources=[];const objects=[];
for(const path of models){
 const bytes=await Bun.file(path).text();
 const nodes=JSON.parse(renderTree(getPostgresqlNode(readDocument(bytes,'json'),'/stmts')));
 sources.push({path,sha256:hash(bytes)});
 for(const [index,node] of nodes.entries()){
  const kind=Object.keys(node.stmt)[0];
  if(!['IndexStmt','CreateSeqStmt','CreateStmt','AlterTableStmt'].includes(kind))continue;
  objects.push({sourceModel:path,sourcePointer:`/stmts/${index}/stmt/${kind}`,kind,definition:node.stmt[kind]});
 }
}
const output={scope:'Original UMF native index/sequence declaration capture only; no native or installation qualification',ownerSources,sources,objects};
await Bun.write('docs/helix/04-build/evidence/design-audit/pgserver-native-object-declarations.json',JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify({indexes:objects.filter(o=>o.kind==='IndexStmt').length,sequences:objects.filter(o=>o.kind==='CreateSeqStmt').length,tables:objects.filter(o=>o.kind==='CreateStmt').length}));
