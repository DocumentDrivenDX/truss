/** Compiler-AST/resolver inventory. Findings do not constitute an admission gate. */
import {createRequire} from 'node:module';
import {readFileSync,readdirSync,writeFileSync} from 'node:fs';
import {resolve,relative,join} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(process.argv[3]??resolve(import.meta.dir,'..'));
const api=process.env.TRUSS_TYPESCRIPT_API;
if(!api)throw Error('Set TRUSS_TYPESCRIPT_API to the adopted TypeScript compiler API entrypoint');
const ts=createRequire(import.meta.url)(resolve(api));
if(ts.version!=='5.9.3')throw Error('This inventory is qualified only with TypeScript5.9.3');
const sha=(bytes:Buffer|string)=>createHash('sha256').update(bytes).digest('hex');
const files:string[]=[];
function walk(directory:string){for(const entry of readdirSync(directory,{withFileTypes:true})){
 const path=join(directory,entry.name);if(entry.isDirectory())walk(path);else if(entry.isFile()&&/\.tsx?$/.test(entry.name))files.push(path);
}}
const packages:string[]=[];const paths:Record<string,string[]>={};
for(const entry of readdirSync(join(root,'packages'),{withFileTypes:true})){
 if(!entry.isDirectory())continue;
 try{const manifest=JSON.parse(readFileSync(join(root,'packages',entry.name,'package.json'),'utf8'));
 packages.push(entry.name);paths[manifest.name]=[`packages/${entry.name}/src/index.ts`];
 walk(join(root,'packages',entry.name,'src'));
 }catch(error){if((error as any).code!=='ENOENT')throw error;}
}
const options={moduleResolution:ts.ModuleResolutionKind.Bundler,module:ts.ModuleKind.ESNext,
 target:ts.ScriptTarget.ES2022,baseUrl:root,paths};
const edges:any[]=[],dynamic:any[]=[],sourceSha256:Record<string,string>={};
const moduleOwner=(path:string)=>/^packages\/([^/]+)\//.exec(path)?.[1]??'contracts-or-other';
for(const file of files.sort()){
 const bytes=readFileSync(file),source=relative(root,file);sourceSha256[source]=sha(bytes);
 const tree=ts.createSourceFile(file,bytes.toString('utf8'),ts.ScriptTarget.Latest,true);
 if(tree.parseDiagnostics.length)throw Error(`TypeScript parse failure: ${source}`);
 function record(node:any,spec:any,kind:string,typeOnly:boolean){
  const line=tree.getLineAndCharacterOfPosition(node.getStart(tree)).line+1;
  if(!spec||!ts.isStringLiteralLike(spec)){dynamic.push({source,line,kind,disposition:'owner semantic review required'});return;}
  const request=spec.text;
  const result=ts.resolveModuleName(request,file,options,ts.sys).resolvedModule;
  const target=result?relative(root,result.resolvedFileName):null;
  edges.push({source,line,kind,typeOnly,request,target,
   resolution:result?'compiler-resolved':request.startsWith('.')?'unresolved-local':'external-or-runtime',
   sourceOwner:moduleOwner(source),targetOwner:target?moduleOwner(target):null});
 }
 function visit(node:any){
  if(ts.isImportDeclaration(node))record(node,node.moduleSpecifier,'import',!!node.importClause?.isTypeOnly);
  else if(ts.isExportDeclaration(node)&&node.moduleSpecifier)record(node,node.moduleSpecifier,'re-export',!!node.isTypeOnly);
  else if(ts.isImportEqualsDeclaration(node)&&ts.isExternalModuleReference(node.moduleReference))record(node,node.moduleReference.expression,'import-equals',false);
  else if(ts.isImportTypeNode(node))record(node,ts.isLiteralTypeNode(node.argument)?node.argument.literal:null,'import-type',true);
  else if(ts.isCallExpression(node)&&(node.expression.kind===ts.SyntaxKind.ImportKeyword||
   ts.isIdentifier(node.expression)&&node.expression.text==='require'))record(node,node.arguments[0],node.expression.kind===ts.SyntaxKind.ImportKeyword?'dynamic-import':'require',false);
  ts.forEachChild(node,visit);
 }
 visit(tree);
}
const crossPackage=edges.filter(e=>e.targetOwner&&e.sourceOwner!==e.targetOwner&&e.targetOwner!=='contracts-or-other');
const privateCrossPackage=crossPackage.filter(e=>!e.target.endsWith('/src/index.ts'));
const unresolvedLocal=edges.filter(e=>e.resolution==='unresolved-local');
const report={scope:'current-worktree TypeScript source import inventory',qualified:false,
 observedAt:new Date().toISOString(),typescriptVersion:ts.version,bunVersion:Bun.version,
 producerSha256:sha(readFileSync(import.meta.filename)),compilerApiSha256:sha(readFileSync(resolve(api))),
 packageNames:packages.sort(),sourceSha256,edgeCount:edges.length,edges,crossPackage,privateCrossPackage,
 unresolvedLocal,dynamic,
 limits:['No source execution or whole-program typecheck','No symbol-level export visibility proof',
 'Indirect loader aliases/reflection require semantic review','No native SQL dependency inventory',
 'Includes peer worktree candidates; inventory does not adopt their APIs','No existing-debt baseline or CI gate established']};
const output=process.argv[2];if(!output)throw Error('Supply an explicit receipt destination');
writeFileSync(resolve(output),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({files:files.length,edges:edges.length,crossPackage:crossPackage.length,
 privateCrossPackage:privateCrossPackage.length,unresolvedLocal:unresolvedLocal.length,dynamic:dynamic.length,qualified:false}));
if(unresolvedLocal.length)process.exitCode=1;
