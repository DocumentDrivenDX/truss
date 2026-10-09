/** Original UMF native declaration worklist; not installed or complete effect authority. */
import {readDocument} from '/Users/erik/Projects/umf/src/model/document';
import {getPostgresqlNode} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {renderTree} from '/Users/erik/Projects/umf/src/model/native-json';
const root='docs/helix/02-design/models/truss-layout-source-epoch-0.16.proposal.umf.json';
const astText=renderTree(getPostgresqlNode(readDocument(await Bun.file(root).text(),'json'),'/stmts'));
const nodes=JSON.parse(astText);
const hash=(s:string)=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
type Effect={kind:string;sourcePointer:string;owner:string|null;declaredName:string|null;nodeSha256:string;authoredPhysicalId:null;nativeIdentity:null};
const effects:Effect[]=[],implicit:{kind:string;creatorPointer:string;owner:string;nativeCardinalityQualified:false}[]=[],statements:{kind:string;sourcePointer:string;nodeSha256:string;reviewedDeclarationClass:boolean}[]=[];
const tables=new Map<string,Set<string>>();
const name=(relation:any)=>[relation.schemaname,relation.relname].filter(Boolean).join('.');
function add(kind:string,pointer:string,node:any,owner:string|null,declaredName:string|null=null){effects.push({kind,sourcePointer:pointer,owner,declaredName,nodeSha256:hash(JSON.stringify(node)),authoredPhysicalId:null,nativeIdentity:null});}
function constraint(node:any,pointer:string,owner:string){
 const kind=['CONSTR_DEFAULT','CONSTR_GENERATED','CONSTR_IDENTITY'].includes(node.contype)?'column_expression_or_allocator':'constraint_source';
 add(kind,pointer,node,owner,node.conname??null);
 if(['CONSTR_PRIMARY','CONSTR_UNIQUE','CONSTR_EXCLUSION'].includes(node.contype))implicit.push({kind:'constraint_supporting_index',creatorPointer:pointer,owner,nativeCardinalityQualified:false});
 if(node.contype==='CONSTR_FOREIGN')implicit.push({kind:'foreign_key_internal_trigger_dependency_set',creatorPointer:pointer,owner,nativeCardinalityQualified:false});
}
function column(node:any,pointer:string,owner:string){
 const columns=tables.get(owner);if(!columns||columns.has(node.colname))throw Error('Missing parent or repeated column declaration');
 columns.add(node.colname);add('column',pointer,node,owner,node.colname);
 for(const [i,c] of (node.constraints??[]).entries())constraint(c.Constraint,pointer+'/constraints/'+i+'/Constraint',owner);
}
const known=new Set(['CreateSchemaStmt','CommentStmt','CreateStmt','InsertStmt','CreateSeqStmt','IndexStmt','AlterTableStmt','CreateFunctionStmt','GrantStmt']);
for(const [i,wrapped] of nodes.entries()){
 const keys=Object.keys(wrapped.stmt);if(keys.length!==1)throw Error('Unclosed native statement');
 const k=keys[0]!,node=wrapped.stmt[k],pointer='/stmts/'+i+'/stmt/'+k;
 statements.push({kind:k,sourcePointer:pointer,nodeSha256:hash(JSON.stringify(node)),reviewedDeclarationClass:known.has(k)});
 if(k==='CreateStmt'){
  const owner=name(node.relation);if(tables.has(owner))throw Error('Repeated relation declaration');tables.set(owner,new Set());add('relation',pointer,node,null,owner);
  for(const [j,e] of (node.tableElts??[]).entries()){
   const p=pointer+'/tableElts/'+j;
   if(e.ColumnDef)column(e.ColumnDef,p+'/ColumnDef',owner);
   else if(e.Constraint)constraint(e.Constraint,p+'/Constraint',owner);
   else add('unreviewed_table_element',p,e,owner);
  }
 }else if(k==='AlterTableStmt'){
  const owner=name(node.relation);if(!tables.has(owner))throw Error('ALTER has no original parent declaration');
  for(const [j,c] of node.cmds.entries()){
   const command=c.AlterTableCmd,p=pointer+'/cmds/'+j+'/AlterTableCmd';
   add('alter_table_effect',p,command,owner,command.name??null);
   if(command.subtype==='AT_AddColumn')column(command.def.ColumnDef,p+'/def/ColumnDef',owner);
   else if(command.subtype==='AT_AddConstraint')constraint(command.def.Constraint,p+'/def/Constraint',owner);
   else if(!['AT_AlterColumnType','AT_DropConstraint'].includes(command.subtype))add('unreviewed_alter_effect',p,command,owner);
  }
 }else if(k==='IndexStmt')add('explicit_index',pointer,node,name(node.relation),node.idxname??null);
 else if(k==='CreateSeqStmt')add('sequence',pointer,node,null,name(node.sequence));
 else if(k==='CreateFunctionStmt')add('routine',pointer,node,null,node.funcname.map((n:any)=>n.String.sval).join('.'));
 else if(k==='CreateSchemaStmt')add('schema',pointer,node,null,node.schemaname);
 else if(k==='CommentStmt')add('comment_or_version_effect',pointer,node,null);
 else if(k==='InsertStmt')add('initialization_effect',pointer,node,name(node.relation));
 else if(k==='GrantStmt')add('privilege_effect',pointer,node,null);
 else add('unreviewed_statement_effect',pointer,node,null);
}
const nativePath='docs/helix/04-build/evidence/design-audit/source-epoch-layout-native.json';
const native=await Bun.file(nativePath).json();
const nativeTables=new Map(native.inventory.tables.map((t:any)=>['truss.'+t.name,t.columns]));
for(const [owner,columns] of tables)if(BigInt(nativeTables.get(owner) as string)!==BigInt(columns.size))throw Error('Original native relation/column-count mismatch');
if(tables.size!==nativeTables.size||tables.size!==48||effects.filter(e=>e.kind==='column').length!==454)throw Error('Incomplete current declared column inventory');
const componentFiles=new Bun.Glob('packages/postgresql/native/*.sql');const components=[];
for await(const path of componentFiles.scan('.'))components.push({path,sha256:hash(await Bun.file(path).text()),composition:'separate_private_component_not_in_layout' as const});
components.sort((a,b)=>a.path.localeCompare(b.path));
const ownerRoot='/Users/erik/Projects/umf';const ownerSourcePins=Object.fromEntries(await Promise.all(['src/model/document.ts','src/model/native-json.ts','src/adapters/postgresql/index.ts'].map(async path=>[path,hash(await Bun.file(ownerRoot+'/'+path).text())])));
const receipt={collectorSha256:hash(await Bun.file('scripts/collect-current-layout-effects.ts').text()),ownerProjection:{sourcePins:ownerSourcePins,scope:'Observed accessor source pins, not complete owner dependency/runtime qualification'},modelPath:root,modelSha256:hash(await Bun.file(root).text()),nativeAstSha256:hash(astText),nativeCountObservation:{path:nativePath,sha256:hash(await Bun.file(nativePath).text()),scope:'relation names/column counts only; not all native column/type/constraint parity'},statements,effects,expectedImplicitClasses:implicit,separateNativeComponentSources:components,counts:{statements:statements.length,relations:tables.size,columns:effects.filter(e=>e.kind==='column').length,routines:effects.filter(e=>e.kind==='routine').length,explicitIndexes:effects.filter(e=>e.kind==='explicit_index').length,implicitWorkItems:implicit.length,unreviewedSourceEffects:effects.filter(e=>e.kind.startsWith('unreviewed')).length},identityAllocation:'Original source pointers/hashes are custody locators, not durable IDs; preserve original authored-ID correspondence before allocation.',scope:'Current UMF native statement/declaration and implicit-dependency worklist; separate private SQL source hashes are not composed or admitted routines. No native identity/security/complete semantic effect inventory.',physicalCoverageComplete:false,installedQualified:false};
const out='docs/helix/04-build/evidence/design-audit/current-layout-declared-effects.json',serialized=JSON.stringify(receipt,null,2)+'\n';
if(process.argv.includes('--check')){if(await Bun.file(out).text()!==serialized)throw Error('Current effect receipt stale')}else await Bun.write(out,serialized);
console.log(JSON.stringify(receipt.counts));
