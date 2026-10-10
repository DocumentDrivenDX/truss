/** Closed report shape evidence only; inventories/native facts require admission. */
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const {default:Ajv}=await import(process.argv[2]);
const ajv=new Ajv({strict:true});
const dependencyNames=['exact-value','history-record','history-event','acceptance-input','acceptance-rejection','enforcement-report','direct-cursor'];
for(const name of dependencyNames)
 ajv.addSchema(await Bun.file(`docs/helix/02-design/contracts/${name}-v0.1.schema.json`).json());
const validate=ajv.compile(await Bun.file('docs/helix/02-design/contracts/acceptance-report-v0.1.schema.json').json());
const pin={identity:'fixture',version:'0.1.0',sha256:'a'.repeat(64)};
const artifact={identity:'fixture',bytesBase64:'e30=',sha256:'a'.repeat(64)};
const input={interfaceVersion:'truss-acceptance-input/0.1.0',layoutProfile:pin,acceptanceProfile:pin,validatorProfile:pin,supportProfile:pin,documents:[{documentId:'doc',documentRevision:'r1',artifact,umfProfile:pin,ingress:{kind:'native'}}],binding:{state:'absent'},policy:{unknownEndpoint:'reject',loss:'strict',profile:pin},transforms:[]};
const report={interfaceVersion:'truss-acceptance-report/0.1.0',reportProfile:pin,rev:'1',originalExecution:{installationId:'installation',sourceEpoch:'epoch',origin:{asserted:{operation:'accept'},databaseRole:'role'},journalOrigin:{asserted:{kind:'string',text:'origin'},databaseRole:'role'},originMappingProfile:pin,captureProfile:pin,contextEvidence:artifact},acceptedInput:input,transformRegistrations:[],umf:[{version:'0.7.0',interpretationProfile:pin,supportedSubset:artifact}],documents:[{doc_id:'doc',doc_revision:'r1',content_sha256:artifact.sha256,ord:'0'}],diagnostics:[],documentInterpretations:[{documentId:'doc',contentSha256:artifact.sha256,interpretationProfile:pin,completeness:'complete',evidence:artifact}],counts:{typesAdded:'0',propertiesAdded:'0',keysAdded:'0',relationshipsAdded:'0',endpointsAdded:'0',elementsRetired:'0'},provisional:[],rebinds:[],assertions:{interfaceVersion:'truss-enforcement-report/0.1.0',catalogRevision:'1',reportProfile:pin,layoutProfile:pin,scope:{kind:'complete'},assertionInventorySha256:artifact.sha256,entries:[]},pending_indexes:[],losses:[],extensions:[]};
const identity={id:'1',typeId:'1',definitionPin:'fixture',owner:{documentId:'doc',moduleId:'module'}};
const eventContext={interfaceVersion:'truss-history-event/0.1.0',sourceEpoch:'epoch',historyProfile:'fixture',xid:'1',seq:'1',identity,eventVersion:'2',eventCatalogRevision:'1',mutationGroup:{profile:'truss-history-group/0.1.0',eventCount:'1',orderedEventDigest:'0'.repeat(64)},origin:{asserted:{kind:'null'},databaseRole:'role'}};
const present={present:true,value:{kind:'null'}};const absent={present:false};
const rebind={...eventContext,operation:'rebind',retainedName:'retained',propertyId:'1',beforeDefinitionContext:'old',afterDefinitionPin:'new',retainedBefore:present,retainedAfter:absent,propertyBefore:absent,propertyAfter:present};
const property={...eventContext,operation:'property',propertyId:'1',definitionPin:'fixture',before:absent,after:present};
const record={interfaceVersion:'truss-history-record/0.1.0',identity,recordVersion:'1',catalogRevision:'1',createdAt:'fixture',updatedAt:'fixture',properties:[],retained:[],kind:'object',ownership:{state:'rootless'}};
const metadata={...eventContext,operation:'metadata',before:record,after:record};
const validateEvent=ajv.getSchema('urn:truss:draft:history-event:0.1.0');
for(const event of [rebind,property,metadata])if(!validateEvent?.(event))throw Error('Control event must independently satisfy event schema');
const cases:[string,unknown,boolean][]=[
 ['complete',report,true],
 ['complete rebind variant',{...report,rebinds:[rebind]},true],
 ['valid property cannot enter rebind inventory',{...report,rebinds:[property]},false],
 ['valid metadata cannot enter rebind inventory',{...report,rebinds:[metadata]},false],
 ['missing original transform inventory',Object.fromEntries(Object.entries(report).filter(([k])=>k!=='transformRegistrations')),false],
 ['manifest needs original recognition',{...report,transformRegistrations:[{registration:pin,manifest:artifact}]},false],
 ['manifest cannot substitute callback code',{...report,transformRegistrations:[{registration:pin,manifest:artifact,originalImplementationRecognition:artifact,source:'return null'}]},false],
 ['extra registration needs semantic inventory refusal',{...report,transformRegistrations:[{registration:pin,manifest:artifact,originalImplementationRecognition:artifact}]},true],
 ['accepted warnings',{...report,diagnostics:[{classification:'upstream_validation',source:{kind:'document',artifact,sourcePointer:''},diagnosticProfile:pin,diagnostic:artifact}],documentInterpretations:[{...report.documentInterpretations[0],completeness:'partial'}]},true],
 ['missing diagnostics',Object.fromEntries(Object.entries(report).filter(([key])=>key!=='diagnostics')),false],
 ['projected assertions',{...report,assertions:{...report.assertions,scope:{kind:'authorized_projection',authorizedScopeIdentity:'scope'}}},false],
 ['host-number counts',{...report,counts:{...report.counts,typesAdded:0}},false],
 ['unknown required member',{...report,ready:true},false],
 ['missing original input',Object.fromEntries(Object.entries(report).filter(([key])=>key!=='acceptedInput')),false],
 ['mismatched inventory remains semantic',{...report,documents:[]},true],
 ['forged evidence remains semantic',report,true]
];
const failures=cases.filter(([,value,expected])=>Boolean(validate(value))!==expected).map(([name])=>name);
const hash=(bytes:ArrayBuffer)=>createHash('sha256').update(new Uint8Array(bytes)).digest('hex');
const sourceNames=[...dependencyNames,'acceptance-report'];
const sourceSha256=Object.fromEntries(await Promise.all(sourceNames.map(async name=>[name+'-v0.1.schema.json',hash(await Bun.file('docs/helix/02-design/contracts/'+name+'-v0.1.schema.json').arrayBuffer())])));
const validatorPackage=await Bun.file(new URL('../package.json',pathToFileURL(process.argv[2]))).json();
const helperSha256=hash(await Bun.file(new URL(import.meta.url)).arrayBuffer());
console.log(JSON.stringify({scope:'accepted report shape only; no native/runtime producer/profile adoption',cases:cases.length,failures,sourceSha256,helperSha256,validator:{name:validatorPackage.name,version:validatorPackage.version},runtime:{bun:process.versions.bun ?? null},nativeEvidence:false,profileAdopted:false},null,2));
if(failures.length)process.exit(1);
export {};
