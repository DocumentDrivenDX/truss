"""@covers US-056-AC2
Actual authored relationship installation/population prerequisite, not protected traversal.
"""
import json,os
from pathlib import Path
import test_group_create_native as base
from test_security_ontology_edges_native import ontology_document
from truss.contracts import MapValue,TextValue,BooleanValue
from truss.groups import CreateObject,CreateEdge,RootlessOwnership,AuthoredValue,AliasObjectReference,NullOrderKey,GroupSuccess

class PublicRelationshipNativeTests(base.PublicCreateGroupTests):
 for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
  locals()[_name]=None
 def test_actual_authored_resource_relationship_and_population(self):
  root=Path(__file__).resolve().parents[3]
  logical=json.loads((root/'docs/helix/03-test/fixtures/security-public-relationship/document.json').read_bytes())
  relationship=logical['modules'][0]['relationships'][0]
  physical=ontology_document('adoc');physical['modules'][0]['relationships'].append(relationship)
  def source(document):document.clear();document.update(physical)
  connection,host,assembly,tx=self.ready(source,document_ids=('adoc',))
  rows=(('Client','c',{'clientId':'C'}),('Project','pa',{'projectId':'A'}),('Project','pb',{'projectId':'B'}),('Staff','alice',{'staffId':'Alice'}),('Staff','bob',{'staffId':'Bob'}),('Staff','outsider',{'staffId':'Outsider'}),('Resource','ra',{'resourceId':'RA','salary':100}),('Resource','rb',{'resourceId':'RB','salary':200}),('Resource','ro',{'resourceId':'RO','salary':300}),('Assignment','aa',{'assignmentId':'AA','active':True}),('Assignment','ai',{'assignmentId':'AI','active':False}),('Assignment','ba',{'assignmentId':'BA','active':True}),('Ownership','oa',{'ownershipId':'OA'}),('Ownership','ob',{'ownershipId':'OB'}))
  policy_links=(('ProjectClient','pa','c'),('ProjectClient','pb','c'),('StaffAssignment','alice','aa'),('StaffAssignment','alice','ai'),('StaffAssignment','bob','ba'),('AssignmentProject','aa','pa'),('AssignmentProject','ai','pb'),('AssignmentProject','ba','pb'),('OwnershipResource','oa','ra'),('OwnershipResource','ob','rb'),('OwnershipProject','oa','pa'),('OwnershipProject','ob','pb'))
  query_links=tuple(('ResourceRelatedResource',s,t) for s,t in (('rb','rb'),('rb','ra'),('ra','rb'),('ro','rb')))
  links=policy_links+query_links
  refs={name:assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id=name).value for name in {r[0] for r in links}}
  operations=[]
  for record,alias,fields in rows:
   values=tuple(AuthoredValue(name=name,value=BooleanValue(value=value) if type(value) is bool else TextValue(kind='integer' if type(value) is int else 'string',text=str(value))) for name,value in fields.items())
   operations.append(CreateObject(type_definition_pin=self.types[('adoc',record)].definition_pin,values=values,ownership=RootlessOwnership(),alias=alias))
  operations.extend(CreateEdge(relationship_definition_pin=refs[name].definition_pin,source=AliasObjectReference(alias=source),target=AliasObjectReference(alias=target),values=(),order_key=NullOrderKey()) for name,source,target in links)
  context=assembly.group_context_in_transaction(tx).value
  result=self.apply(assembly,tx,context.input(tuple(operations),MapValue(entries=())),context.request('public-relationship-source-seed'))
  self.assertIsInstance(result,GroupSuccess)
  ids={item.alias:int(item.identity.id) for item in result.response.semantic.aliases}
  host.detach();connection.commit()
  expected=[(int(refs[name].relationship_id),ids[s],ids[t]) for name,s,t in links]
  observed=self.admin.execute('SELECT rel_type_id,source_id,target_id FROM truss.edge ORDER BY id').fetchall()
  self.assertEqual(observed,expected)
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(14,))
  self.assertEqual(len(observed),16)
  reader,reader_host,reader_assembly,reader_tx=self.consumer()
  from truss import ObjectFound
  actual_objects=[]
  for record,alias,fields in rows:
   found=reader_assembly.get_object_in_transaction(reader_tx,document_id='adoc',module_id='m',record_id=record,object_id=ids[alias]).value
   self.assertIsInstance(found,ObjectFound)
   actual_fields={name:(int(value.text) if name=='salary' else value.text) if isinstance(value,TextValue) else value for name,value in found.object.values}
   self.assertEqual(actual_fields,fields)
   actual_objects.append((str(ids[alias]),str(self.types[('adoc',record)].type_id),actual_fields))
  reader_host.detach();reader.rollback()
  actual_edges=tuple(tuple(str(value) for value in row) for row in self.admin.execute('SELECT id,rel_type_id,source_id,source_type,target_id,target_type FROM truss.edge ORDER BY id').fetchall())
  from security_ontology_edge_projection import project_public_relationship_edge_cells
  selection={name:str(ref.relationship_id) for name,ref in refs.items()};type_selection={name:str(self.types[('adoc',name)].type_id) for name in ('Client','Project','Staff','Resource','Assignment','Ownership')}
  projected=project_public_relationship_edge_cells(tuple(actual_objects),actual_edges,type_selection,selection)
  self.assertEqual({(e[2],e[4]) for e in projected['queryRelationshipOccurrences']},{(str(ids[s]),str(ids[t])) for _,s,t in query_links})
  self.assertEqual(len(projected['queryRelationshipOccurrences']),4)
  for missing,wrong_type in ((False,True),(True,False)):
   changed=list(actual_edges);index=next(i for i,e in enumerate(changed) if e[1]==selection['ResourceRelatedResource']);edge=list(changed[index]);edge[5]=type_selection['Staff'] if wrong_type else edge[5];edge[4]='9223372036854775807' if missing else edge[4];changed[index]=tuple(edge)
   with self.assertRaisesRegex(ValueError,'Original complete public relationship projection required'):project_public_relationship_edge_cells(tuple(actual_objects),tuple(changed),type_selection,selection)
  # Native catalog identity is observed, never copied from the old fixture IDs.
  directory=os.environ.get('TRUSS_SECURITY_PUBLIC_RELATIONSHIP_EVIDENCE')
  if directory:
   out=Path(directory);out.mkdir(parents=True,exist_ok=True)
   (out/'projected-relationship-facts.json').write_text(json.dumps(projected,indent=2)+'\n')
   for document in self.documents:(out/(document.document_id+'-accepted-source.json')).write_bytes(document.content)
   from hashlib import sha256
   from truss._security_catalog_assessment import capture_accepted_catalog,SOURCE_TABLES
   from psycopg import sql
   physical_request=json.dumps({'modules':[{'pin':{'documentId':d.document_id,'revision':d.document_revision,'umfVersion':'0.8.0','sha256':sha256(d.content).hexdigest()},'documentJson':d.content.decode()} for d in self.documents]}).encode()
   with self.admin.transaction():
    self.admin.execute(sql.SQL('LOCK TABLE {} IN SHARE MODE').format(sql.SQL(',').join(sql.Identifier('truss',name) for name in SOURCE_TABLES)))
    with self.admin.cursor() as cursor:assessment=capture_accepted_catalog(cursor,physical_request)
    relationship_binary=os.environ.get('TRUSS_SECURITY_RELATIONSHIP_COMPILER_BINARY')
    if relationship_binary:
     self.admin.execute('CREATE TABLE truss.catalog_subject_map(role_oid pg_catalog.oid PRIMARY KEY,staff_key pg_catalog.text NOT NULL)')
     self.admin.execute('LOCK TABLE truss.object,truss.edge,truss.catalog_subject_map IN SHARE MODE')
    (out/'accepted-assessment.json').write_bytes(assessment)
    import runpy
    derive=runpy.run_path(str(root/'scripts/prepare-security-relationship-correspondence.py'))['derive_relationship_correspondence']
    fixture=root/'docs/helix/03-test/fixtures/security-public-relationship'
    selected={name:(fixture/(name+'.json')).read_bytes() for name in ('document','resolution','policy','transport')}
    duplicate=b'{"inventory":{},"inventory":{}}'
    with self.assertRaisesRegex(ValueError,'Duplicate correspondence source member'):derive(duplicate,physical_request,selected)
    for suffix,policy_file in [('', 'policy'),('-observation-denied','policy-observation-denied')]:
     sources={**selected,'policy':(fixture/(policy_file+'.json')).read_bytes()}
     correspondence=derive(assessment,physical_request,sources)
     mapped=json.loads(correspondence)
     self.assertEqual(mapped['inventorySha256'],sha256(assessment).hexdigest())
     self.assertEqual(mapped['logicalSourceDigests']['policy'],sha256(sources['policy']).hexdigest())
     self.assertEqual(mapped['queryRelationships'][0]['nativeRelationshipId'],str(refs['ResourceRelatedResource'].relationship_id))
     (out/('live-correspondence'+suffix+'.json')).write_bytes(correspondence)
     from security_relationship_request import prepare_relationship_request
     request=prepare_relationship_request(physical_request,assessment,observation_denied=bool(suffix))
     selected_request=json.loads(request)
     self.assertEqual(json.loads(selected_request['bindingJson'])['inventoryJson'].encode(),assessment)
     self.assertEqual(selected_request['policyJson'].encode(),sources['policy'])
     self.assertEqual(json.loads(selected_request['queryProfileJson'])['binding']['sha256'],sha256(selected_request['bindingJson'].encode()).hexdigest())
     (out/('compiler-request'+suffix+'.json')).write_bytes(request)
     if relationship_binary:
      import subprocess
      from security_relationship_codecs import prepare_owned_relationship_codec_checker
      from security_relationship_inspection import prepare_owned_relationship_inspector
      from security_relationship_capture import execute_relationship_program
      output=subprocess.run([relationship_binary],input=request,capture_output=True,check=True,timeout=15).stdout
      checker=prepare_owned_relationship_codec_checker(Path(relationship_binary).with_name('security_relationship_codecs'))
      inspector=prepare_owned_relationship_inspector(Path(relationship_binary).with_name('security_relationship_result'))
      observations=[]
      for subject,alias in [('Alice','alice'),('Bob','bob'),('Outsider','outsider')]:
       with self.admin.cursor() as cursor:executed=execute_relationship_program(cursor,request,output,ids[alias],checker,inspector)
       rows=json.loads(executed['batch'])['rows']
       expected=[[{'outcomeId':'original','disposition':'original','value':{'string':'RB'}}]] if subject=='Bob' and not suffix else []
       self.assertEqual(rows,expected)
       observations.append({'subjectDataKey':subject,'expected':expected,'observed':rows,'operandBatch':executed['operandBatch'].decode(),'batch':executed['batch'].decode(),'inspection':executed['inspection'].decode()})
      (out/('excluded-assessor-sql'+suffix+'.json')).write_text(json.dumps({'scope':'Excluded fixture assessor with supplied native Staff locator; not authenticated ordinary caller or protected publication','securityReady':False,'observations':observations},indent=2)+'\n')
   (out/'physical-request.json').write_bytes(physical_request)
   catalog={}
   for name,table,order in (('types','type_def','type_id'),('properties','prop_def','prop_id'),('keys','key_def','type_id,key_num'),('relationships','rel_def','rel_type_id'),('endpoints','rel_endpoint','rel_type_id,source_type,target_type')):
    catalog[name]=[row[0] for row in self.admin.execute('SELECT pg_catalog.to_jsonb(t)::pg_catalog.text FROM truss.'+table+' t ORDER BY '+order).fetchall()]
   (out/'catalog-inventory.json').write_text(json.dumps({'scope':'Excluded assessor raw native TEXT JSONB capture; no protected source admission','revision':str(self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1').fetchone()[0]),'inventoryTextRows':catalog},indent=2)+'\n')
   (out/'physical-document.json').write_text(json.dumps(physical,separators=(',',':'))+'\n')
   capture={'status':'native-installation-population-prerequisite-passed','securityReady':False,'serverVersion':self.admin.execute('SHOW server_version').fetchone()[0],'relationId':str(refs['ResourceRelatedResource'].relationship_id),'expectedEdges':expected,'observedEdges':observed,'objectIds':ids,'catalogRelations':[r[0] for r in self.admin.execute('SELECT pg_catalog.to_jsonb(r)::pg_catalog.text FROM truss.rel_def r ORDER BY rel_type_id').fetchall()],'nativeEdges':[r[0] for r in self.admin.execute('SELECT pg_catalog.to_jsonb(e)::pg_catalog.text FROM truss.edge e ORDER BY id').fetchall()]}
   (out/'native-capture.json').write_text(json.dumps(capture,indent=2)+'\n')
  if os.environ.get('TRUSS_SECURITY_RELATIONSHIP_SOURCE_FACTORY'):
   import subprocess
   from hashlib import sha256
   from dataclasses import replace
   from psycopg import sql
   from truss import Ok,Error,adopt_psycopg_host
   from truss._security_catalog_assessment import capture_accepted_catalog
   from truss._security_relationship_source import PreparedRelationshipSecuritySource
   from truss._security_home_installation import bootstrap_security_homes_in_transaction
   from truss._security_catalog_source_installation import bootstrap_catalog_source_marker_in_transaction,verify_catalog_source_archive_with_cursor
   from truss._security_source_epoch_installation import bootstrap_source_epoch_infrastructure_in_transaction
   from truss._security_catalog_source_epoch import issue_initial_catalog_source_epoch_in_transaction
   from truss._psycopg_fact_cut import _FactRelationComparison,_FactColumnComparison
   from security_relationship_request import prepare_relationship_request
   binary=os.environ['TRUSS_SECURITY_RELATIONSHIP_COMPILER_BINARY']
   physical_request=json.dumps({'modules':[{'pin':{'documentId':d.document_id,'revision':d.document_revision,'umfVersion':'0.8.0','sha256':sha256(d.content).hexdigest()},'documentJson':d.content.decode()} for d in self.documents]}).encode()
   self.admin.execute('BEGIN');factory=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);factory_tx=factory.adopt_transaction().value
   self.addCleanup(factory.detach)
   with self.admin.cursor() as cursor:assessment=capture_accepted_catalog(cursor,physical_request)
   compiler_request=prepare_relationship_request(physical_request,assessment)
   output=subprocess.run([binary],input=compiler_request,capture_output=True,check=True,timeout=15).stdout
   profile=sha256(compiler_request).digest();guard=(self.installation.installation_id.encode(),profile,1)
   selected=PreparedRelationshipSecuritySource(physical_request,assessment,compiler_request,output,guard)
   homes=bootstrap_security_homes_in_transaction(factory,factory_tx,installation_identity=guard[0],authored_profile=profile,max_retained=8)
   self.assertIsInstance(homes,Ok,str(factory._custody.last_attempt.error))
   marked=bootstrap_catalog_source_marker_in_transaction(factory,factory_tx,selected)
   self.assertIsInstance(marked,Ok,str(factory._custody.last_attempt.error))
   self.assertIsInstance(bootstrap_catalog_source_marker_in_transaction(factory,factory_tx,selected),Error)
   infrastructure=bootstrap_source_epoch_infrastructure_in_transaction(factory,factory_tx,installation_identity=guard[0])
   self.assertIsInstance(infrastructure,Ok,str(factory._custody.last_attempt.error))
   subjects=None
   if os.environ.get('TRUSS_SECURITY_RELATIONSHIP_REGISTERED_SUBJECT'):
    import uuid
    from truss._security_graph_subject_installation import bootstrap_graph_subjects_in_transaction
    self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.catalog_subject_map').fetchone(),(0,))
    self.admin.execute('DROP TABLE truss.catalog_subject_map')
    role_prefix='relationship_subject_'+uuid.uuid4().hex[:8]
    roles={name:role_prefix+'_'+name.lower() for name in ('Alice','Bob','Outsider')}
    for role in roles.values():self.admin.execute(sql.SQL('CREATE ROLE {} LOGIN NOINHERIT').format(sql.Identifier(role)))
    registered=bootstrap_graph_subjects_in_transaction(factory,factory_tx,source=selected,bindings=tuple((role,name) for name,role in roles.items()))
    self.assertIsInstance(registered,Ok,str(factory._custody.last_attempt.error));subjects=registered.value
    self.assertIn(b'truss.registered-relationship-subject/0.1-candidate',subjects.profile_bytes)
   else:
    self.admin.execute(sql.SQL('ALTER TABLE truss.catalog_subject_map OWNER TO {}').format(sql.Identifier(self.installation.owner_role)))
   fence=(root/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text();self.admin.execute(fence)
   self.admin.execute(sql.SQL('ALTER FUNCTION truss.runtime_fence_authorization_fact_write() OWNER TO {}').format(sql.Identifier(self.installation.owner_role)))
   facts=[]
   for name in ('object','edge','catalog_subject_map'):
    self.admin.execute(sql.SQL('CREATE TRIGGER fact_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON {} FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_authorization_fact_write()').format(sql.Identifier('truss',name)))
    self.admin.execute(sql.SQL('ALTER TABLE {} ENABLE ALWAYS TRIGGER fact_write_fence').format(sql.Identifier('truss',name)))
    oid,owner=self.admin.execute('SELECT oid,relowner FROM pg_catalog.pg_class WHERE oid=%s::pg_catalog.regclass',('truss.'+name,)).fetchone()
    columns=self.admin.execute('SELECT attname,attnum,atttypid,atttypmod,attnotnull,attcollation,attgenerated,attidentity FROM pg_catalog.pg_attribute WHERE attrelid=%s AND attnum>0 AND NOT attisdropped ORDER BY attnum',(oid,)).fetchall()
    facts.append(_FactRelationComparison('truss',name,oid,owner,fence.split('AS $$',1)[1].split('$$;',1)[0],tuple(_FactColumnComparison(*c) for c in columns)))
   inputs=dict(mapping=selected,marker=marked.value,infrastructure=infrastructure.value,fact_relations=tuple(facts),subject_source=(root/'packages/python/src/truss/_security_bootstrap/graph-subject.sql').read_bytes())
   self.admin.execute("CREATE TEMP TABLE relationship_factory_prior(value text);INSERT INTO relationship_factory_prior VALUES('kept');SAVEPOINT before_relationship_epoch")
   issued=issue_initial_catalog_source_epoch_in_transaction(factory,factory_tx,**inputs)
   self.assertIsInstance(issued,Ok,str(factory._custody.last_attempt.error))
   comparison=issued.value.comparison
   self.assertIn(b'truss-owned-relationship-source-profile/0.1-candidate',comparison.profile)
   self.assertEqual(self.admin.execute('SELECT source_epoch,profile_bytes,evidence_bytes FROM truss.source_epoch_registry').fetchall(),[(comparison.epoch,comparison.profile,assessment)])
   with self.admin.cursor() as cursor:verify_catalog_source_archive_with_cursor(cursor,selected,self.installation.installation_id)
   self.assertIsInstance(issue_initial_catalog_source_epoch_in_transaction(factory,factory_tx,**inputs),Error)
   self.admin.execute('ROLLBACK TO before_relationship_epoch')
   self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.source_epoch_registry').fetchone(),(0,))
   self.assertEqual(self.admin.execute('TABLE relationship_factory_prior').fetchall(),[('kept',)])
   stale=replace(selected,native_guard=(guard[0],profile,2))
   self.assertIsInstance(issue_initial_catalog_source_epoch_in_transaction(factory,factory_tx,**{**inputs,'mapping':stale}),Error)
   self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.source_epoch_registry').fetchone(),(0,))
   issued=issue_initial_catalog_source_epoch_in_transaction(factory,factory_tx,**inputs);self.assertIsInstance(issued,Ok,str(factory._custody.last_attempt.error))
   relationship_context=None
   if os.environ.get('TRUSS_SECURITY_RELATIONSHIP_EPOCH_READ'):
    from truss._security_relationship_epoch_read import bootstrap_relationship_epoch_read_cut_in_transaction,RelationshipEpochReadContext
    private_role='relationship_executor_'+__import__('uuid').uuid4().hex[:8]
    self.admin.execute(sql.SQL('CREATE ROLE {} LOGIN NOINHERIT').format(sql.Identifier(private_role)))
    self.admin.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(private_role)))
    from truss._security_catalog_assessment import SOURCE_TABLES
    for table in ('object','edge','catalog_subject_map')+SOURCE_TABLES:self.admin.execute(sql.SQL('GRANT SELECT ON {} TO {}').format(sql.Identifier('truss',table),sql.Identifier(private_role)))
    routines=self.admin.execute("SELECT p.oid::pg_catalog.regprocedure::pg_catalog.text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss' AND NOT p.prosecdef AND p.prokind='f'").fetchall()
    for routine, in routines:self.admin.execute(sql.SQL('GRANT EXECUTE ON FUNCTION '+routine+' TO {}').format(sql.Identifier(private_role)))
    original_cut=(root/'scripts/security-ontology-read-cut.sql').read_text();self.admin.execute(original_cut)
    self.admin.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.acquire_ontology_read_cut() TO {}').format(sql.Identifier(private_role)))
    issuer=bootstrap_relationship_epoch_read_cut_in_transaction(factory,factory_tx,executor_role=private_role)
    self.assertIsInstance(issuer,Ok,str(factory._custody.last_attempt.error))
    relationship_context=RelationshipEpochReadContext(selected,issued.value.comparison,issuer.value,inputs['subject_source'])
   if directory:
    (out/'source-epoch-issuance.json').write_text(json.dumps({'securityReady':False,'profile':json.loads(issued.value.comparison.profile),'epoch':issued.value.comparison.epoch,'exactReadback':True,'reuseRefused':True,'rollbackKeepsPriorWork':True,'staleGuardNoEpoch':True,'freshSuccessorIssued':True,'scope':'Actual initial native source epoch registration only; ordinary Subject/read/publication admission remains separate'},indent=2)+'\n')
   factory.detach()
   if subjects is None:self.admin.rollback()
   else:
    self.admin.commit()
    import psycopg
    from truss._security_graph_subject_installation import read_own_graph_subject_with_cursor
    observed=[]
    for name,role in roles.items():
     parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['user']=role
     with psycopg.connect(**parameters,autocommit=True) as ordinary:
      identity=ordinary.execute('SELECT (SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database())::text,(SELECT oid FROM pg_catalog.pg_roles WHERE rolname=SESSION_USER)::text').fetchone()
      with ordinary.cursor() as cursor:self.assertEqual(read_own_graph_subject_with_cursor(cursor,subjects,identity),name)
      with self.assertRaises(psycopg.errors.InsufficientPrivilege):ordinary.execute('SELECT * FROM truss.catalog_subject_map')
      observed.append({'subject':name,'ownNativeSession':True,'rawMapSelectDenied':True})
    if relationship_context is not None:
     from truss._security_relationship_epoch_read import acquire_relationship_epoch_read,verify_held_relationship_epoch_read,snapshot_relationship_epoch_read_context
     from truss._security_graph_epoch_read import snapshot_graph_epoch_read_context
     from security_ontology_read_cut import acquire_issued_ontology_read_cut
     parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['user']=private_role
     with psycopg.connect(**parameters,autocommit=True) as private:
      private.execute('BEGIN')
      with private.cursor() as cursor:
       acquire_issued_ontology_read_cut(cursor,relationship_context.issuer.owner_oid,relationship_context.issuer.caller_oid)
       acquire_relationship_epoch_read(cursor,relationship_context);verify_held_relationship_epoch_read(cursor,relationship_context)
       stale_context=replace(relationship_context,comparison=replace(relationship_context.comparison,epoch='stale-epoch'))
       with self.assertRaisesRegex(ValueError,'Original current graph source epoch required'):verify_held_relationship_epoch_read(cursor,stale_context)
       with self.assertRaises(ValueError):snapshot_graph_epoch_read_context(relationship_context)
      private.rollback()
     if directory:(out/'relationship-epoch-read.json').write_text(json.dumps({'securityReady':False,'privateExecutorOwnSession':True,'actualSourceFactAndEpochCuts':True,'currentArchivesGuardCensusVerified':True,'staleEpochRefused':True,'legacyContextRefused':True,'scope':'Ordinary private executor source epoch read, not protected Resource query/publication'},indent=2)+'\n')
    if directory:(out/'registered-subjects.json').write_text(json.dumps({'securityReady':False,'profile':json.loads(subjects.profile_bytes),'observations':observed,'scope':'Actual ordinary own-session metadata issuer only; protected Resource traversal/publication remains pending'},indent=2)+'\n')
