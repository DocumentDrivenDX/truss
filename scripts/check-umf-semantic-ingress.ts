/** Actual upstream producer evidence; does not install or accept a Truss catalog. */
import {verifyExactArtifacts} from '@documentdrivendx/truss-postgresql';
import {readFile,writeFile,mkdtemp} from 'node:fs/promises';
import {join} from 'node:path';
const umfRoot=process.argv[2],examples=process.argv[3];if(!umfRoot||!examples)throw Error('Pinned UMF checkout and Ashlar example directory required');
const revision='fac1497a5ac5cb39bbaaac34eb0da8dc8b208c69';
const git=(args:string[])=>{const result=Bun.spawnSync(['git',...args],{cwd:umfRoot});if(result.exitCode)throw Error('UMF source observation failed');return new TextDecoder().decode(result.stdout).trim();};
if(git(['rev-parse','HEAD'])!==revision||git(['status','--porcelain']))throw Error('Exact clean UMF source required');
const temporary=await mkdtemp('/private/tmp/truss-umf-validator-');const entry=join(temporary,'producer.ts');
await writeFile(entry,`export {readDocument} from ${JSON.stringify(umfRoot+'/src/model/document.ts')};\nexport {validateDocument} from ${JSON.stringify(umfRoot+'/src/validation/document.ts')};\n`);
await writeFile(entry,`export {inspectCoreNullability} from ${JSON.stringify(umfRoot+'/src/model/nullability.ts')};\nexport {inspectCoreCardinality} from ${JSON.stringify(umfRoot+'/src/model/cardinality.ts')};\nexport {inspectCoreFacets} from ${JSON.stringify(umfRoot+'/src/model/facets.ts')};\nexport {inspectCoreKeys} from ${JSON.stringify(umfRoot+'/src/model/keys.ts')};\nexport {inspectCoreRelationships} from ${JSON.stringify(umfRoot+'/src/model/relationships.ts')};\n`,{flag:'a'});
const built=await Bun.build({entrypoints:[entry],outdir:temporary,target:'browser',format:'esm',naming:'producer.js'});if(!built.success)throw Error('Actual UMF producer build failed');
const bundle=await readFile(join(temporary,'producer.js'));const producer=await import(join(temporary,'producer.js'));
const results=[];const inventories=[];
for(const identity of ['schema-v1.umf.json','schema-v2.umf.json','schema-v3.umf.json','schema-unknown.umf.json']){
 const bytes=await readFile(examples+'/'+identity);const sha256=new Bun.CryptoHasher('sha256').update(bytes).digest('hex');
 const [artifact]=await verifyExactArtifacts([{identity,bytesBase64:bytes.toString('base64'),sha256}],{maxArtifacts:1,maxSingleBytes:65536,maxTotalBytes:65536});
 const text=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(Buffer.from(artifact.bytesBase64,'base64'));
 const document=producer.readDocument(text,'json');const validation=producer.validateDocument(document);
 const entries=[];
 for(let mi=0;mi<document.modules.length;mi++){
  const module=document.modules[mi];
  entries.push({definition:{artifactSha256:sha256,path:'/modules/'+mi},producer:'inspectCoreRelationships',originalResult:producer.inspectCoreRelationships(document,{module:module.id}),requiredCheckProducer:null,nativeBinding:null});
  for(let ei=0;ei<module.elements.length;ei++){
   const element=module.elements[ei],identity={module:module.id,element:element.id},definition={artifactSha256:sha256,path:'/modules/'+mi+'/elements/'+ei};
   const operations=element.kind==='field'?['inspectCoreNullability','inspectCoreCardinality','inspectCoreFacets']:element.kind==='record'?['inspectCoreKeys']:[];
   for(const operation of operations)entries.push({definition,producer:operation,originalResult:producer[operation](document,identity),requiredCheckProducer:null,nativeBinding:null});
  }
 }
 inventories.push({identity,originalArtifact:artifact,originalValidation:validation,entries,uninterpretedDiagnostics:validation.diagnostics.filter((d:any)=>d.code.startsWith('UNKNOWN')),supportProfile:null,writableAcceptance:'unavailable_no_qualified_semantic_check_composition'});
 if(identity==='schema-unknown.umf.json'&&JSON.stringify(document['x-future-assertion'])!==JSON.stringify({meaning:'retained until supported'}))throw Error('Unknown UMF content lost');
 results.push({identity,sha256,umf:document.umf,originalValidation:validation,aggregateValidationCondition:validation.valid&&validation.complete?'valid_complete':'not_valid_complete',writableAcceptance:'unavailable_no_qualified_semantic_check_composition',acceptedCatalogRevision:null});
}
await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/umf-semantic-ingress.json',import.meta.url),JSON.stringify({umfSourceRevision:revision,producerBundleSha256:new Bun.CryptoHasher('sha256').update(bundle).digest('hex'),loader:'bun/'+Bun.version,results,qualification:'Actual pinned UMF readDocument/validateDocument producer on original Ashlar example files after public Truss byte-integrity ingress. Complete original diagnostics retained; unknown assertion preservation checked. Aggregate condition describes this document producer only, not completeness of separately selected semantic checks or writable readiness. Browser-target producer bundle executed in Bun, not a real browser. No qualified isolation/resource validator service, native catalog acceptance, installation, accepted IDs, transforms or streaming claim.'},null,2)+'\n');
await writeFile(new URL('../docs/helix/04-build/evidence/inert-assembly/umf-check-inventory.json',import.meta.url),JSON.stringify({umfSourceRevision:revision,producerBundleSha256:new Bun.CryptoHasher('sha256').update(bundle).digest('hex'),inventories,qualification:'Actual UMF inspectors enumerate original declaration meanings with exact source artifact/pointer and full original operation results. Inspection is not a complete semantic value check or original author/native provenance. No required-check producer or native binding is fabricated; support profile remains unselected. Unknown scopes and original diagnostics remain preserved. This inventory is a prerequisite, not writable catalog acceptance.'},null,2)+'\n');
console.log(JSON.stringify(results.map(result=>({identity:result.identity,valid:result.originalValidation.valid,complete:result.originalValidation.complete,aggregateValidationCondition:result.aggregateValidationCondition}))));
