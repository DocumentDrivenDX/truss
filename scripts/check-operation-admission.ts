/** Isolated native internal component; no normal installation marker or public writer. */
import {SQL} from 'bun';
import {loadUmfProducer} from '../packages/umf-bun/src/index';
const producerDirectory=process.env.TRUSS_UMF_PRODUCER;if(!producerDirectory)throw Error('Pinned original UMF producer required');
const producer=await loadUmfProducer(producerDirectory);
const url=process.env.TRUSS_OPERATION_TEST_URL;
if(!url||!url.startsWith('postgres://postgres@127.0.0.1:15434/'))throw Error('Dedicated local test endpoint required');
const sql=new SQL(url,{max:1});
const layout=await Bun.file('docs/helix/04-build/evidence/weft-integration-layout-0.13.owner-export.sql').text();
const body=await Bun.file('packages/postgresql/native/operation-admission.sql').text();
const checks:string[]=[];
const assert=(v:boolean,label:string)=>{if(!v)throw Error(label);checks.push(label)};
try{
 const version=await sql.unsafe('SHOW server_version');assert(version[0].server_version.startsWith('17.9'),'exact PostgreSQL17.9');
 await sql.unsafe(layout);await sql.unsafe(body);
 const observer=await Bun.file('packages/postgresql/native/operation-generation-observer.sql').text();await sql.unsafe(observer);
 const triggers=await sql.unsafe("SELECT count(*)::text AS n FROM pg_trigger WHERE tgname IN ('runtime_state_generation','runtime_node_generation','runtime_scalar_generation') AND tgenabled='A' AND NOT tgisinternal");assert(triggers[0].n==='3','three ALWAYS generation observers installed');
 await sql.unsafe('BEGIN');
 const xid=await sql.unsafe('SELECT pg_catalog.pg_current_xact_id()::text AS xid');
 const rows=await sql.unsafe("SELECT * FROM truss.runtime_admit_operation('mutation',decode('00ff','hex'),decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'))");
 assert(rows.length===1&&rows[0].writer_xid===xid[0].xid&&rows[0].ordinal==='0','actual native xid and ordinal');
 const context=JSON.parse(Buffer.from(rows[0].context_hex,'hex').toString('utf8'));
 assert(context.xid===xid[0].xid&&context.sessionUser==='postgres'&&context.actingUser==='postgres','original actor and native context captured');
 await sql.unsafe('SAVEPOINT duplicate');
 let code='';try{await sql.unsafe("SELECT * FROM truss.runtime_admit_operation('mutation',decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'))")}catch(e){code=(e as any).errno??(e as any).code}
 assert(code==='55000','second unfinished operation refused');await sql.unsafe('ROLLBACK TO SAVEPOINT duplicate');
 const stored=await sql.unsafe("SELECT encode(original_definition_bytes,'hex') AS bytes FROM truss.row_home_operation");
 assert(stored.length===1&&stored[0].bytes==='00ff','original binary artifact retained');
 await sql.unsafe('ROLLBACK');
 const after=await sql.unsafe('SELECT count(*)::text AS n FROM truss.row_home_operation');assert(after[0].n==='0','rollback removes operation custody');
 const grants=await sql.unsafe("SELECT count(*)::text AS n FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE n.nspname='truss' AND p.proname='runtime_admit_operation' AND a.grantee=0 AND a.privilege_type='EXECUTE'");assert(grants[0].n==='0','no public execute');
 const barrier=await Bun.file('packages/postgresql/native/operation-commit-barrier.sql').text();await sql.unsafe(barrier);
 const admit="SELECT * FROM truss.runtime_admit_operation('mutation',decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'))";
 await sql.unsafe('BEGIN');await sql.unsafe(admit);
 let commitCode='';try{await sql.unsafe('COMMIT')}catch(e){commitCode=(e as any).errno??(e as any).code}
 assert(commitCode==='55000','unfinalized operation cannot commit');
 const rejected=await sql.unsafe('SELECT count(*)::text AS n FROM truss.row_home_operation');assert(rejected[0].n==='0','failed commit removes custody');
 await sql.unsafe('CREATE TEMP TABLE caller_sentinel (value text)');await sql.unsafe('BEGIN');
 await sql.unsafe("INSERT INTO caller_sentinel VALUES ('earlier caller work')");await sql.unsafe('SAVEPOINT operation');await sql.unsafe(admit);await sql.unsafe('ROLLBACK TO SAVEPOINT operation');await sql.unsafe('COMMIT');
 const sentinel=await sql.unsafe('SELECT value FROM caller_sentinel');assert(sentinel.length===1&&sentinel[0].value==='earlier caller work','rolled back operation preserves earlier caller work');
 await sql.unsafe('BEGIN');await sql.unsafe(admit);
 await sql.unsafe("UPDATE truss.row_home_operation SET phase='application_finalized',readiness_generation=0,sealed_generation=0,application_generation=0,application_result_bytes=decode('01','hex')");
 let forgedCode='';try{await sql.unsafe('COMMIT')}catch(e){forgedCode=(e as any).errno??(e as any).code}
 assert(forgedCode==='55000','phase flags cannot bypass unavailable complete finalizer');
 const catalogStage=await Bun.file('packages/postgresql/native/catalog-document-stage.sql').text();await sql.unsafe(catalogStage);
 const documentBatch=await Bun.file('packages/postgresql/native/catalog-document-batch.sql').text();await sql.unsafe(documentBatch);
 const beforeHead=await sql.unsafe('SELECT rev::text AS rev FROM truss.schema_head');const beforeRevisions=await sql.unsafe('SELECT count(*)::text AS n FROM truss.schema_rev');
 await sql.unsafe('BEGIN');
 await sql.unsafe(admit.replace("'mutation'","'catalog-acceptance'"));
 const originalModel={umf:'0.7.0',id:'original-document',vocabularies:{},extensions:{},modules:[{id:'m',namespace:'m',elements:[
  ...['a','b','z'].map(id=>({id,kind:'record',extensions:{},...(id==='a'?{keys:[{id:'label-key',name:'label-key',fields:[{module:'m',element:'label'}],primary:true},...['aaa-secondary','a-secondary','z-secondary'].map(keyId=>({id:keyId,name:keyId,fields:[{module:'m',element:'zz-'+keyId}],primary:false}))]}:{}),members:id==='a'?[{module:'m',element:'label'},{module:'m',element:'caption'},...['aaa-secondary','a-secondary','z-secondary'].map(keyId=>({module:'m',element:'zz-'+keyId}))]:[]})),
  {id:'label',name:'label',kind:'field',extensions:{},scalarType:'string',nullability:'required',cardinality:'one'},
  {id:'caption',name:'caption',kind:'field',extensions:{},scalarType:'string',nullability:'absent-allowed',cardinality:'one'},...['aaa-secondary','a-secondary','z-secondary'].map(keyId=>({id:'zz-'+keyId,name:'zz-'+keyId,kind:'field',extensions:{},scalarType:'string',nullability:'required',cardinality:'one'}))],relationships:[{id:'a-z',name:'a-z',source:[{module:'m',element:'a'}],target:[{module:'m',element:'a',key:'label-key'}],sourceMultiplicity:{min:0,max:1},targetMultiplicity:{min:0,max:2},targetLifecycle:'independent',directed:true}]}]};
 const originalDocument=JSON.stringify(originalModel);const originalInspection=producer.inspect(originalDocument);
 assert(originalInspection.sourceValidation.valid&&originalInspection.targetValidation.valid,'actual original UMF source and transition validate');
 const recordCheck=producer.checkRecord(originalInspection.target,{module:'m',element:'a'},[{field:{module:'m',element:'label'},state:'present',value:{string:'雪🙂'}},...['aaa-secondary','a-secondary','z-secondary'].map(keyId=>({field:{module:'m',element:'zz-'+keyId},state:'present',value:{string:keyId}}))]);
 assert(recordCheck.validation.valid&&!recordCheck.validation.complete,'actual owner producer retains declared-key dataset incompleteness');
 const originalValidation={producerSource:producer.sourceRevision,producerBundleSha256:producer.bundleSha256,sourceValidation:originalInspection.sourceValidation,transition:originalInspection.transition,targetValidation:originalInspection.targetValidation,recordChecks:[recordCheck]};
 const secondText=JSON.stringify({...originalModel,id:'second-document'});const secondInspection=producer.inspect(secondText);
 assert(secondInspection.sourceValidation.valid,'second original document validated');
 const documents=[{documentId:'original-document',revision:'r1',umfVersion:'0.7.0',originalText:originalDocument,validation:originalValidation},{documentId:'second-document',revision:'r2',umfVersion:'0.7.0',originalText:secondText,validation:{sourceValidation:secondInspection.sourceValidation,transition:secondInspection.transition}}];
 await sql.unsafe('SAVEPOINT duplicate_documents');let duplicateDocumentCode='';
 try{await sql.unsafe("SELECT * FROM truss.runtime_stage_catalog_documents($1::text::jsonb,'{}'::jsonb)",[JSON.stringify([documents[0],documents[0]])])}catch(e){duplicateDocumentCode=(e as any).errno??(e as any).code}
 assert(duplicateDocumentCode==='22023','duplicate documents refuse before revision allocation');await sql.unsafe('ROLLBACK TO SAVEPOINT duplicate_documents');
 const beforeValid=await sql.unsafe('SELECT count(*)::text AS n FROM truss.schema_rev');assert(beforeValid[0].n===beforeRevisions[0].n,'rejected document set leaves original revision inventory');
 const staged=await sql.unsafe("SELECT * FROM truss.runtime_stage_catalog_documents($1::text::jsonb,'{}'::jsonb)",[JSON.stringify(documents)]);
 assert(staged[0].document_count==='2','complete ordered document set shares one native revision');
 const orderedDocuments=await sql.unsafe('SELECT doc_id,ord::text AS ord FROM truss.schema_doc ORDER BY ord');assert(orderedDocuments.length===2&&orderedDocuments[0].doc_id==='original-document'&&orderedDocuments[1].ord==='1','original document order retained');
 assert(staged.length===1&&staged[0].provisional_revision==='1','native provisional catalog revision allocated');
 const typeStage=await Bun.file('packages/postgresql/native/catalog-type-stage.sql').text();await sql.unsafe(typeStage);
 const candidates=[{documentId:'original-document',moduleId:'m',elementId:'z',lineageProfile:'test-original-bytes',lineageHex:'00ff'},{documentId:'original-document',moduleId:'m',elementId:'a',lineageProfile:'test-original-bytes',lineageHex:'01'}];
 const allocated=await sql.unsafe('SELECT * FROM truss.runtime_stage_new_types($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify(candidates)]);
 assert(allocated.length===2&&allocated[0].element_id==='a'&&allocated[0].type_id==='1'&&allocated[1].type_id==='2','native IDs follow original qualified byte order');
 await sql.unsafe('SAVEPOINT existing_type');let existingCode='';try{await sql.unsafe('SELECT * FROM truss.runtime_stage_new_types($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify(candidates)])}catch(e){existingCode=(e as any).errno??(e as any).code}assert(existingCode==='55000','existing identities refuse new allocation');await sql.unsafe('ROLLBACK TO SAVEPOINT existing_type');
 const propertyStage=await Bun.file('packages/postgresql/native/catalog-property-stage.sql').text();await sql.unsafe(propertyStage);
 const fields=originalModel.modules[0].elements.filter(field=>field.kind==='field').map(field=>({ownerTypeId:allocated[0].type_id,home:'json',field}));
 await sql.unsafe('SAVEPOINT duplicate_properties');let duplicatePropertyCode='';
 const duplicateNames=fields.map(value=>({...value,field:{...value.field,name:'same-name'}}));
 try{await sql.unsafe('SELECT * FROM truss.runtime_stage_new_properties($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify(duplicateNames)])}catch(e){duplicatePropertyCode=(e as any).errno??(e as any).code}
 assert(duplicatePropertyCode==='22023','duplicate field names refuse before property allocation');await sql.unsafe('ROLLBACK TO SAVEPOINT duplicate_properties');
 const rejectedProperties=await sql.unsafe('SELECT count(*)::text AS n FROM truss.prop_def');assert(rejectedProperties[0].n==='0','rejected property batch leaves no partial field');
 const survivingTypes=await sql.unsafe('SELECT count(*)::text AS n FROM truss.type_def');assert(survivingTypes[0].n==='2','earlier allocated types survive rejected field batch');
 const properties=await sql.unsafe('SELECT * FROM truss.runtime_stage_new_properties($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify(fields)]);assert(properties.length===5&&properties[0].field_id==='caption'&&properties[0].property_id==='1'&&properties[1].property_id==='2','native owner property IDs allocated in field order');
 const keyStage=await Bun.file('packages/postgresql/native/catalog-key-stage.sql').text();await sql.unsafe(keyStage);
 const labelProperty=properties.find((p:any)=>p.field_id==='label').property_id;
 const keyBatch=await Bun.file('packages/postgresql/native/catalog-key-batch.sql').text();await sql.unsafe(keyBatch);
 const originalOwner=originalModel.modules[0].elements.find(element=>element.id==='a')!;
 const originalKeys=originalOwner.keys!.map(key=>({ownerTypeId:allocated[0].type_id,keyId:key.id,primary:key.primary,
  propertyIds:key.fields.map(field=>{const match=properties.filter((p:any)=>p.field_id===field.element);if(field.module!=='m'||match.length!==1)throw Error('Original key field correspondence');return match[0].property_id})}));
 for(const [label,keyId,propertyId,primary] of [
  ['invented key declaration refuses','invented-key',labelProperty,false],
  ['changed original primary flag refuses','label-key',labelProperty,false],
  ['valid but wrong original key property refuses','aaa-secondary',labelProperty,false],
 ] as const){
  await sql.unsafe('SAVEPOINT key_source_mismatch');let refusal='';
  try{await sql.unsafe('SELECT truss.runtime_stage_new_key($1::int,$2::int,$3::text,ARRAY[$4::int],$5::boolean)',[staged[0].provisional_revision,allocated[0].type_id,keyId,propertyId,primary])}catch(e){refusal=(e as any).errno??(e as any).code}
  assert(refusal==='55000',label);await sql.unsafe('ROLLBACK TO SAVEPOINT key_source_mismatch');
 }
 const beforeKeys=await sql.unsafe('SELECT count(*)::text AS n FROM truss.key_def');assert(beforeKeys[0].n==='0','source mismatch cannot allocate a key declaration');
 const key=await sql.unsafe('SELECT * FROM truss.runtime_stage_new_keys($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify(originalKeys.filter(key=>key.primary))]);assert(key[0].key_number==='1','native owner-local key number allocated');
 const nativeKey=await sql.unsafe('SELECT prop_ids::text AS ids FROM truss.key_def');assert(nativeKey[0].ids==='{'+labelProperty+'}','original key component order and native property identity retained');
 await sql.unsafe('SAVEPOINT invalid_key_batch');let keyBatchCode='';
 try{await sql.unsafe('SELECT * FROM truss.runtime_stage_new_keys($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify([
  originalKeys.find(key=>key.keyId==='aaa-secondary')!,
  {...originalKeys[0],keyId:'zzz-invalid',primary:false,propertyIds:['2147483647']}
 ])])}catch(e){keyBatchCode=(e as any).errno??(e as any).code}
 assert(keyBatchCode==='55000','invalid later key refuses whole batch');await sql.unsafe('ROLLBACK TO SAVEPOINT invalid_key_batch');
 const partialKey=await sql.unsafe("SELECT count(*)::text AS n FROM truss.key_def WHERE key_id='aaa-secondary'");assert(partialKey[0].n==='0','earlier key in failed batch leaves no partial declaration');
 for(const [label,statement,expected] of [
  ['duplicate key identity refuses',"SELECT truss.runtime_stage_new_key($1::int,$2::int,'label-key',ARRAY[$3::int],true)",'55000'],
  ['duplicate key component refuses',"SELECT truss.runtime_stage_new_key($1::int,$2::int,'other-key',ARRAY[$3::int,$3::int],false)",'22023'],
  ['missing key component refuses',"SELECT truss.runtime_stage_new_key($1::int,$2::int,'other-key',ARRAY[2147483647],false)",'55000'],
  ['empty key refuses',"SELECT truss.runtime_stage_new_key($1::int,$2::int,'other-key',ARRAY[]::int[],false)",'22023'],
 ] as const){
  await sql.unsafe('SAVEPOINT invalid_key');let refusal='';
  try{await sql.unsafe(statement,[staged[0].provisional_revision,allocated[0].type_id,...(statement.includes('$3')?[labelProperty]:[])])}catch(e){refusal=(e as any).errno??(e as any).code}
  assert(refusal===expected,label);await sql.unsafe('ROLLBACK TO SAVEPOINT invalid_key');
 }
 const keyInventory=await sql.unsafe('SELECT count(*)::text AS n FROM truss.key_def');assert(keyInventory[0].n==='1','refused keys preserve earlier key declaration');
 const orderedKeys=await sql.unsafe('SELECT * FROM truss.runtime_stage_new_keys($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify([
  originalKeys.find(key=>key.keyId==='z-secondary')!,
  originalKeys.find(key=>key.keyId==='a-secondary')!
 ])]);assert(orderedKeys.length===2&&orderedKeys[0].key_id==='a-secondary'&&orderedKeys[0].key_number==='2'&&orderedKeys[1].key_number==='3','internal batch allocates key numbers in original identity byte order');
 const fieldState=await sql.unsafe("SELECT nullability FROM truss.prop_def WHERE element='caption'");assert(fieldState[0].nullability==='absent-allowed','original field availability retained');
 const relationshipStage=await Bun.file('packages/postgresql/native/catalog-relationship-stage.sql').text();await sql.unsafe(relationshipStage);
 const relationship=originalModel.modules[0].relationships[0];
 const stageRelationship="SELECT truss.runtime_stage_new_relationship($1::int,'original-document','m',$2::text::jsonb,ARRAY[$3::int],ARRAY[$4::int],'test-original-bytes',decode('aabb','hex')) AS id";
 const relationshipInputs=[staged[0].provisional_revision,JSON.stringify(relationship),allocated[0].type_id,allocated[0].type_id];
 await sql.unsafe('SAVEPOINT wrong_endpoint');let wrongEndpointCode='';
 try{await sql.unsafe(stageRelationship,[...relationshipInputs.slice(0,2),allocated[1].type_id,allocated[0].type_id])}catch(e){wrongEndpointCode=(e as any).errno??(e as any).code}
 assert(wrongEndpointCode==='55000','active but wrong original source endpoint refuses');await sql.unsafe('ROLLBACK TO SAVEPOINT wrong_endpoint');
 const beforeRelationship=await sql.unsafe('SELECT count(*)::text AS n FROM truss.rel_def');assert(beforeRelationship[0].n==='0','wrong endpoint leaves no partial relationship');
 await sql.unsafe('SAVEPOINT invented_relationship');let inventedRelationshipCode='';
 try{await sql.unsafe(stageRelationship,[staged[0].provisional_revision,JSON.stringify({...relationship,name:'invented'}),allocated[0].type_id,allocated[0].type_id])}catch(e){inventedRelationshipCode=(e as any).errno??(e as any).code}
 assert(inventedRelationshipCode==='55000','invented relationship definition refuses original source mismatch');await sql.unsafe('ROLLBACK TO SAVEPOINT invented_relationship');
 await sql.unsafe('SAVEPOINT wrong_target');let wrongTargetCode='';
 try{await sql.unsafe(stageRelationship,[...relationshipInputs.slice(0,3),allocated[1].type_id])}catch(e){wrongTargetCode=(e as any).errno??(e as any).code}
 assert(wrongTargetCode==='55000','active but wrong original target endpoint refuses');await sql.unsafe('ROLLBACK TO SAVEPOINT wrong_target');
 const stagedRelationship=await sql.unsafe(stageRelationship,relationshipInputs);assert(stagedRelationship[0].id==='1','native authored relationship ID allocated');
 const endpoints=await sql.unsafe('SELECT source_type::text AS source,target_type::text AS target FROM truss.rel_endpoint');assert(endpoints.length===1&&endpoints[0].source===allocated[0].type_id&&endpoints[0].target===allocated[0].type_id,'resolved original endpoint identities persisted');
 const relationshipCustody=await sql.unsafe("SELECT r.document_id,encode(l.original_identity_bytes,'hex') AS bytes,r.source_max::text AS source_max,r.target_max::text AS target_max FROM truss.rel_def r JOIN truss.relationship_lineage l USING(rel_type_id)");assert(relationshipCustody[0].document_id==='original-document'&&relationshipCustody[0].bytes==='aabb'&&relationshipCustody[0].source_max==='1'&&relationshipCustody[0].target_max==='2','declaring owner lineage and original multiplicities retained');
 await sql.unsafe('SAVEPOINT duplicate_relationship');let relationshipCode='';try{await sql.unsafe(stageRelationship,relationshipInputs)}catch(e){relationshipCode=(e as any).errno??(e as any).code}assert(relationshipCode==='55000','existing relationship refuses new allocation');await sql.unsafe('ROLLBACK TO SAVEPOINT duplicate_relationship');
 for(const [label,original,sourceId,expected] of [
  ['unarchived relationship declaration refuses',{...relationship,id:'other'},'2147483647','55000'],
  ['inverted relationship multiplicity refuses',{...relationship,id:'other',sourceMultiplicity:{min:2,max:1}},allocated[0].type_id,'22023'],
  ['null relationship maximum refuses',{...relationship,id:'other',sourceMultiplicity:{min:0,max:null}},allocated[0].type_id,'22023'],
  ['unsupported relationship member refuses',{...relationship,id:'other',inverse:'unknown'},allocated[0].type_id,'22023'],
 ] as const){
  await sql.unsafe('SAVEPOINT invalid_relationship');let refusal='';
  try{await sql.unsafe(stageRelationship.replace("'aabb'","'ccdd'"),[staged[0].provisional_revision,JSON.stringify(original),sourceId,allocated[0].type_id])}catch(e){refusal=(e as any).errno??(e as any).code}
  assert(refusal===expected,label);await sql.unsafe('ROLLBACK TO SAVEPOINT invalid_relationship');
 }
 const survivingRelationships=await sql.unsafe('SELECT count(*)::text AS n FROM truss.rel_def');assert(survivingRelationships[0].n==='1','refused relationships leave original declaration intact');
 await sql.unsafe('UPDATE truss.type_def SET retired_rev=since_rev');
 const next=await sql.unsafe('SELECT * FROM truss.runtime_stage_new_types($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify([{...candidates[0],elementId:'b'}])]);assert(next[0].type_id==='3','retired retained IDs remain high-water contributors');
 const originalLineage=await sql.unsafe("SELECT encode(lineage_bytes,'hex') AS bytes FROM truss.type_def WHERE element='z'");assert(originalLineage[0].bytes==='00ff','original lineage bytes retained');
 const retained=await sql.unsafe("SELECT document,validation::text AS validation FROM truss.schema_doc WHERE doc_id='original-document'");assert(JSON.parse(retained[0].validation).transition.source.umf==='0.7.0'&&JSON.parse(retained[0].validation).recordChecks[0].validation.complete===false,'original transition and checker result retained natively');assert(retained[0].document===originalDocument,'verbatim original source retained');
 const head=await sql.unsafe('SELECT rev::text AS rev FROM truss.schema_head');assert(JSON.stringify(head)===JSON.stringify(beforeHead),'document stage cannot publish catalog head');
 await sql.unsafe('ROLLBACK');
 const remaining=await sql.unsafe('SELECT count(*)::text AS n FROM truss.schema_rev');assert(remaining[0].n===beforeRevisions[0].n,'rollback removes staged revision and source');
 const rolledRelationships=await sql.unsafe('SELECT count(*)::text AS n FROM truss.relationship_lineage');assert(rolledRelationships[0].n==='0','rollback removes staged relationship lineage');
 const receipt={component:'native operation and owner-backed catalog staging',engine:'PostgreSQL17.9',umfSource:producer.sourceRevision,umfBundleSha256:producer.bundleSha256,checks,bodySha256:new Bun.CryptoHasher('sha256').update(body).digest('hex'),observerSha256:new Bun.CryptoHasher('sha256').update(observer).digest('hex'),barrierSha256:new Bun.CryptoHasher('sha256').update(barrier).digest('hex'),catalogStageSha256:new Bun.CryptoHasher('sha256').update(catalogStage).digest('hex'),documentBatchSha256:new Bun.CryptoHasher('sha256').update(documentBatch).digest('hex'),typeStageSha256:new Bun.CryptoHasher('sha256').update(typeStage).digest('hex'),propertyStageSha256:new Bun.CryptoHasher('sha256').update(propertyStage).digest('hex'),relationshipStageSha256:new Bun.CryptoHasher('sha256').update(relationshipStage).digest('hex'),keyBatchSha256:new Bun.CryptoHasher('sha256').update(keyBatch).digest('hex'),keyStageSha256:new Bun.CryptoHasher('sha256').update(keyStage).digest('hex'),qualification:'Actual xid/context/artifact bounds/single unfinished/rollback/private invocation component only. Protected issuer registration, canonical observers, finalization, deferred complete-cohort checks, installer security and public runtime remain unfinished.'};
 await Bun.write('docs/helix/04-build/evidence/runtime-operation-admission.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({checks:checks.length}));
}finally{await sql.close()}
