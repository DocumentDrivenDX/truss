/** Isolated native internal component; no normal installation marker or public writer. */
import {SQL} from 'bun';
import {loadUmfProducer,loadUmfValueProducer} from '../packages/umf-bun/src/index';
const producerDirectory=process.env.TRUSS_UMF_PRODUCER;if(!producerDirectory)throw Error('Pinned original UMF producer required');
const producer=await loadUmfProducer(producerDirectory);
const valueDirectory=process.env.TRUSS_UMF_VALUE_PRODUCER;if(!valueDirectory)throw Error('Original current-core value producer required');const valueProducer=await loadUmfValueProducer(valueDirectory);
const url=process.env.TRUSS_OPERATION_TEST_URL;
if(!url||!url.startsWith('postgres://postgres@127.0.0.1:15434/'))throw Error('Dedicated local test endpoint required');
const sql=new SQL(url,{max:1});
const peer=new SQL(url,{max:1});
const layoutPath='docs/helix/04-build/evidence/qualified-property-layout-0.15.owner-export.sql';
const layout=await Bun.file(layoutPath).text();
const body=await Bun.file('packages/postgresql/native/operation-admission.sql').text();
const checks:string[]=[];
const assert=(v:boolean,label:string)=>{if(!v)throw Error(label);checks.push(label)};
try{
 const version=await sql.unsafe('SHOW server_version');assert(version[0].server_version.startsWith('17.9'),'exact PostgreSQL17.9');
 await sql.unsafe(layout);await sql.unsafe(body);
 const observer=await Bun.file('packages/postgresql/native/operation-generation-observer.sql').text();await sql.unsafe(observer);
 const triggers=await sql.unsafe("SELECT count(*)::text AS n FROM pg_trigger WHERE tgname IN ('runtime_state_generation','runtime_node_generation','runtime_scalar_generation','runtime_key_generation','runtime_reservation_generation') AND tgenabled='A' AND NOT tgisinternal");assert(triggers[0].n==='5','five ALWAYS canonical generation observers installed');
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
 const headLock=await sql.unsafe("SELECT count(*)::text AS n FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND relation='truss.schema_head'::regclass AND mode='RowShareLock'");assert(headLock[0].n==='1','mutation admission obtains original head share before registry');
 const concurrentAdmit="SELECT * FROM truss.runtime_admit_operation('catalog-acceptance',decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'))";
 await peer.unsafe('BEGIN');await peer.unsafe("SET LOCAL lock_timeout='100ms'");let peerWait='';try{await peer.unsafe(concurrentAdmit)}catch(e){peerWait=(e as any).errno??(e as any).code}assert(peerWait==='55P03','catalog acceptance waits for original mutation head admission');await peer.unsafe('ROLLBACK');
 await sql.unsafe('ROLLBACK');
 const after=await sql.unsafe('SELECT count(*)::text AS n FROM truss.row_home_operation');assert(after[0].n==='0','rollback removes operation custody');
 await peer.unsafe('BEGIN');await peer.unsafe(concurrentAdmit);
 await sql.unsafe('BEGIN');await sql.unsafe("SET LOCAL lock_timeout='100ms'");let acceptanceWait='';try{await sql.unsafe(concurrentAdmit)}catch(e){acceptanceWait=(e as any).errno??(e as any).code}assert(acceptanceWait==='55P03','second catalog acceptance waits at original admission exclusion');await sql.unsafe('ROLLBACK');await peer.unsafe('ROLLBACK');
 await sql.unsafe('BEGIN');await sql.unsafe(concurrentAdmit.replace("'catalog-acceptance'","'mutation'"));await sql.unsafe('SAVEPOINT no_upgrade');let upgradeCode='';try{await sql.unsafe(concurrentAdmit)}catch(e){upgradeCode=(e as any).errno??(e as any).code}assert(upgradeCode==='55000','shared head admission cannot upgrade after earlier operation');await sql.unsafe('ROLLBACK TO SAVEPOINT no_upgrade');await sql.unsafe('ROLLBACK');
 await sql.unsafe('BEGIN');const releasedAdmission=await sql.unsafe(concurrentAdmit);assert(releasedAdmission.length===1,'catalog admission proceeds after original transactions roll back');await sql.unsafe('ROLLBACK');
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
 const foreignField={id:'foreign-note',name:'foreign-note',kind:'field',extensions:{},scalarType:'string',nullability:'required',cardinality:'one'};
 (originalModel.modules[0].elements.find(e=>e.id==='a') as any).members.push({module:'other',element:'foreign-note'});
 (originalModel.modules as any[]).push({id:'other',namespace:'other',elements:[foreignField]},{id:'shadow',namespace:'shadow',elements:[{...foreignField}]});
 const twinField={...foreignField,name:'twin-note'};
 (originalModel.modules as any[]).push({id:'twin',namespace:'twin',elements:[twinField]});
 (originalModel.modules[0].elements.find(e=>e.id==='a') as any).members.push({module:'twin',element:'foreign-note'});
 (originalModel.modules[0].elements.find(e=>e.id==='a') as any).keys.push({id:'module-twin-key',name:'module-twin-key',fields:[{module:'twin',element:'foreign-note'},{module:'other',element:'foreign-note'}],primary:false});
 const originalDocument=JSON.stringify(originalModel);const originalInspection=producer.inspect(originalDocument);
 assert(originalInspection.sourceValidation.valid&&originalInspection.targetValidation.valid,'actual original UMF source and transition validate');
 const recordCheck=producer.checkRecord(originalInspection.target,{module:'m',element:'a'},[...['other','twin'].map(module=>({field:{module,element:'foreign-note'},state:'present' as const,value:{string:module}})),{field:{module:'m',element:'label'},state:'present',value:{string:'雪🙂'}},...['aaa-secondary','a-secondary','z-secondary'].map(keyId=>({field:{module:'m',element:'zz-'+keyId},state:'present',value:{string:keyId}}))]);
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
 const stringEncoderBody=await Bun.file('packages/postgresql/native/canonical-string-bytes.sql').text();await sql.unsafe(stringEncoderBody);
 for(const [original,expected,label] of [
  ['', '2222','empty canonical string'],
  ['0008090a0c0d1f', '225c75303030305c75303030385c75303030395c75303030615c75303030635c75303030645c753030316622','canonical NUL and controls use lowercase six-byte escapes'],
  ['225cc3a965cc81e99baaf09f9982','225c225c5cc3a965cc81e99baaf09f998222','canonical quotes backslash exact Unicode without normalization'],
 ] as const){const encoded=await sql.unsafe("SELECT encode(truss.runtime_canonical_string_bytes(decode($1::text,'hex')),'hex') AS bytes",[original]);assert(encoded[0].bytes===expected,label)}
 for(const invalid of ['c080','eda080','f4908080','c200']){await sql.unsafe('SAVEPOINT invalid_string_utf8');let invalidUtf8='';try{await sql.unsafe("SELECT truss.runtime_canonical_string_bytes(decode($1::text,'hex'))",[invalid])}catch(e){invalidUtf8=(e as any).errno??(e as any).code}assert(invalidUtf8==='22021',`canonical string rejects invalid UTF8 ${invalid}`);await sql.unsafe('ROLLBACK TO SAVEPOINT invalid_string_utf8')}
 const lineageBody=await Bun.file('packages/postgresql/native/catalog-lineage-producer.sql').text();await sql.unsafe(lineageBody);
 for(const [file,category] of [['type','record'],['relationship','authored']] as const){
  const corpus=await Bun.file(`docs/helix/02-design/contracts/bindings/${file}-lineage-bytes-v0.1.vectors.json`).json();
  for(const vector of corpus.vectors){
   if(category==='authored'&&vector.identity.category!=='authored')continue;
   const parts=category==='record'?vector.identity:[vector.identity.relationship.document,vector.identity.relationship.module,vector.identity.relationship.element];
   const result=await sql.unsafe("SELECT encode(b,'hex') AS bytes,octet_length(b)::text AS length,encode(sha256(b),'hex') AS route FROM (SELECT truss.runtime_lineage_bytes($1::text,$2::text,$3::text,$4::text) b) q",[category,...parts]);
   assert(result[0].bytes===vector.storedBytesHex&&result[0].length===vector.storedBytesLength&&result[0].route===vector.routingSha256,`${file} lineage original vector ${vector.name}`);
  }
 }
 const quoted=await sql.unsafe('SELECT truss.runtime_lineage_quote($1::text) AS value',['\b\t\n\f\r'+String.fromCharCode(1,31)+'"\\雪🙂']);
 assert(quoted[0].value==='"\\u0008\\u0009\\u000a\\u000c\\u000d\\u0001\\u001f\\"\\\\雪🙂"','canonical identity controls quote backslash Unicode');
 const sourcedLineage=await sql.unsafe("SELECT truss.runtime_catalog_lineage(1,'record','original-document','m','a')=truss.runtime_lineage_bytes('record','original-document','m','a') AS record, truss.runtime_catalog_lineage(1,'authored','original-document','m','a-z')=truss.runtime_lineage_bytes('authored','original-document','m','a-z') AS relationship");
 assert(sourcedLineage[0].record&&sourcedLineage[0].relationship,'lineage resolves original archived Record and relationship');
 await sql.unsafe('SAVEPOINT missing_lineage');let lineageRefusal='';try{await sql.unsafe("SELECT truss.runtime_catalog_lineage(1,'record','original-document','m','label')")}catch(e){lineageRefusal=(e as any).errno??(e as any).code}assert(lineageRefusal==='55000','lineage refuses Field as original Record');await sql.unsafe('ROLLBACK TO SAVEPOINT missing_lineage');
 const typeMatchBody=await Bun.file('packages/postgresql/native/catalog-type-match.sql').text();await sql.unsafe(typeMatchBody);
 const typeStage=await Bun.file('packages/postgresql/native/catalog-type-stage.sql').text();await sql.unsafe(typeStage);
 const candidates=[{documentId:'original-document',moduleId:'m',elementId:'z'},{documentId:'original-document',moduleId:'m',elementId:'a'}];
 for(const [label,invalid] of [
  ['Field cannot be allocated as a Record type',{...candidates[0],elementId:'label'}],
  ['invented Record identity refuses',{...candidates[0],elementId:'invented'}],
 ] as const){
  await sql.unsafe('SAVEPOINT invalid_type_source');let refusal='';
  try{await sql.unsafe('SELECT * FROM truss.runtime_stage_new_types($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify([candidates[1],invalid])])}catch(e){refusal=(e as any).errno??(e as any).code}
  assert(refusal==='55000',label);await sql.unsafe('ROLLBACK TO SAVEPOINT invalid_type_source');
 }
 await sql.unsafe('SAVEPOINT forged_type_lineage');let forgedLineage='';try{await sql.unsafe('SELECT * FROM truss.runtime_stage_new_types($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify([{...candidates[0],lineageProfile:'forged',lineageHex:'00ff'}])])}catch(e){forgedLineage=(e as any).errno??(e as any).code}assert(forgedLineage==='22023','type staging rejects caller-supplied lineage substitution');await sql.unsafe('ROLLBACK TO SAVEPOINT forged_type_lineage');
 const beforeTypes=await sql.unsafe('SELECT count(*)::text AS n FROM truss.type_def');assert(beforeTypes[0].n==='0','type source mismatch leaves no partial Record allocation');
 const allocated=await sql.unsafe('SELECT * FROM truss.runtime_stage_new_types($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify(candidates)]);
 assert(allocated.length===2&&allocated[0].element_id==='a'&&allocated[0].type_id==='1'&&allocated[1].type_id==='2','native IDs follow original qualified byte order');
 const matchRecord="SELECT * FROM truss.runtime_match_record_identity(1,'original-document','m',$1::text)";
 const activeMatch=await sql.unsafe(matchRecord,['a']);assert(activeMatch[0].match_state==='active'&&activeMatch[0].storage_id===allocated[0].type_id&&activeMatch[0].creation_revision==='1','active lineage match preserves native ID and creation');
 const newMatch=await sql.unsafe(matchRecord,['b']);assert(newMatch[0].match_state==='new'&&newMatch[0].storage_id===null,'genuinely new original Record has no assigned matching ID');
 await sql.unsafe('SAVEPOINT retired_match');await sql.unsafe("UPDATE truss.type_def SET retired_rev=1 WHERE element='a'");const retiredMatch=await sql.unsafe(matchRecord,['a']);assert(retiredMatch[0].match_state==='retired'&&retiredMatch[0].storage_id===allocated[0].type_id&&retiredMatch[0].retirement_revision==='1','retired lineage match preserves original identity without reactivation');const stillRetired=await sql.unsafe("SELECT retired_rev::text AS rev FROM truss.type_def WHERE element='a'");assert(stillRetired[0].rev==='1','identity matching cannot clear retirement');await sql.unsafe('SAVEPOINT retired_allocation');let retiredAllocation='';try{await sql.unsafe('SELECT * FROM truss.runtime_stage_new_types(1,$1::text::jsonb)',[JSON.stringify([{...candidates[0],elementId:'b'},candidates[1]])])}catch(e){retiredAllocation=(e as any).errno??(e as any).code}assert(retiredAllocation==='55000','mixed new and retired batch cannot allocate a substitute ID');await sql.unsafe('ROLLBACK TO SAVEPOINT retired_allocation');const noPartialRetired=await sql.unsafe("SELECT count(*)::text AS n FROM truss.type_def WHERE element='b'");assert(noPartialRetired[0].n==='0','retired match refusal leaves earlier new candidate unallocated');await sql.unsafe('ROLLBACK TO SAVEPOINT retired_match');
 await sql.unsafe('SAVEPOINT corrupt_match');await sql.unsafe("UPDATE truss.type_def SET lineage_bytes=decode('00ff','hex') WHERE element='a'");let corruptMatch='';try{await sql.unsafe(matchRecord,['a'])}catch(e){corruptMatch=(e as any).errno??(e as any).code}assert(corruptMatch==='55000','matching refuses qualified tuple with substituted original bytes');await sql.unsafe('ROLLBACK TO SAVEPOINT corrupt_match');
 await sql.unsafe('SAVEPOINT existing_type');let existingCode='';try{await sql.unsafe('SELECT * FROM truss.runtime_stage_new_types($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify(candidates)])}catch(e){existingCode=(e as any).errno??(e as any).code}assert(existingCode==='55000','existing identities refuse new allocation');await sql.unsafe('ROLLBACK TO SAVEPOINT existing_type');
 const propertyMatchBody=await Bun.file('packages/postgresql/native/catalog-property-match.sql').text();await sql.unsafe(propertyMatchBody);
 const propertyStage=await Bun.file('packages/postgresql/native/catalog-property-stage.sql').text();await sql.unsafe(propertyStage);
 const fields=originalModel.modules[0].elements.filter(field=>field.kind==='field').map(field=>({ownerTypeId:allocated[0].type_id,fieldModule:'m',home:field.id==='caption'?'row':'json',field}));
 await sql.unsafe('SAVEPOINT cross_module_property');const crossModuleStaged=await sql.unsafe('SELECT * FROM truss.runtime_stage_new_properties(1,$1::text::jsonb)',[JSON.stringify([fields[0],{ownerTypeId:allocated[0].type_id,fieldModule:'other',home:'json',field:foreignField}])]);const crossModuleStored=await sql.unsafe("SELECT declaration_module,element,definition_document_id FROM truss.prop_def WHERE element='foreign-note'");assert(crossModuleStaged.length===2&&crossModuleStored[0].declaration_module==='other'&&crossModuleStored[0].element==='foreign-note'&&crossModuleStored[0].definition_document_id==='original-document','original cross-module Field declaration identity persists independently');await sql.unsafe('ROLLBACK TO SAVEPOINT cross_module_property');const crossModuleRows=await sql.unsafe('SELECT count(*)::text AS n FROM truss.prop_def');assert(crossModuleRows[0].n==='0','cross-module property batch rolls back completely');
 await sql.unsafe('SAVEPOINT qualified_twins');const twinProperties=await sql.unsafe('SELECT * FROM truss.runtime_stage_new_properties(1,$1::text::jsonb)',[JSON.stringify([{ownerTypeId:allocated[0].type_id,fieldModule:'twin',home:'json',field:twinField},{ownerTypeId:allocated[0].type_id,fieldModule:'other',home:'json',field:foreignField}])]);assert(twinProperties.length===2&&twinProperties[0].field_module==='other'&&twinProperties[1].field_module==='twin'&&twinProperties[0].field_id===twinProperties[1].field_id&&twinProperties[0].property_id!==twinProperties[1].property_id,'equal Field IDs on one owner retain distinct declaring-module identities and IDs');await sql.unsafe('ROLLBACK TO SAVEPOINT qualified_twins');
 await sql.unsafe('SAVEPOINT wrong_declaration_module');let wrongDeclarationModule='';try{await sql.unsafe('SELECT * FROM truss.runtime_stage_new_properties(1,$1::text::jsonb)',[JSON.stringify([{ownerTypeId:allocated[0].type_id,fieldModule:'shadow',home:'json',field:foreignField}])])}catch(e){wrongDeclarationModule=(e as any).errno??(e as any).code}assert(wrongDeclarationModule==='55000','equal original Field bytes in another module cannot substitute owner membership');await sql.unsafe('ROLLBACK TO SAVEPOINT wrong_declaration_module');
 await sql.unsafe('SAVEPOINT duplicate_properties');let duplicatePropertyCode='';
 const duplicateNames=fields.map(value=>({...value,field:{...value.field,name:'same-name'}}));
 try{await sql.unsafe('SELECT * FROM truss.runtime_stage_new_properties($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify(duplicateNames)])}catch(e){duplicatePropertyCode=(e as any).errno??(e as any).code}
 assert(duplicatePropertyCode==='22023','duplicate field names refuse before property allocation');await sql.unsafe('ROLLBACK TO SAVEPOINT duplicate_properties');
 const rejectedProperties=await sql.unsafe('SELECT count(*)::text AS n FROM truss.prop_def');assert(rejectedProperties[0].n==='0','rejected property batch leaves no partial field');
 const survivingTypes=await sql.unsafe('SELECT count(*)::text AS n FROM truss.type_def');assert(survivingTypes[0].n==='2','earlier allocated types survive rejected field batch');
 for(const [label,invalid] of [
  ['changed original Field semantics refuse',{...fields[1],field:{...fields[1].field,scalarType:'boolean'}}],
  ['Field bound to wrong original Record refuses',{...fields[1],ownerTypeId:allocated[1].type_id}],
  ['invented Field declaration refuses',{...fields[1],field:{...fields[1].field,id:'invented',name:'invented'}}],
 ] as const){
  await sql.unsafe('SAVEPOINT invalid_field_source');let refusal='';
  try{await sql.unsafe('SELECT * FROM truss.runtime_stage_new_properties($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify([fields[0],invalid])])}catch(e){refusal=(e as any).errno??(e as any).code}
  assert(refusal==='55000',label);await sql.unsafe('ROLLBACK TO SAVEPOINT invalid_field_source');
 }
 const beforeFields=await sql.unsafe('SELECT count(*)::text AS n FROM truss.prop_def');assert(beforeFields[0].n==='0','field source mismatch leaves no partial property allocation');
 const properties=await sql.unsafe('SELECT * FROM truss.runtime_stage_new_properties($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify(fields)]);assert(properties.length===5&&properties[0].field_id==='caption'&&properties[0].property_id==='1'&&properties[1].property_id==='2','native owner property IDs allocated in field order');
 const matchProperty="SELECT * FROM truss.runtime_match_property_identity(1,$1::int,$2::text,$3::text)";
 const activeProperty=await sql.unsafe(matchProperty,[allocated[0].type_id,'m','label']);assert(activeProperty[0].match_state==='active'&&activeProperty[0].storage_id===properties.find((p:any)=>p.field_id==='label').property_id,'retained property matches original owner and declaring Field');
 const unmatchedField=await sql.unsafe(matchProperty,[allocated[0].type_id,'other','foreign-note']);assert(unmatchedField[0].match_state==='new'&&unmatchedField[0].storage_id===null,'new cross-module Field identity is not allocated by matcher');
 await sql.unsafe('SAVEPOINT retired_property_match');await sql.unsafe("UPDATE truss.prop_def SET retired_rev=1 WHERE element='label'");const retiredProperty=await sql.unsafe(matchProperty,[allocated[0].type_id,'m','label']);assert(retiredProperty[0].match_state==='retired'&&retiredProperty[0].storage_id===activeProperty[0].storage_id&&retiredProperty[0].retirement_revision==='1','retired property match preserves original ID and retirement');await sql.unsafe('SAVEPOINT retired_property_allocation');let retiredPropertyAllocation='';try{await sql.unsafe('SELECT * FROM truss.runtime_stage_new_properties(1,$1::text::jsonb)',[JSON.stringify([{ownerTypeId:allocated[0].type_id,fieldModule:'other',home:'json',field:foreignField},fields.find(f=>f.field.id==='label')])])}catch(e){retiredPropertyAllocation=(e as any).errno??(e as any).code}assert(retiredPropertyAllocation==='55000','mixed new and retired properties refuse substitute allocation');await sql.unsafe('ROLLBACK TO SAVEPOINT retired_property_allocation');const absentNewProperty=await sql.unsafe("SELECT count(*)::text AS n FROM truss.prop_def WHERE declaration_module='other'");assert(absentNewProperty[0].n==='0','retired property refusal leaves new candidate unallocated');await sql.unsafe('ROLLBACK TO SAVEPOINT retired_property_match');
 await sql.unsafe('SAVEPOINT wrong_property_member');let wrongPropertyMember='';try{await sql.unsafe(matchProperty,[allocated[0].type_id,'shadow','foreign-note'])}catch(e){wrongPropertyMember=(e as any).errno??(e as any).code}assert(wrongPropertyMember==='55000','property matching refuses equal unbound Field in another module');await sql.unsafe('ROLLBACK TO SAVEPOINT wrong_property_member');
 await sql.unsafe('SAVEPOINT orphan_original_property');const orphanModel=structuredClone(originalModel);const orphanRecord=orphanModel.modules[0].elements.find(e=>e.id==='a') as any;orphanRecord.members=orphanRecord.members.filter((m:any)=>m.element!=='label');orphanRecord.keys=orphanRecord.keys.filter((k:any)=>k.id!=='label-key');orphanModel.modules[0].relationships=[];const orphanText=JSON.stringify(orphanModel);const orphanInspection=producer.inspect(orphanText);assert(orphanInspection.sourceValidation.valid&&orphanInspection.targetValidation.valid,'original UMF admits separately declared Field outside Record membership');const orphanRevision=await sql.unsafe("SELECT * FROM truss.runtime_stage_catalog_documents($1::text::jsonb,'{}'::jsonb)",[JSON.stringify([{documentId:'original-document',revision:'orphan-fixture',umfVersion:'0.7.0',originalText:orphanText,validation:{sourceValidation:orphanInspection.sourceValidation,transition:orphanInspection.transition}}])]);await sql.unsafe("UPDATE truss.prop_def SET definition_rev=$1::int,definition_doc_ord=0 WHERE element='label'",[orphanRevision[0].provisional_revision]);await sql.unsafe('SAVEPOINT orphan_property_match');let orphanPropertyMatch='';try{await sql.unsafe(matchProperty,[allocated[0].type_id,'m','label'])}catch(e){orphanPropertyMatch=(e as any).errno??(e as any).code}assert(orphanPropertyMatch==='55000','retained Field declaration cannot replace original owning Record membership');await sql.unsafe('ROLLBACK TO SAVEPOINT orphan_original_property');
 const keyMatchBody=await Bun.file('packages/postgresql/native/catalog-key-match.sql').text();await sql.unsafe(keyMatchBody);
 const keyStage=await Bun.file('packages/postgresql/native/catalog-key-stage.sql').text();await sql.unsafe(keyStage);
 const labelProperty=properties.find((p:any)=>p.field_id==='label').property_id;
 const keyBatch=await Bun.file('packages/postgresql/native/catalog-key-batch.sql').text();await sql.unsafe(keyBatch);
 const originalOwner=originalModel.modules[0].elements.find(element=>element.id==='a')!;
 const originalKeys=originalOwner.keys!.filter(key=>key.id!=='module-twin-key').map(key=>({ownerTypeId:allocated[0].type_id,keyId:key.id,primary:key.primary,
  propertyIds:key.fields.map(field=>{const match=properties.filter((p:any)=>p.field_id===field.element);if(field.module!=='m'||match.length!==1)throw Error('Original key field correspondence');return match[0].property_id})}));
 await sql.unsafe('SAVEPOINT cross_module_key');const keyFields=await sql.unsafe('SELECT * FROM truss.runtime_stage_new_properties(1,$1::text::jsonb)',[JSON.stringify([{ownerTypeId:allocated[0].type_id,fieldModule:'twin',home:'json',field:twinField},{ownerTypeId:allocated[0].type_id,fieldModule:'other',home:'json',field:foreignField}])]);const otherProperty=keyFields.find((p:any)=>p.field_module==='other').property_id;const twinProperty=keyFields.find((p:any)=>p.field_module==='twin').property_id;
 await sql.unsafe('SAVEPOINT swapped_module_key');let swappedModuleKey='';try{await sql.unsafe("SELECT truss.runtime_stage_new_key(1,$1::int,'module-twin-key',ARRAY[$2::int,$3::int],false)",[allocated[0].type_id,otherProperty,twinProperty])}catch(e){swappedModuleKey=(e as any).errno??(e as any).code}assert(swappedModuleKey==='55000','same Field IDs cannot conceal swapped key declaring modules');await sql.unsafe('ROLLBACK TO SAVEPOINT swapped_module_key');
 const moduleKey=await sql.unsafe("SELECT truss.runtime_stage_new_key(1,$1::int,'module-twin-key',ARRAY[$2::int,$3::int],false) AS number",[allocated[0].type_id,twinProperty,otherProperty]);const moduleKeyStored=await sql.unsafe("SELECT prop_ids::text AS ids FROM truss.key_def WHERE key_id='module-twin-key'");assert(moduleKey[0].number==='1'&&moduleKeyStored[0].ids==='{'+twinProperty+','+otherProperty+'}','authored cross-module key retains exact original ordered qualified components');await sql.unsafe('ROLLBACK TO SAVEPOINT cross_module_key');
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
 const matchKey="SELECT * FROM truss.runtime_match_key_identity(1,$1::int,$2::text)";const activeKey=await sql.unsafe(matchKey,[allocated[0].type_id,'label-key']);assert(activeKey[0].match_state==='active'&&activeKey[0].owner_type_id===allocated[0].type_id&&activeKey[0].key_number==='1'&&activeKey[0].creation_revision==='1','retained key matching preserves original owner-local tuple');
 const newKey=await sql.unsafe(matchKey,[allocated[0].type_id,'module-twin-key']);assert(newKey[0].match_state==='new'&&newKey[0].key_number===null,'new authored key has no allocated local number');
 await sql.unsafe('SAVEPOINT retired_key_match');await sql.unsafe("UPDATE truss.key_def SET retired_rev=1 WHERE key_id='label-key'");const retiredKey=await sql.unsafe(matchKey,[allocated[0].type_id,'label-key']);assert(retiredKey[0].match_state==='retired'&&retiredKey[0].owner_type_id===allocated[0].type_id&&retiredKey[0].key_number==='1'&&retiredKey[0].retirement_revision==='1','retired key matching preserves original tuple without clearance');await sql.unsafe('ROLLBACK TO SAVEPOINT retired_key_match');
 await sql.unsafe('SAVEPOINT wrong_key_owner');let wrongKeyOwner='';try{await sql.unsafe(matchKey,[allocated[1].type_id,'label-key'])}catch(e){wrongKeyOwner=(e as any).errno??(e as any).code}assert(wrongKeyOwner==='55000','key matching cannot borrow another Record declaration');await sql.unsafe('ROLLBACK TO SAVEPOINT wrong_key_owner');
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
 const historyTypes=await sql.unsafe("SELECT a.attname,t.typname FROM pg_attribute a JOIN pg_type t ON t.oid=a.atttypid WHERE a.attrelid='truss.key_lifecycle_history'::regclass AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum");
 assert(historyTypes.map((r:any)=>r.typname).join(',')==='int4,int4,int4,int2,text,int4,int4,bytea,bytea','key history exact native column domains');
 const historyInsert="INSERT INTO truss.key_lifecycle_history(rev,seq,type_id,key_num,transition_kind,before_retired_rev,after_retired_rev,before_definition_bytes,after_definition_bytes) VALUES (1,0,$1::int,1,$2::text,$3::int,$4::int,decode('01','hex'),decode('02','hex'))";
 for(const [tag,before,after,owner,expected,label] of [
  ['retirement',null,1,allocated[0].type_id,'','retirement history explicit interval'],
  ['reactivation',0,null,allocated[0].type_id,'','reactivation history earlier interval'],
  ['definition_change',null,null,allocated[0].type_id,'','active edit history explicit null state'],
  ['retirement',null,null,allocated[0].type_id,'23514','retirement history rejects ambiguous null result'],
  ['reactivation',1,null,allocated[0].type_id,'23514','reactivation history rejects same-revision retirement'],
  ['reactivation',null,null,allocated[0].type_id,'23514','reactivation history rejects missing prior interval'],
  ['definition_change',0,null,allocated[0].type_id,'23514','definition edit cannot masquerade as reactivation'],
  ['retirement',null,1,allocated[1].type_id,'23503','key history requires exact owning key tuple'],
 ] as const){
  await sql.unsafe('SAVEPOINT history_shape');let historyCode='';try{await sql.unsafe(historyInsert,[owner,tag,before,after])}catch(e){historyCode=(e as any).errno??(e as any).code}assert(historyCode===expected,label);await sql.unsafe('ROLLBACK TO SAVEPOINT history_shape');
 }
 const historyAfter=await sql.unsafe('SELECT count(*)::text AS n FROM truss.key_lifecycle_history');assert(historyAfter[0].n==='0','component history probes retain no fabricated lifecycle rows');
 const relationshipMatchBody=await Bun.file('packages/postgresql/native/catalog-relationship-match.sql').text();await sql.unsafe(relationshipMatchBody);
 const relationshipStage=await Bun.file('packages/postgresql/native/catalog-relationship-stage.sql').text();await sql.unsafe(relationshipStage);
 const relationship=originalModel.modules[0].relationships[0];
 const stageRelationship="SELECT truss.runtime_stage_new_relationship($1::int,'original-document','m',$2::text::jsonb,ARRAY[$3::int],ARRAY[$4::int]) AS id";
 const legacyRelationshipSignature=await sql.unsafe("SELECT to_regprocedure('truss.runtime_stage_new_relationship(integer,text,text,jsonb,integer[],integer[],text,bytea)') IS NULL AS absent");assert(legacyRelationshipSignature[0].absent,'relationship staging exposes no caller lineage signature');
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
 const matchRelationship="SELECT * FROM truss.runtime_match_relationship_identity(1,'original-document','m','a-z')";
 const newRelationship=await sql.unsafe(matchRelationship);assert(newRelationship[0].match_state==='new'&&newRelationship[0].storage_id===null,'new original relationship has no matching allocated ID');
 const stagedRelationship=await sql.unsafe(stageRelationship,relationshipInputs);assert(stagedRelationship[0].id==='1','native authored relationship ID allocated');
 const endpoints=await sql.unsafe('SELECT source_type::text AS source,target_type::text AS target FROM truss.rel_endpoint');assert(endpoints.length===1&&endpoints[0].source===allocated[0].type_id&&endpoints[0].target===allocated[0].type_id,'resolved original endpoint identities persisted');
 const relationshipCustody=await sql.unsafe("SELECT r.document_id,l.identity_profile='truss-relationship-lineage-bytes/0.1.0' AND l.original_identity_bytes=truss.runtime_catalog_lineage(r.definition_rev,'authored',r.document_id,r.module,r.rel_id) AS original,r.source_max::text AS source_max,r.target_max::text AS target_max FROM truss.rel_def r JOIN truss.relationship_lineage l USING(rel_type_id)");assert(relationshipCustody[0].document_id==='original-document'&&relationshipCustody[0].original&&relationshipCustody[0].source_max==='1'&&relationshipCustody[0].target_max==='2','declaring owner lineage and original multiplicities retained');
 const activeRelationship=await sql.unsafe(matchRelationship);assert(activeRelationship[0].match_state==='active'&&activeRelationship[0].storage_id===stagedRelationship[0].id&&activeRelationship[0].creation_revision==='1','active relationship identity preserves original ID and creation');
 await sql.unsafe('SAVEPOINT retired_relationship_match');await sql.unsafe('UPDATE truss.rel_def SET retired_rev=1');const retiredRelationship=await sql.unsafe(matchRelationship);assert(retiredRelationship[0].match_state==='retired'&&retiredRelationship[0].storage_id===stagedRelationship[0].id&&retiredRelationship[0].retirement_revision==='1','retired relationship match retains original ID without clearance');await sql.unsafe('ROLLBACK TO SAVEPOINT retired_relationship_match');
 await sql.unsafe('SAVEPOINT corrupt_relationship_match');await sql.unsafe("UPDATE truss.relationship_lineage SET original_identity_bytes=decode('00ff','hex')");let corruptRelationship='';try{await sql.unsafe(matchRelationship)}catch(e){corruptRelationship=(e as any).errno??(e as any).code}assert(corruptRelationship==='55000','relationship matching refuses substituted full identity bytes');await sql.unsafe('ROLLBACK TO SAVEPOINT corrupt_relationship_match');
 await sql.unsafe('SAVEPOINT duplicate_relationship');let relationshipCode='';try{await sql.unsafe(stageRelationship,relationshipInputs)}catch(e){relationshipCode=(e as any).errno??(e as any).code}assert(relationshipCode==='55000','existing relationship refuses new allocation');await sql.unsafe('ROLLBACK TO SAVEPOINT duplicate_relationship');
 for(const [label,original,sourceId,expected] of [
  ['unarchived relationship declaration refuses',{...relationship,id:'other'},'2147483647','55000'],
  ['inverted relationship multiplicity refuses',{...relationship,id:'other',sourceMultiplicity:{min:2,max:1}},allocated[0].type_id,'22023'],
  ['null relationship maximum refuses',{...relationship,id:'other',sourceMultiplicity:{min:0,max:null}},allocated[0].type_id,'22023'],
  ['unsupported relationship member refuses',{...relationship,id:'other',inverse:'unknown'},allocated[0].type_id,'22023'],
 ] as const){
  await sql.unsafe('SAVEPOINT invalid_relationship');let refusal='';
  try{await sql.unsafe(stageRelationship,[staged[0].provisional_revision,JSON.stringify(original),sourceId,allocated[0].type_id])}catch(e){refusal=(e as any).errno??(e as any).code}
  assert(refusal===expected,label);await sql.unsafe('ROLLBACK TO SAVEPOINT invalid_relationship');
 }
 const survivingRelationships=await sql.unsafe('SELECT count(*)::text AS n FROM truss.rel_def');assert(survivingRelationships[0].n==='1','refused relationships leave original declaration intact');
 // Actual canonical event dispatch, still under a rollback-only component operation.
 const objectProps=Object.fromEntries(properties.filter((p:any)=>p.field_id!=='caption').map((p:any)=>[p.property_id,p.field_id==='label'?'雪🙂':p.field_id.slice(3)]));
 for(const [table,statement,parameters] of [
  ['type_def',matchRecord,['a']],
  ['prop_def',matchProperty,[allocated[0].type_id,'m','label']],
  ['key_def',matchKey,[allocated[0].type_id,'label-key']],
  ['rel_def',matchRelationship,[]],
 ] as const){
  await sql.unsafe('SAVEPOINT unavailable_source_profile');await sql.unsafe(`UPDATE truss.${table} SET definition_source_kind='accepted_binding',definition_rev=NULL,definition_doc_ord=NULL,definition_document_id=NULL,binding_source_rev=1,binding_source_pointer='component-binding-fixture',binding_source_bytes=decode('01','hex')`);let unavailableProfile='';try{await sql.unsafe(statement,[...parameters])}catch(e){unavailableProfile=(e as any).errno??(e as any).code}assert(unavailableProfile==='0A000',`${table} matching explicitly refuses unregistered binding source interpretation`);await sql.unsafe('ROLLBACK TO SAVEPOINT unavailable_source_profile');
 }
 const object=await sql.unsafe('INSERT INTO truss.object(type_id,props,rev) VALUES($1::int,$2::text::jsonb,$3::int) RETURNING id::text AS id',[allocated[0].type_id,JSON.stringify(objectProps),staged[0].provisional_revision]);
 const nodeIds=await sql.unsafe("SELECT nextval('truss.row_home_id_seq')::text AS state_id,nextval('truss.row_home_id_seq')::text AS node_id");
 const captionProperty=properties.find((p:any)=>p.field_id==='caption').property_id;
 await sql.unsafe("INSERT INTO truss.row_home_state(state_id,owner_kind,object_id,object_type_id,property_owner_type_id,property_id,root_node_id,definition_bytes,home_profile_bytes,value_profile_bytes,source_bytes) VALUES($1::bigint,'object',$2::bigint,$3::int,$3::int,$4::int,$5::bigint,decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'))",[nodeIds[0].state_id,object[0].id,allocated[0].type_id,captionProperty,nodeIds[0].node_id]);
 await sql.unsafe("INSERT INTO truss.row_home_node(state_id,node_id,slot_kind,value_kind,definition_bytes,source_bytes) VALUES($1::bigint,$2::bigint,'root','scalar',decode('01','hex'),decode('04','hex'))",[nodeIds[0].state_id,nodeIds[0].node_id]);
 await sql.unsafe("INSERT INTO truss.row_home_scalar(state_id,node_id,scalar_kind,text_value,codec_definition_bytes,original_source_bytes) VALUES($1::bigint,$2::bigint,'string','first',decode('05','hex'),decode('04','hex'))",[nodeIds[0].state_id,nodeIds[0].node_id]);
 const generation=()=>sql.unsafe('SELECT effect_generation::text AS generation,phase,readiness_generation::text AS readiness FROM truss.row_home_operation');
 assert((await generation())[0].generation==='3','actual state node and scalar inserts each advance operation generation');
 await sql.unsafe("UPDATE truss.row_home_operation SET phase='effects_ready',readiness_generation=effect_generation");
 await sql.unsafe("UPDATE truss.row_home_scalar SET text_value='second'");
 const invalidated=await generation();assert(invalidated[0].generation==='4'&&invalidated[0].phase==='admitted'&&invalidated[0].readiness===null,'actual scalar update invalidates prior readiness generation');
 await sql.unsafe('SAVEPOINT canonical_rollback');await sql.unsafe("UPDATE truss.row_home_scalar SET text_value='rolled-back'");assert((await generation())[0].generation==='5','savepoint-local canonical update advances generation');await sql.unsafe('ROLLBACK TO SAVEPOINT canonical_rollback');
 const restoredScalar=await sql.unsafe('SELECT text_value FROM truss.row_home_scalar');assert((await generation())[0].generation==='4'&&restoredScalar[0].text_value==='second','savepoint rollback restores original generation and scalar together');
 await sql.unsafe('SAVEPOINT generation_overflow');await sql.unsafe('UPDATE truss.row_home_operation SET effect_generation=9223372036854775807');let generationOverflow='';
 try{await sql.unsafe("UPDATE truss.row_home_scalar SET text_value='overflow'")}catch(e){generationOverflow=(e as any).errno??(e as any).code}
 assert(generationOverflow==='54000','actual canonical event refuses generation exhaustion');await sql.unsafe('ROLLBACK TO SAVEPOINT generation_overflow');
 await sql.unsafe('SAVEPOINT missing_operation');await sql.unsafe('DELETE FROM truss.row_home_operation');let missingOperation='';
 try{await sql.unsafe("UPDATE truss.row_home_scalar SET text_value='unattributed'")}catch(e){missingOperation=(e as any).errno??(e as any).code}
 assert(missingOperation==='55000','canonical update without original operation refuses');await sql.unsafe('ROLLBACK TO SAVEPOINT missing_operation');
 const prestateBody=await Bun.file('packages/postgresql/native/row-prestate-capture.sql').text();await sql.unsafe(prestateBody);
 const nativePrestate=await sql.unsafe("SELECT encode(truss.runtime_capture_row_prestate('object',$1::bigint,$2::int,$2::int,$3::int),'hex') AS bytes",[object[0].id,allocated[0].type_id,captionProperty]);
 const prestateFacts=await sql.unsafe("SELECT convert_from(decode($1::text,'hex'),'UTF8')::jsonb #>> '{state,state_id}' AS state_id,convert_from(decode($1::text,'hex'),'UTF8')::jsonb #>> '{scalars,0,text_value}' AS value",[nativePrestate[0].bytes]);
 assert(prestateFacts[0].state_id===nodeIds[0].state_id&&prestateFacts[0].value==='second','native prestate retains actual state identity and scalar without host numeric decoding');
 await sql.unsafe('SAVEPOINT wrong_prestate_owner');let wrongPrestateOwner='';
 try{await sql.unsafe("SELECT truss.runtime_capture_row_prestate('object',$1::bigint,$2::int,$3::int,$4::int)",[object[0].id,allocated[1].type_id,allocated[0].type_id,captionProperty])}catch(e){wrongPrestateOwner=(e as any).errno??(e as any).code}
 assert(wrongPrestateOwner==='55000','native prestate refuses foreign object property owner');await sql.unsafe('ROLLBACK TO SAVEPOINT wrong_prestate_owner');
 await sql.unsafe('SAVEPOINT absent_prestate');await sql.unsafe('DELETE FROM truss.row_home_state');
 const absentPrestate=await sql.unsafe("SELECT encode(truss.runtime_capture_row_prestate('object',$1::bigint,$2::int,$2::int,$3::int),'hex') AS bytes",[object[0].id,allocated[0].type_id,captionProperty]);
 const absence=await sql.unsafe("SELECT (convert_from(decode($1::text,'hex'),'UTF8')::jsonb->'state'='null'::jsonb) AS absent,jsonb_array_length(convert_from(decode($1::text,'hex'),'UTF8')::jsonb->'nodes')::text AS nodes",[absentPrestate[0].bytes]);assert(absence[0].absent&&absence[0].nodes==='0','native snapshot records missing state and empty node inventory explicitly');await sql.unsafe('ROLLBACK TO SAVEPOINT absent_prestate');
 const keyMembershipBody=await Bun.file('packages/postgresql/native/object-key-stage.sql').text();await sql.unsafe(keyMembershipBody);
 const tupleReceipt=valueProducer.encodeCoreKeyTuple(originalInspection.target,{module:'m',element:'a',key:'label-key'},[{string:'雪🙂'}]);valueProducer.verifyCoreKeyTuple(tupleReceipt,originalInspection.target);
 const namespaceHex=Buffer.from('component-test-namespace:'+allocated[0].type_id+':1').toString('hex');
 const keyHex=Buffer.from('umf-key-tuple-v1:hex:'+tupleReceipt.bytesHex).toString('hex');const keyContextHex=Buffer.from(JSON.stringify(tupleReceipt)).toString('hex');
 const stageMembership="SELECT truss.runtime_stage_object_key($1::bigint,$2::int,1::smallint,decode($3::text,'hex'),decode($4::text,'hex'),decode($5::text,'hex')) AS id";
 const keyMembership=await sql.unsafe(stageMembership,[object[0].id,allocated[0].type_id,namespaceHex,keyHex,keyContextHex]);assert(typeof keyMembership[0].id==='string','native membership gets a separate exact storage identity');
 const heldKey=await sql.unsafe("SELECT encode(key_bytes,'hex') AS bytes,encode(original_context_bytes,'hex') AS context FROM truss.object_key_bucket");assert(heldKey[0].bytes===keyHex&&heldKey[0].context===keyContextHex,'original UMF tuple transport and receipt retained natively');
 const keyGeneration=await sql.unsafe('SELECT generation::text AS generation FROM truss.key_bucket_guard');assert(keyGeneration[0].generation==='1'&&(await generation())[0].generation==='5','actual key membership advances guard and operation generations');
 const duplicateOwner=await sql.unsafe('INSERT INTO truss.object(type_id,props,rev) VALUES($1::int,$2::text::jsonb,$3::int) RETURNING id::text AS id',[allocated[0].type_id,JSON.stringify(objectProps),staged[0].provisional_revision]);
 await sql.unsafe('SAVEPOINT duplicate_membership');let keyConflict='';try{await sql.unsafe(stageMembership,[duplicateOwner[0].id,allocated[0].type_id,namespaceHex,keyHex,keyContextHex])}catch(e){keyConflict=(e as any).errno??(e as any).code}assert(keyConflict==='23505','same complete key identity on another native object refuses');await sql.unsafe('ROLLBACK TO SAVEPOINT duplicate_membership');
 const survivingMembership=await sql.unsafe('SELECT count(*)::text AS n FROM truss.object_key_bucket');assert(survivingMembership[0].n==='1','conflicting membership leaves original membership intact');
 await sql.unsafe('SAVEPOINT key_guard_overflow');await sql.unsafe('UPDATE truss.key_bucket_guard SET generation=9223372036854775807');let keyGuardOverflow='';
 try{await sql.unsafe('UPDATE truss.object_key_bucket SET object_id=object_id')}catch(e){keyGuardOverflow=(e as any).errno??(e as any).code}assert(keyGuardOverflow==='54000','actual key membership event refuses guard exhaustion');await sql.unsafe('ROLLBACK TO SAVEPOINT key_guard_overflow');
 const reservedReceipt=valueProducer.encodeCoreKeyTuple(originalInspection.target,{module:'m',element:'a',key:'label-key'},[{string:'reserved'}]);
 const reservedHex=Buffer.from('umf-key-tuple-v1:hex:'+reservedReceipt.bytesHex).toString('hex');const reservationFixture=Buffer.from(JSON.stringify({componentFixture:true,tuple:reservedReceipt})).toString('hex');
 await sql.unsafe("INSERT INTO truss.key_bucket_guard(namespace_sha256,key_sha256,generation) VALUES(sha256(decode($1::text,'hex')),sha256(decode($2::text,'hex')),0)",[namespaceHex,reservedHex]);
 await sql.unsafe("INSERT INTO truss.object_key_reservation_bucket(namespace_bytes,key_bytes,original_reservation_bytes) VALUES(decode($1::text,'hex'),decode($2::text,'hex'),decode($3::text,'hex'))",[namespaceHex,reservedHex,reservationFixture]);
 assert((await generation())[0].generation==='6','actual reservation insertion advances original operation generation');
 await sql.unsafe('SAVEPOINT reserved_membership');let reservedConflict='';try{await sql.unsafe(stageMembership,[duplicateOwner[0].id,allocated[0].type_id,namespaceHex,reservedHex,reservationFixture])}catch(e){reservedConflict=(e as any).errno??(e as any).code}assert(reservedConflict==='23505','retained full-byte reservation refuses membership under forbid policy');await sql.unsafe('ROLLBACK TO SAVEPOINT reserved_membership');
 await sql.unsafe('DELETE FROM truss.object_key_reservation_bucket');assert((await generation())[0].generation==='7','actual reservation deletion advances original operation generation');
 await sql.unsafe('DELETE FROM truss.object WHERE id=$1::bigint',[object[0].id]);
 assert((await generation())[0].generation==='11','actual key state node and scalar cascaded deletes each advance generation');
 const afterCascade=await sql.unsafe('SELECT count(*)::text AS n FROM truss.row_home_state');assert(afterCascade[0].n==='0','canonical cascade removes original state');
 const removedKey=await sql.unsafe('SELECT generation::text AS generation FROM truss.key_bucket_guard');assert(removedKey[0].generation==='2','actual cascaded membership deletion advances original key guard');
 const deletedPrestate=await sql.unsafe("SELECT convert_from(decode($1::text,'hex'),'UTF8')::jsonb #>> '{owner,id}' AS owner_id,convert_from(decode($1::text,'hex'),'UTF8')::jsonb #>> '{state,state_id}' AS state_id",[nativePrestate[0].bytes]);assert(deletedPrestate[0].owner_id===object[0].id&&deletedPrestate[0].state_id===nodeIds[0].state_id,'original native prestate retains deleted parent attribution after cascade');
 await sql.unsafe('UPDATE truss.type_def SET retired_rev=since_rev');
 const next=await sql.unsafe('SELECT * FROM truss.runtime_stage_new_types($1::int,$2::text::jsonb)',[staged[0].provisional_revision,JSON.stringify([{...candidates[0],elementId:'b'}])]);assert(next[0].type_id==='3','retired retained IDs remain high-water contributors');
 const originalLineage=await sql.unsafe("SELECT lineage_profile='truss-type-lineage/0.1.0' AND lineage_bytes=truss.runtime_catalog_lineage(1,'record',document_id,module,element) AS original FROM truss.type_def WHERE element='z'");assert(originalLineage[0].original,'archive-derived original type lineage retained');
 const retained=await sql.unsafe("SELECT document,validation::text AS validation FROM truss.schema_doc WHERE doc_id='original-document'");assert(JSON.parse(retained[0].validation).transition.source.umf==='0.7.0'&&JSON.parse(retained[0].validation).recordChecks[0].validation.complete===false,'original transition and checker result retained natively');assert(retained[0].document===originalDocument,'verbatim original source retained');
 const head=await sql.unsafe('SELECT rev::text AS rev FROM truss.schema_head');assert(JSON.stringify(head)===JSON.stringify(beforeHead),'document stage cannot publish catalog head');
 await sql.unsafe('ROLLBACK');
 const remaining=await sql.unsafe('SELECT count(*)::text AS n FROM truss.schema_rev');assert(remaining[0].n===beforeRevisions[0].n,'rollback removes staged revision and source');
 const rolledRelationships=await sql.unsafe('SELECT count(*)::text AS n FROM truss.relationship_lineage');assert(rolledRelationships[0].n==='0','rollback removes staged relationship lineage');
 const receipt={stringEncoderSha256:new Bun.CryptoHasher('sha256').update(stringEncoderBody).digest('hex'),layoutPath,layoutSha256:new Bun.CryptoHasher('sha256').update(layout).digest('hex'),component:'native operation and owner-backed catalog staging',engine:'PostgreSQL17.9',umfSource:producer.sourceRevision,umfBundleSha256:producer.bundleSha256,checks,lineageProducerSha256:new Bun.CryptoHasher('sha256').update(lineageBody).digest('hex'),bodySha256:new Bun.CryptoHasher('sha256').update(body).digest('hex'),keyMembershipBodySha256:new Bun.CryptoHasher('sha256').update(keyMembershipBody).digest('hex'),umfValueSource:valueProducer.sourceRevision,umfValueBundleSha256:valueProducer.bundleSha256,prestateCaptureSha256:new Bun.CryptoHasher('sha256').update(prestateBody).digest('hex'),observerSha256:new Bun.CryptoHasher('sha256').update(observer).digest('hex'),barrierSha256:new Bun.CryptoHasher('sha256').update(barrier).digest('hex'),catalogStageSha256:new Bun.CryptoHasher('sha256').update(catalogStage).digest('hex'),documentBatchSha256:new Bun.CryptoHasher('sha256').update(documentBatch).digest('hex'),typeMatchSha256:new Bun.CryptoHasher('sha256').update(typeMatchBody).digest('hex'),typeStageSha256:new Bun.CryptoHasher('sha256').update(typeStage).digest('hex'),propertyMatchSha256:new Bun.CryptoHasher('sha256').update(propertyMatchBody).digest('hex'),propertyStageSha256:new Bun.CryptoHasher('sha256').update(propertyStage).digest('hex'),relationshipMatchSha256:new Bun.CryptoHasher('sha256').update(relationshipMatchBody).digest('hex'),relationshipStageSha256:new Bun.CryptoHasher('sha256').update(relationshipStage).digest('hex'),keyBatchSha256:new Bun.CryptoHasher('sha256').update(keyBatch).digest('hex'),keyMatchSha256:new Bun.CryptoHasher('sha256').update(keyMatchBody).digest('hex'),keyStageSha256:new Bun.CryptoHasher('sha256').update(keyStage).digest('hex'),qualification:'Actual xid/context/artifact bounds/single unfinished/rollback/private invocation and actual canonical generation dispatch component only. Canonical fixture carrier bytes, component namespace and reservation fixture are not admitted codec/layout/installation/historical reservation authority. Full-byte key stage and actual membership generation are component evidence only. Protected issuer registration, canonical observers, finalization, deferred complete-cohort checks, installer security and public runtime remain unfinished.'};
 await Bun.write('docs/helix/04-build/evidence/runtime-operation-admission.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({checks:checks.length}));
}finally{await peer.close();await sql.close()}
