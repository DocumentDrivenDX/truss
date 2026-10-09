/** Existing UMF-owned native tree extraction; no SQL parsing/lowering in Truss. */
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {getPostgresqlNode} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const owner=Bun.spawnSync(['git','-C','/Users/erik/Projects/umf','rev-parse','HEAD']);
if(new TextDecoder().decode(owner.stdout).trim()!=='16c35e8d943769ccfa7bb57d16785aa7159abe65')throw Error('Review changed owner source before extraction');
for(const [version,path] of [['0.12','docs/helix/02-design/models/truss-layout-reference-history-0.12.proposal.umf.json'],['0.15','docs/helix/02-design/models/truss-layout-qualified-property-0.15.proposal.umf.json']] as const){
 const original=readDocument(await Bun.file(path).text(),'json');
 await Bun.write(`docs/helix/04-build/evidence/design-audit/core-refresh-${version}.native-ast.json`,renderTree(getPostgresqlNode(original,'/stmts'))+'\n');
}
