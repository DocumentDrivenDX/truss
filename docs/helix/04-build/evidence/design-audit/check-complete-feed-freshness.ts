/** Existing declared wire shape only; no native fact clock or authority qualification. */
const {default:Ajv}=await import(process.argv[2]);const ajv=new Ajv({strict:true});
const root='docs/helix/02-design/contracts/';for(const f of new Bun.Glob('*.schema.json').scanSync(root))ajv.addSchema(await Bun.file(root+f).json());
const id='urn:truss:draft:complete-feed-freshness:0.2.0',request=ajv.getSchema(id)!,result=ajv.compile({$ref:id+'#/$defs/result'});
const pin={identity:'shape-only',version:'0.1.0',sha256:'0'.repeat(64)},artifact={identity:'shape-only',bytesBase64:'eA==',sha256:'0'.repeat(64)};
const context={sourceEpoch:'epoch',feedProfile:'feed',scopeIdentity:'scope'},worker={context,consumerId:'consumer',registrationId:'registration',generation:'1'};
const req={interfaceVersion:'truss-complete-feed-freshness/0.2.0',worker,observationProfile:pin};
const observed={outcome:'observed',worker,sourceApplied:{state:'seed',context,seedId:'seed',activationEvidenceSha256:'0'.repeat(64),seedProfile:pin},checkpointUpdatedAt:'selected-clock-text',observedAt:'selected-clock-text',safeWatermarkXid:'1',publishable:{state:'empty',ageNanoseconds:'0'},held:{state:'present',oldestWriteAt:'selected-clock-text',ageNanoseconds:'12'},observationProfile:pin,factClockProfile:pin,observation:artifact,limitations:[]};
const cases:any[]=[];const failures:string[]=[];
function probe(name:string,source:any,v:any,expected:boolean,change:(x:any)=>void=()=>{}){const x=structuredClone(source);change(x);const actual=!!v(x);cases.push({case:name,expected,actual});if(actual!==expected)failures.push(name);}
probe('request',req,request,true);
probe('old request version',req,request,false,x=>x.interfaceVersion='truss-complete-feed-freshness/0.1.0');
probe('numeric worker generation',req,request,false,x=>x.worker.generation=1);
probe('observed result',observed,result,true);
probe('missing fact clock',observed,result,false,x=>delete x.factClockProfile);
probe('missing original observation',observed,result,false,x=>delete x.observation);
probe('old seed boundary',observed,result,false,x=>delete x.sourceApplied.seedProfile);
probe('numeric watermark',observed,result,false,x=>x.safeWatermarkXid=1);
probe('negative age',observed,result,false,x=>x.held.ageNanoseconds='-1');
probe('empty has timestamp',observed,result,false,x=>x.publishable.oldestWriteAt='leak');
probe('backlog unavailable',observed,result,true,x=>x.held={state:'unavailable',reason:'clock'});
probe('unavailable backlog leaks age',observed,result,false,x=>x.held={state:'unavailable',reason:'clock',ageNanoseconds:'0'});
probe('scope unavailable', {outcome:'unavailable',reason:'authorization'},result,true);
probe('unavailable leaks progress',{outcome:'unavailable',reason:'authorization'},result,false,x=>x.sourceApplied=observed.sourceApplied);
probe('fabricated coherent timestamp remains shape valid',observed,result,true,x=>x.observedAt='forged');
const path=root+'complete-feed-freshness-v0.2.schema.json';const schemaBytes=new Uint8Array(await Bun.file(path).arrayBuffer());
const receipt={scope:'Closed freshness request/result/backlog shape; fabricated timestamps/artifact evidence intentionally require semantic/native refusal. No native observation/clock/authorization/worker/progress qualification.',cases,failures,schema:{path,sha256:new Bun.CryptoHasher('sha256').update(schemaBytes).digest('hex')}};
await Bun.write('docs/helix/04-build/evidence/design-audit/complete-feed-freshness-shapes.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({cases:cases.length,failures}));if(failures.length)process.exit(1);export {};
