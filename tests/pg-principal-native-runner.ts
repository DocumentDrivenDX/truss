/** Dedicated disposable native fixture; no installed-policy authority. */
import {createPgConnectionSource,createOrdinarySubjectKeyBinding} from '../packages/pg-runtime/src/index';
import * as owner from '../packages/python/src/truss/_umf_keys08/producer.js';
import {createHash} from 'node:crypto';
const originalRequest=JSON.parse(await Bun.file(import.meta.dir+'/../packages/python/tests/fixtures/security-mapping-request.json').text());
const originalSourceText=JSON.parse(await Bun.file(import.meta.dir+'/../packages/python/tests/fixtures/security-mapping-request.json').text()).modules[0].documentJson;
function originalSubjectInspector(sourceText:string){
 const request=structuredClone(originalRequest);
 if(sourceText!==originalSourceText){
  const source=JSON.parse(sourceText);const ref=(element:string)=>({documentId:source.id,moduleId:'m',elementId:element});
  request.modules[0].documentJson=sourceText;request.modules[0].pin.sha256=createHash('sha256').update(sourceText).digest('hex');
  const ontology=JSON.parse(request.ontologyJson);ontology.subject=ref('Staff');ontology.entities=[{type:ref('Staff'),keyId:'pk',fields:source.modules[0].elements.filter((e:any)=>e.kind==='field').map((e:any)=>({ref:ref(e.id),protection:'unprotected'}))}];ontology.associations=[];ontology.context=[];
  request.ontologyJson=JSON.stringify(ontology);
  const policy=JSON.parse(request.policyJson);policy.rules=[{id:'allow',effect:'permit',actions:['read'],target:[ref('Staff')],condition:{op:'literal',value:true}}];request.policyJson=JSON.stringify(policy);
  const profile=JSON.parse(request.queryProfileJson);profile.modelPins=[request.modules[0].pin];profile.policySha256=createHash('sha256').update(request.policyJson).digest('hex');profile.ontologySha256=createHash('sha256').update(request.ontologyJson).digest('hex');profile.targets=[ref('Staff')];profile.bindings=[];request.queryProfileJson=JSON.stringify(profile);
  request.sql='SELECT r.k0 FROM Staff r';request.parameters={};
 }
 return (selection:any)=>{
  const binary=process.env.TRUSS_SUBJECT_KEY_INSPECTOR_BINARY;if(!binary)throw Error('Original subject inspector required');
  const run=Bun.spawnSync([binary],{stdin:new TextEncoder().encode(JSON.stringify({request,subjectKeyProbe:selection})),stdout:'pipe',stderr:'pipe'});
  if(run.exitCode!==0)throw Error(new TextDecoder().decode(run.stderr));
  const response=JSON.parse(new TextDecoder().decode(run.stdout));if(response.securityReady!==false||response.subjectKeyInspectionPassed!==true)throw Error('Original subject inspection refused');
  return undefined;
 };
}
const config=JSON.parse(await Bun.stdin.text());const cases:string[]=[];
const refuses=(fn:()=>unknown)=>{let refused=false;try{fn();}catch{refused=true;}if(!refused)throw Error('Observation lifecycle did not refuse');};
const transaction={isolation:'repeatable_read' as const,accessMode:'read_only' as const};
async function check(name:string,user:string,options:any,positive:boolean,expected?:string){
 const host=createPgConnectionSource({...config,user,max:1},options);let failed=false;
 try{
  const connection=await host.source.acquire();refuses(()=>host.observeOrdinarySubject(connection));
  refuses(()=>host.observeOrdinarySubject({...connection}));await connection.begin(transaction);
  if(options.ordinarySubject){
   const observed=host.observeOrdinarySubject(connection);
   if(observed.principal!==user||JSON.stringify(observed.keyColumns)!==JSON.stringify(options.ordinarySubject.keyColumns)||observed.keyValues[0]!=='alice'||observed.keyHex[0]!==Buffer.from('alice').toString('hex'))throw Error('Native subject bytes lost');
   if(!Object.isFrozen(observed)||!Object.isFrozen(observed.keyValues)||!Object.isFrozen(observed.keyHex)||!Object.isFrozen(observed.keyColumns))throw Error('Subject observation mutable');
   if(observed.keyValues.length===1){
    const binder=createOrdinarySubjectKeyBinding({host,owner,inspectSubjectKey:originalSubjectInspector(originalSourceText),sourceText:originalSourceText,identity:{module:'m',element:'Staff',key:'pk'},keyColumns:['staff_id'],encodings:['string']});
    const encoded=binder.encode(connection);
    const expected=owner.encodeCoreKeyTuple(owner.readJsonValue(originalSourceText,'json'),{module:'m',element:'Staff',key:'pk'},[{string:'alice'}]);
    if(encoded.bytesHex!==expected.bytesHex||encoded.observation!==observed)throw Error('Original semantic subject key mismatch');
    refuses(()=>binder.encode({...connection}));
   }
   if(observed.keyValues.length===2&&observed.keyValues[1]!=='9007199254740993')throw Error('Subject key rounded');
  }else refuses(()=>host.observeOrdinarySubject(connection));
  const result=await connection.execute({sql:'SELECT SESSION_USER::pg_catalog.text AS actor,CURRENT_USER::pg_catalog.text AS effective',parameters:[]});
  if(JSON.stringify(result.rows)!==JSON.stringify([[{state:'text',text:user},{state:'text',text:user}]]))throw Error('Native caller changed');
  await connection.rollback();refuses(()=>host.observeOrdinarySubject(connection));await connection.release();refuses(()=>host.observeOrdinarySubject(connection));await host.close();
 }catch(error){if(positive)throw error;failed=true;if(expected&&!String(error).includes(expected))throw Error('Wrong native refusal: '+name);if(host.quarantinedCount()!==1)throw Error('Uncertain admission lost quarantine');await host.shutdownQuarantinedTransports();}
 if(failed===positive)throw Error('Unexpected native admission: '+name);cases.push(name);
}
const observer={schema:'principal_diag',routine:'observe'};
const subject={schema:'principal_diag',routine:'subject_text',keyColumns:['staff_id']};
await check('direct native caller','principal_alice',{ordinaryPrincipal:'principal_alice'},true);
await check('observer and text subject','principal_alice',{ordinaryPrincipal:'principal_alice',ordinaryPrincipalObserver:observer,ordinarySubject:subject},true);
await check('observer and name subject','principal_alice',{ordinaryPrincipal:'principal_alice',ordinaryPrincipalObserver:observer,ordinarySubject:{...subject,routine:'subject_name',actorCarrier:'name'}},true);
await check('ordered exact TEXT composite subject','principal_alice',{ordinaryPrincipal:'principal_alice',ordinarySubject:{...subject,routine:'subject_composite',keyColumns:['staff_id','ordinal']}},true);
await check('wrong pinned caller','principal_alice',{ordinaryPrincipal:'principal_bob'},false,'Pinned ordinary principal unavailable');
await check('unbound native subject','principal_bob',{ordinaryPrincipal:'principal_bob',ordinaryPrincipalObserver:observer,ordinarySubject:subject},false,'Original subject binding unavailable');
await check('wrong subject columns','principal_alice',{ordinaryPrincipal:'principal_alice',ordinarySubject:{...subject,keyColumns:['different']}},false,'Original subject binding unavailable');
await check('wrong subject output OID','principal_alice',{ordinaryPrincipal:'principal_alice',ordinarySubject:{...subject,routine:'subject_wrong_type'}},false,'Original subject binding unavailable');
await check('native superuser refused',config.user,{ordinaryPrincipal:config.user},false,'Pinned ordinary principal unavailable');
const typedHost=createPgConnectionSource({...config,user:'principal_alice',max:1},{ordinaryPrincipal:'principal_alice',ordinarySubject:{schema:'principal_diag',routine:'subject_typed',keyColumns:['k0','k1','k2','k3','k4']}});
const typedConnection=await typedHost.source.acquire();await typedConnection.begin(transaction);
const typedSource=JSON.parse(originalSourceText);const kinds=['string','boolean','integer','decimal','binary'];
typedSource.modules[0].elements=[{id:'Staff',kind:'record',name:'Staff',members:kinds.map((_,i)=>({module:'m',element:'k'+i})),keys:[{id:'pk',name:'Key',fields:kinds.map((_,i)=>({module:'m',element:'k'+i}))}],extensions:{}},...kinds.map((kind,i)=>({id:'k'+i,name:'k'+i,kind:'field',scalarType:kind,cardinality:'one',nullability:'required',extensions:{},...(kind==='decimal'?{facets:{precision:30,scale:4}}:{})}))];
const typedBinding=createOrdinarySubjectKeyBinding({host:typedHost,owner,inspectSubjectKey:originalSubjectInspector(JSON.stringify(typedSource)),sourceText:JSON.stringify(typedSource),identity:{module:'m',element:'Staff',key:'pk'},keyColumns:['k0','k1','k2','k3','k4'],encodings:kinds.map(()=> 'core-literal-json')});
const nativeTypedKey=typedBinding.encode(typedConnection);
const expectedTypedKey=owner.encodeCoreKeyTuple(typedSource,{module:'m',element:'Staff',key:'pk'},[{string:'Δ\uFEFF'},{boolean:true},{integerToken:'9007199254740993'},{decimalToken:'9007199254740993.0000'},{binaryHex:'0001'}]);
if(nativeTypedKey.bytesHex!==expectedTypedKey.bytesHex)throw Error('Native typed subject semantic mismatch');
await typedConnection.commit();refuses(()=>typedBinding.encode(typedConnection));await typedConnection.release();await typedHost.close();cases.push('native five-family CoreLiteral JSON binds original semantic key');
const failedTransaction=createPgConnectionSource({...config,user:'principal_alice',max:1},{ordinaryPrincipal:'principal_alice',ordinarySubject:subject});
const failedConnection=await failedTransaction.source.acquire();await failedConnection.begin(transaction);
const priorObservation=failedTransaction.observeOrdinarySubject(failedConnection);
let nativeFailed=false;try{await failedConnection.execute({sql:'SELECT 1/0',parameters:[]});}catch{nativeFailed=true;}
if(!nativeFailed)throw Error('Native error not produced');refuses(()=>failedTransaction.observeOrdinarySubject(failedConnection));
await failedConnection.rollback();await failedConnection.begin(transaction);
if(failedTransaction.observeOrdinarySubject(failedConnection)===priorObservation)throw Error('Failed transaction observation reused');
await failedConnection.rollback();await failedConnection.release();await failedTransaction.close();cases.push('native failed transaction invalidates observation and fresh begin recaptures');
const pooled=createPgConnectionSource({...config,user:'principal_alice',max:1},{ordinaryPrincipal:'principal_alice'});
const first=await pooled.source.acquire();await first.begin(transaction);
await first.execute({sql:'SET ROLE principal_delegate',parameters:[]});await first.commit();await first.release();
const second=await pooled.source.acquire();await second.begin(transaction);
const identity=await second.execute({sql:'SELECT CURRENT_USER::pg_catalog.text AS actor',parameters:[]});
if(JSON.stringify(identity.rows)!==JSON.stringify([[{state:'text',text:'principal_alice'}]]))throw Error('Pooled role reset failed');
await second.rollback();await second.release();await pooled.close();cases.push('committed role change reset before pooled reuse');
for(const options of [{originalResponseTimeoutMs:0},{originalResponseTimeoutMs:60001},{ordinarySubject:subject},{ordinaryPrincipalObserver:observer},{ordinaryPrincipal:'principal_alice',ordinarySubject:{...subject,actorCarrier:'other'}}]){
 let refused=false;try{createPgConnectionSource(config,options as any);}catch{refused=true;}if(!refused)throw Error('Invalid construction admitted');
}
cases.push('five invalid constructions before acquisition');
console.log(JSON.stringify({cases,scope:'Original native caller/subject preflight and quarantine in isolated local fixture. Helpers explicitly fixture-trusted; no installed deployment, writer closure, authenticated application issuer or protected release.'}));
