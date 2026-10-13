// Current original UMF observations only; no native acceptance or execution.
import * as owner from './producer.js';
const version='truss-core08-catalog-source/0.1.0';
const hash=s=>new Bun.CryptoHasher('sha256').update(s).digest('hex');
const bytes=s=>new TextEncoder().encode(s).length;
try {
 const text=await Bun.stdin.text();if(bytes(text)>8_000_000)throw Error('resource');
 const request=JSON.parse(text);
 if(!request||Object.keys(request).sort().join(',')!=='documentId,documentJson,documentRevision'||
   !['documentId','documentRevision','documentJson'].every(k=>typeof request[k]==='string'&&request[k].length))throw Error('input');
 const original=request.documentJson;if(bytes(original)>4_000_000)throw Error('resource');
 const source=owner.readDocument(original,'json');if(source.umf!=='0.8.0'||source.id!==request.documentId)throw Error('source');
 const schedule=[];
 const add=(operation,identity)=>{if(schedule.length>=4096)throw Error('resource');schedule.push([operation,identity]);};
 add('inspectCoreSchemaProperties',{scope:'document'});
 for(const module of source.modules){
  add('inspectCoreSchemaProperties',{scope:'module',module:module.id});add('inspectCoreRelationships',{module:module.id});
  for(const element of module.elements){
   add('inspectCoreSchemaProperties',{scope:'element',module:module.id,element:element.id});
   for(const operation of ['inspectCoreElementKind','inspectCoreNullability','inspectCoreCardinality','inspectCoreFacets','inspectCoreRecordMembers','inspectCoreScalarType','inspectCoreReferenceLinks'])add(operation,{module:module.id,element:element.id});
   if(element.kind==='record')add('inspectCoreKeys',{module:module.id,element:element.id});
  }
 }
 // Each original owner result retains the source. Reserve selected source
 // replication before calls; output checks additionally bound actual responses.
 // These are transport/work bounds, not a proof of total heap or CPU use.
 if(schedule.length*(6*bytes(original)+16384)>16_000_000)throw Error('resource');
 const observations=[];let retained=0;
 for(const [operation,identity] of schedule){
  const result=owner[operation](source,identity);
  const captured={operation,identity,result};retained+=bytes(JSON.stringify(captured));
  if(retained>16_000_000)throw Error('resource');observations.push(captured);
 }
 const response={interfaceVersion:version,status:'prepared',nativeReady:false,documentId:request.documentId,documentRevision:request.documentRevision,sourceSha256:hash(original),originalDocumentJson:original,observations};
 const encoded=JSON.stringify(response);if(bytes(encoded)>16_000_000)throw Error('resource');
 process.stdout.write(encoded);
} catch(error) {
 // Diagnostics cannot become native authority or leak a partial observation set.
 process.stdout.write(JSON.stringify({interfaceVersion:version,status:'refused',nativeReady:false,reason:error?.message==='resource'?'resource':'source'}));
}
