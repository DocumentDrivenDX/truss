/** Existing UMF statement composition; source fidelity only, no physical/native qualification. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {getPostgresqlNode,proposePostgresqlNodeEdit,exportPostgresqlSql,importPostgresqlSql} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const modelPath='docs/helix/02-design/models/truss-layout-0.2.umf.json';
const original=await Bun.file(modelPath).text();
const d=readDocument(original,'json');
const s=getPostgresqlNode(d,'/stmts');if(s.kind!=='array')throw Error('statement array absent');
const outputs:string[]=[];for(const node of s.items){const one=proposePostgresqlNodeEdit(d,'/stmts','['+renderTree(node)+']').document;outputs.push(await exportPostgresqlSql(one,backend));}
const joined=outputs.join(';\n')+';';
const reloaded=await importPostgresqlSql(joined,backend,{id:'truss-statement-composition-probe'});
if(await exportPostgresqlSql(reloaded,backend)!==await exportPostgresqlSql(d,backend))throw Error('composition re-export mismatch');
const hash=(text:string)=>new Bun.CryptoHasher('sha256').update(text).digest('hex');
if(await Bun.file(modelPath).text()!==original)throw Error('model changed during source check');
const joins=['',...outputs.slice(1).map(()=>';\n'),';'];
const statements=outputs.map((sql,ordinal)=>({ordinal:String(ordinal),sourcePath:'/stmts/'+ordinal,sql,sha256:hash(sql)}));
const receipt={scope:'Existing UMF guarded single-statement export and explicit composition/source re-import only; no complete physical-effect/source inventory, native execution, installer or accepted binding',modelPath,modelSha256:hash(original),backend:backend.identity,bunVersion:Bun.version,statements,joins,joinedSqlSha256:hash(joined),joinedOwnerReexportExact:true,physicalCoverageComplete:false};
await Bun.write('docs/helix/04-build/evidence/design-audit/bootstrap-statement-composition.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({statements:statements.length,joinedOwnerReexportExact:true,physicalCoverageComplete:false,nativeExecution:false}));
