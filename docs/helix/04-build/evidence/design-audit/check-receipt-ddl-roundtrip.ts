/** Existing UMF owner parser/exporter; no native database or installation. */
import {backend} from '/Users/erik/Projects/umf/native/postgresql/runtime';
import {importPostgresqlSql,exportPostgresqlSql,getPostgresqlSource} from '/Users/erik/Projects/umf/src/adapters/postgresql';
import {getPostgresqlDdlDeclarations} from '/Users/erik/Projects/umf/src/adapters/postgresql/declarations';
import {writeDocument,readDocument} from '/Users/erik/Projects/umf/src/model/document';
const failures:string[]=[],results:any[]=[];
for(const name of ['request-receipt-layout','request-receipt-statements']){
 const path='docs/helix/02-design/contracts/'+name+'-v0.1.draft.sql',source=await Bun.file(path).text();
 try{
  const document=await importPostgresqlSql(source,backend,{id:'truss-'+name+'-draft'});
  const output=await exportPostgresqlSql(document,backend),declarations=getPostgresqlDdlDeclarations(document);
  if(name==='request-receipt-layout'){
   const modelText=writeDocument(document,'json'),reloaded=readDocument(modelText,'json');
   if(getPostgresqlSource(reloaded)!==source)failures.push('receipt UMF serialized original source changed');
   if(await exportPostgresqlSql(reloaded,backend)!==output)failures.push('receipt reloaded export changed');
   const modelPath='docs/helix/02-design/models/truss-receipt-candidate.umf.json';
   await Bun.write(modelPath,modelText);
   await Bun.write('docs/helix/02-design/models/truss-receipt-candidate.capture.json',JSON.stringify({profile:'truss-native-layout-capture/0.1.0',status:'unadopted_candidate',source:path,sourceSha256:new Bun.CryptoHasher('sha256').update(source).digest('hex'),model:modelPath,modelSha256:new Bun.CryptoHasher('sha256').update(modelText).digest('hex'),backend:backend.identity,checks:{sourceArchiveExact:true,jsonReload:true,reloadedExportExact:true},physicalIdentityAllocationComplete:false,completeExporterCorrespondence:false,installed:false,adoptionPrerequisites:['ADR-005 and governing layout reconciliation','complete authored physical identities and native definitions','complete UMF exporter statement/source correspondence','native functions/privileges/clock/namespace profiles']},null,2)+'\n');
  }
  if(getPostgresqlSource(document)!==source)failures.push(name+' original source archive changed');
  if(declarations.complete!==false)failures.push(name+' declaration inventory overclaimed completeness');
  const xidColumns=declarations.declarations.flatMap(d=>d.columns).filter(c=>['original_writer_xid','original_update_writer_xid','expiry_writer_xid'].includes(c.element.name));
  if(name==='request-receipt-layout'&&(xidColumns.length!==3||xidColumns.some(c=>c.typeResolution!=='unresolved'||c.element.scalarType!==undefined)))failures.push('xid8 native type must remain unresolved, not guessed integer');
  await Bun.write('docs/helix/04-build/evidence/design-audit/'+name+'.owner-export.sql',output);
  results.push({path,inputSha256:new Bun.CryptoHasher('sha256').update(source).digest('hex'),exportSha256:new Bun.CryptoHasher('sha256').update(output).digest('hex'),originalSourcePreserved:getPostgresqlSource(document)===source,declarationStatus:declarations.status,complete:declarations.complete,declarations:declarations.declarations.length,unhandled:declarations.unhandled.length,xidColumns:xidColumns.map(c=>({name:c.element.name,typeResolution:c.typeResolution})),diagnostics:declarations.diagnostics.map(d=>({code:d.code,severity:d.severity,path:d.path}))});
 }catch(error){failures.push(name+': '+String(error));}
}
const receipt={scope:'UMF pinned parser/export codec and AST reparse guard only; no database execution, permissions, complete statement correspondence API or installed layout support',backend:backend.identity,results,failures};
await Bun.write('docs/helix/04-build/evidence/design-audit/receipt-ddl-roundtrip.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({scope:receipt.scope,results:results.map(r=>({path:r.path,declarations:r.declarations,unhandled:r.unhandled,xidColumns:r.xidColumns})),failures}));if(failures.length)process.exit(1);
