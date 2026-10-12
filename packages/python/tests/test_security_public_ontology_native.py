"""Actual public graph ontology fixture; candidate lowering, not admitted security."""
import json,os,subprocess
from pathlib import Path
import psycopg
from truss import Ok
from truss.contracts import TextValue,BooleanValue
from truss.groups import CreateObject,CreateEdge,AuthoredValue,RootlessOwnership,AliasObjectReference,NullOrderKey,GroupSuccess,RequestNone
import test_group_create_native as groups
RECORDS={'Client':{'code':'string'},'Project':{'code':'string'},'Staff':{'code':'string','login':'string'},'Resource':{'code':'string'},'Assignment':{'code':'string','active':'boolean'}}
LINKS={'staff_assignment':('Staff','Assignment'),'assignment_project':('Assignment','Project'),'resource_project':('Resource','Project'),'project_client':('Project','Client')}
class PublicOntologySecurityTests(groups.PublicCreateGroupTests):
 for name in tuple(n for n in dir(groups.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None
 def tearDown(self):
  self.admin.rollback();self.admin.execute('DROP SCHEMA IF EXISTS ontology_fixture CASCADE')
  super().tearDown()
 def consumer(self):
  # Larger atomic ontology seed; retain an explicit finite native deadline.
  from truss import adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='consumer'
  connection=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=60000')
  self.addCleanup(connection.close);connection.execute('BEGIN');host=adopt_psycopg_host(connection,statement_timeout_ms=60000,operation_timeout_ms=60000);self.addCleanup(host.detach);self.consumer_connections.append((connection,host))
  assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
  return connection,host,assembly,host.adopt_transaction().value
 def model(self,document):
  if document['id']!='adoc':return # The ontology belongs to adoc; retain zdoc baseline.
  m=document['modules'][0];m['elements']=[];m['relationships']=[]
  for name,fields in RECORDS.items():
   m['elements'].append({'id':name,'kind':'record','members':[{'module':'m','element':name+'-'+f} for f in fields],'keys':[{'id':'pk','name':'primary','primary':True,'fields':[{'module':'m','element':name+'-code'}]}],'extensions':{}})
   for field,scalar in fields.items():m['elements'].append({'id':name+'-'+field,'name':name+'-'+field,'kind':'field','scalarType':scalar,'nullability':'required','cardinality':'one','extensions':{}})
  for name,(source,target) in LINKS.items():m['relationships'].append({'id':name,'name':name,'source':[{'module':'m','element':source}],'target':[{'module':'m','element':target,'key':'pk'}],'sourceMultiplicity':{'min':0,'max':100},'targetMultiplicity':{'min':0,'max':100},'targetLifecycle':'independent','directed':True})
 def test_public_created_membership_graph(self):
  c,h,a,t=self.ready(self.model);ops=[]
  def node(record,code,**extras):
   values={'code':code,**extras};ops.append(CreateObject(type_definition_pin=self.types[('adoc',record)].definition_pin,values=tuple(AuthoredValue(name=record+'-'+f,value=BooleanValue(value=v) if isinstance(v,bool) else TextValue(kind='string',text=v)) for f,v in values.items()),ownership=RootlessOwnership(),alias=code))
  node('Client','C');node('Project','A');node('Project','B')
  for login in ['alice','bob','outsider']:node('Staff','staff-'+login,login=login)
  for code in ['RA','RB','RAB','RO']:node('Resource',code)
  for code,active in [('AA',True),('AB',False),('BB',True)]:node('Assignment',code,active=active)
  connections={'staff_assignment':[('staff-alice','AA'),('staff-alice','AB'),('staff-bob','BB')],'assignment_project':[('AA','A'),('AB','B'),('BB','B')],'resource_project':[('RA','A'),('RB','B'),('RAB','A'),('RAB','B')],'project_client':[('A','C'),('B','C')]}
  for link,pairs in connections.items():
   pin=a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id=link).value.definition_pin
   for i,(source,target) in enumerate(pairs):ops.append(CreateEdge(relationship_definition_pin=pin,source=AliasObjectReference(alias=source),target=AliasObjectReference(alias=target),values=(),order_key=NullOrderKey(),alias=link+str(i)))
  inp,_=self.input(a,t,tuple(ops));result=a.apply_in_transaction(t,inp,RequestNone(),documents=self.documents,bun_executable='/opt/homebrew/bin/bun');self.assertIsInstance(result,Ok,str(a._host._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess);h.detach();c.commit()
  packet={'records':{},'links':{}}
  for record,fields in RECORDS.items():
   type_id=self.types[('adoc',record)].type_id;props={name:str(pid) for name,pid in self.admin.execute('SELECT name,prop_id FROM truss.prop_def WHERE type_id=%s',(int(type_id),))}
   packet['records'][record]={'typeId':type_id,'fields':{f:{'id':props[record+'-'+f],'scalar':scalar} for f,scalar in fields.items()}}
  for link,(source,target) in LINKS.items():packet['links'][link]={'id':str(self.admin.execute("SELECT rel_type_id FROM truss.rel_def WHERE document_id='adoc' AND module='m' AND rel_id=%s",(link,)).fetchone()[0]),'source':source,'target':target}
  produced=subprocess.run(['/opt/homebrew/bin/bun',str(Path(__file__).resolve().parents[3]/'tests/fixtures/security-public-ontology.ts')],input=json.dumps(packet),text=True,capture_output=True,timeout=30);self.assertEqual(produced.returncode,0,produced.stderr);sql=json.loads(produced.stdout);observations=[]
  version=self.admin.execute('SHOW server_version_num').fetchone()[0];self.assertEqual(version,'180006');observations.append({'id':'native-version','observed':version})
  self.admin.execute('CREATE SCHEMA ontology_fixture')
  for name,source in sql['objects'].items():
   valid=self.admin.execute(source['validitySql']).fetchone()[0];self.assertEqual(valid,'true');observations.append({'id':'complete-object-source-'+name,'observed':valid});self.admin.execute('CREATE VIEW ontology_fixture.'+name.lower()+' AS '+source['sql'])
  for name,source in sql['edges'].items():
   valid=self.admin.execute(source['validitySql']).fetchone()[0];self.assertEqual(valid,'true');observations.append({'id':'complete-edge-endpoints-'+name,'observed':valid});self.admin.execute('CREATE VIEW ontology_fixture.'+name+' AS '+source['sql'])
  self.admin.execute('CREATE VIEW ontology_fixture.assignments AS SELECT a.code,a.active,s.source_code AS staff_code,p.target_code AS project_code FROM ontology_fixture.assignment a LEFT JOIN ontology_fixture.staff_assignment s ON s.target_code=a.code LEFT JOIN ontology_fixture.assignment_project p ON p.source_code=a.code')
  rows=self.admin.execute('SELECT code,active,staff_code,project_code FROM ontology_fixture.assignments ORDER BY code').fetchall();self.assertEqual(rows,[('AA',True,'staff-alice','A'),('AB',False,'staff-alice','B'),('BB',True,'staff-bob','B')]);observations.append({'id':'actual-assignment-business-key-facts','observed':[list(r) for r in rows]})
  self.admin.execute('CREATE ROLE ontology_facts NOLOGIN NOINHERIT NOSUPERUSER NOBYPASSRLS;GRANT USAGE ON SCHEMA truss,ontology_fixture TO ontology_facts;GRANT SELECT(id,type_id,props) ON truss.object TO ontology_facts;GRANT SELECT(id,rel_type_id,source_id,source_type,target_id,target_type) ON truss.edge TO ontology_facts')
  self.addCleanup(self.admin.execute,'DROP OWNED BY ontology_facts;DROP ROLE ontology_facts')
  for name in [*RECORDS,*LINKS,'assignments']:self.admin.execute('ALTER VIEW ontology_fixture.'+name.lower()+' OWNER TO ontology_facts')
  self.admin.execute('CREATE FUNCTION ontology_fixture.decision_bound(text,text) RETURNS text LANGUAGE SQL SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=on AS $$ '+sql['fold']['sql']+' $$;REVOKE ALL ON FUNCTION ontology_fixture.decision_bound(text,text) FROM PUBLIC;GRANT CREATE ON SCHEMA ontology_fixture TO ontology_facts;ALTER FUNCTION ontology_fixture.decision_bound(text,text) OWNER TO ontology_facts')
  self.admin.execute("CREATE FUNCTION ontology_fixture.eligible_bound(text,text) RETURNS bool LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=on AS $$ DECLARE decision text;BEGIN decision:=ontology_fixture.decision_bound($1,$2);IF decision IS NULL OR decision NOT IN ('permit','deny') THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;RETURN decision='permit';END $$;REVOKE ALL ON FUNCTION ontology_fixture.eligible_bound(text,text) FROM PUBLIC;ALTER FUNCTION ontology_fixture.eligible_bound(text,text) OWNER TO ontology_facts")
  self.admin.execute("CREATE FUNCTION ontology_fixture.eligible(text) RETURNS bool LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=on AS $$ DECLARE subject_count bigint;subject_key text;BEGIN IF current_setting('transaction_isolation')<>'read committed' THEN RAISE EXCEPTION 'security authority profile unavailable' USING ERRCODE='0A000';END IF;SELECT count(*),min(code) INTO subject_count,subject_key FROM ontology_fixture.staff WHERE login OPERATOR(pg_catalog.=) SESSION_USER::pg_catalog.text;IF subject_count<>1 THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;RETURN ontology_fixture.eligible_bound($1,subject_key);END $$;REVOKE ALL ON FUNCTION ontology_fixture.eligible(text) FROM PUBLIC;ALTER FUNCTION ontology_fixture.eligible(text) OWNER TO ontology_facts;REVOKE CREATE ON SCHEMA ontology_fixture FROM ontology_facts")
  self.admin.execute('ALTER TABLE truss.object ENABLE ROW LEVEL SECURITY;ALTER TABLE truss.object FORCE ROW LEVEL SECURITY;CREATE POLICY complete_private_facts ON truss.object FOR SELECT TO ontology_facts USING(true)')
  resource=packet['records']['Resource'];key=resource['fields']['code']['id']
  for login in ['alice','bob','outsider']:
   self.admin.execute('CREATE ROLE '+login+' LOGIN NOSUPERUSER NOBYPASSRLS;GRANT USAGE ON SCHEMA truss,ontology_fixture TO '+login+';GRANT SELECT(id,type_id,props) ON truss.object TO '+login+';GRANT EXECUTE ON FUNCTION ontology_fixture.eligible(text) TO '+login)
   self.addCleanup(self.admin.execute,'DROP OWNED BY '+login+';DROP ROLE '+login)
  self.admin.execute("CREATE POLICY resource_membership ON truss.object FOR SELECT TO alice,bob,outsider USING(type_id="+resource['typeId']+" AND ontology_fixture.eligible(props->'"+key+"'->>'text'))")
  expected={'alice':['RA','RAB'],'bob':['RAB','RB'],'outsider':[]}
  for login,wanted in expected.items():
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    identity=reader.execute('SELECT session_user,current_user').fetchone();self.assertEqual(identity,(login,login));observations.append({'id':'original-native-caller-'+login,'observed':list(identity)})
    actual=[r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,wanted);observations.append({'id':'membership-resource-oracle-'+login,'expected':wanted,'observed':actual})
    count=reader.execute('SELECT count(*) FROM truss.object').fetchone()[0];self.assertEqual(count,len(wanted));observations.append({'id':'membership-count-'+login,'observed':count})
    flags=reader.execute('SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone();self.assertEqual(flags,(False,False));observations.append({'id':'ordinary-native-flags-'+login,'observed':list(flags)})
    private_count=reader.execute('SELECT count(*) FROM truss.object WHERE type_id=%s',(int(packet['records']['Assignment']['typeId']),)).fetchone()[0];self.assertEqual(private_count,0);observations.append({'id':'hidden-assignment-object-count-'+login,'observed':private_count})
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute('SELECT * FROM truss.edge')
    observations.append({'id':'private-native-edge-table-denied-'+login,'observed':'42501'})
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute("SELECT ontology_fixture.eligible_bound('RB','staff-bob')")
    observations.append({'id':'caller-supplied-subject-binding-denied-'+login,'observed':'42501'})
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute('SET ROLE ontology_facts')
    observations.append({'id':'private-fact-owner-adoption-denied-'+login,'observed':'42501'})
    storage_substitution=reader.execute('SELECT id FROM truss.object WHERE ontology_fixture.eligible(id::text)').fetchall();self.assertEqual(storage_substitution,[]);observations.append({'id':'storage-id-is-not-business-key-'+login,'observed':storage_substitution})
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute('SELECT * FROM ontology_fixture.assignments')
    observations.append({'id':'private-assignment-view-denied-'+login,'observed':'42501'})
  aliases={entry.alias:entry.identity for entry in result.value.response.semantic.aliases};assignment=packet['records']['Assignment'];active_id=assignment['fields']['active']['id']
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':False}),int(aliases['AA'].id),int(assignment['typeId'])))
  for login,wanted in [('alice',[]),('bob',['RAB','RB'])]:
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    actual=[r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,wanted);observations.append({'id':'fresh-statement-after-committed-assignment-change-'+login,'expected':wanted,'observed':actual})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':True}),int(aliases['AA'].id),int(assignment['typeId'])))
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='alice'
  with psycopg.connect(**params,autocommit=True) as reader:
   actual=[r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,['RA','RAB']);observations.append({'id':'restored-assignment-original-visibility','observed':actual})
  # A malformed hidden assignment must not look like a complete empty result.
  self.admin.execute('UPDATE truss.object SET props=props-%s WHERE id=%s AND type_id=%s',(active_id,int(aliases['AB'].id),int(assignment['typeId'])))
  valid=self.admin.execute(sql['objects']['Assignment']['validitySql']).fetchone()[0];self.assertEqual(valid,'false');observations.append({'id':'hidden-assignment-required-field-preflight-invalid','observed':valid})
  decision=self.admin.execute("SELECT ontology_fixture.decision_bound('RB','staff-bob')").fetchone()[0];self.assertEqual(decision,'indeterminate');observations.append({'id':'unrelated-valid-permit-cannot-hide-incomplete-facts','observed':decision})
  for login in ['alice','bob','outsider']:
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    for operation,query in [('list','SELECT id FROM truss.object'),('count','SELECT count(*) FROM truss.object')]:
     with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState) as failure:reader.execute(query).fetchall()
     self.assertEqual(failure.exception.sqlstate,'55000');self.assertEqual(failure.exception.diag.message_primary,'security facts unavailable');observations.append({'id':'incomplete-private-facts-refuse-'+operation+'-'+login,'observed':{'sqlState':'55000','message':'security facts unavailable'}})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':False}),int(aliases['AB'].id),int(assignment['typeId'])))
  valid=self.admin.execute(sql['objects']['Assignment']['validitySql']).fetchone()[0];self.assertEqual(valid,'true');observations.append({'id':'complete-assignment-facts-restored','observed':valid})
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='bob'
  with psycopg.connect(**params,autocommit=True) as reader:
   actual=[r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,['RAB','RB']);observations.append({'id':'restored-facts-original-bob-visibility','observed':actual})
  # An endpoint object exists, but a required business key cannot be decoded.
  project=packet['records']['Project'];project_key=project['fields']['code']['id']
  self.admin.execute('UPDATE truss.object SET props=props-%s WHERE id=%s AND type_id=%s',(project_key,int(aliases['B'].id),int(project['typeId'])))
  rows=self.admin.execute('SELECT occurrence_id,source_code,target_code FROM ontology_fixture.resource_project ORDER BY occurrence_id').fetchall();self.assertEqual(len(rows),4);self.assertEqual(sum(row[2] is None for row in rows),2);observations.append({'id':'malformed-project-key-preserves-original-edge-population','edgeCount':len(rows),'nullTargetKeys':2})
  decision=self.admin.execute("SELECT ontology_fixture.decision_bound('RA','staff-alice')").fetchone()[0];self.assertEqual(decision,'indeterminate');observations.append({'id':'valid-other-project-does-not-hide-null-endpoint-key','observed':decision})
  for login in ['alice','bob','outsider']:
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState) as failure:reader.execute('SELECT count(*) FROM truss.object').fetchall()
    self.assertEqual(failure.exception.sqlstate,'55000');observations.append({'id':'incomplete-endpoint-key-refuses-count-'+login,'observed':'55000'})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(project_key,json.dumps({'kind':'string','text':'B'}),int(aliases['B'].id),int(project['typeId'])))
  decision=self.admin.execute("SELECT ontology_fixture.decision_bound('RA','staff-alice')").fetchone()[0];self.assertEqual(decision,'permit');observations.append({'id':'restored-project-key-restores-original-decision','observed':decision})
  # Ownerless data must not short-circuit a missing intrinsic subject binding.
  for resource_key,subject_key in [('RO',None),(None,'staff-alice')]:
   decision=self.admin.execute('SELECT ontology_fixture.decision_bound(%s,%s)',(resource_key,subject_key)).fetchone()[0];self.assertEqual(decision,'indeterminate');observations.append({'id':'missing-intrinsic-key-indeterminate-'+('subject' if subject_key is None else 'resource'),'observed':decision})
  staff=packet['records']['Staff'];login_id=staff['fields']['login']['id']
  self.admin.execute('UPDATE truss.object SET props=props-%s WHERE id=%s AND type_id=%s',(login_id,int(aliases['staff-alice'].id),int(staff['typeId'])))
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='alice'
  with psycopg.connect(**params,autocommit=True) as reader:
   with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState) as failure:reader.execute("SELECT ontology_fixture.eligible('RO')").fetchall()
   self.assertEqual(failure.exception.sqlstate,'55000');observations.append({'id':'missing-original-caller-binding-refuses-even-ownerless-resource','observed':'55000'})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(login_id,json.dumps({'kind':'string','text':'alice'}),int(aliases['staff-alice'].id),int(staff['typeId'])))
  with psycopg.connect(**params,autocommit=True) as reader:
   result=reader.execute("SELECT ontology_fixture.eligible('RO'),ontology_fixture.eligible('RA')").fetchone();self.assertEqual(result,(False,True));observations.append({'id':'restored-caller-binding-distinguishes-denial-and-permit','observed':list(result)})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(login_id,json.dumps({'kind':'string','text':'alice'}),int(aliases['staff-outsider'].id),int(staff['typeId'])))
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='alice'
  with psycopg.connect(**params,autocommit=True) as reader:
   for operation,query in [('ownerless',"SELECT ontology_fixture.eligible('RO')"),('count','SELECT count(*) FROM truss.object')]:
    with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState) as failure:reader.execute(query).fetchall()
    self.assertEqual(failure.exception.sqlstate,'55000');self.assertEqual(failure.exception.diag.message_primary,'security facts unavailable');observations.append({'id':'ambiguous-original-caller-refuses-'+operation,'observed':{'sqlState':'55000','message':'security facts unavailable'}})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(login_id,json.dumps({'kind':'string','text':'outsider'}),int(aliases['staff-outsider'].id),int(staff['typeId'])))
  with psycopg.connect(**params,autocommit=True) as reader:
   actual=[r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,['RA','RAB']);observations.append({'id':'unique-original-caller-mapping-restores-visibility','observed':actual})
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='alice'
  with psycopg.connect(**params,autocommit=True) as old_snapshot:
   old_snapshot.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
   old_snapshot.execute('SELECT count(*) FROM pg_class').fetchone() # Establish original snapshot before change.
   isolation=old_snapshot.execute('SHOW transaction_isolation').fetchone()[0];self.assertEqual(isolation,'repeatable read');observations.append({'id':'old-authority-snapshot-established-before-change','observed':isolation})
   self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':False}),int(aliases['AA'].id),int(assignment['typeId'])))
   with self.assertRaises(psycopg.errors.FeatureNotSupported) as failure:old_snapshot.execute('SELECT count(*) FROM truss.object').fetchall()
   self.assertEqual(failure.exception.sqlstate,'0A000');self.assertEqual(failure.exception.diag.message_primary,'security authority profile unavailable');observations.append({'id':'first-protected-read-under-old-snapshot-refuses','observed':{'sqlState':'0A000','message':'security authority profile unavailable'}})
   old_snapshot.rollback()
  with psycopg.connect(**params,autocommit=True) as fresh:
   actual=[r[0] for r in fresh.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,[]);observations.append({'id':'fresh-read-after-committed-authority-change-denies','observed':actual})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':True}),int(aliases['AA'].id),int(assignment['typeId'])))
  with psycopg.connect(**params,autocommit=True) as fresh:
   actual=[r[0] for r in fresh.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,['RA','RAB']);observations.append({'id':'restored-authority-fresh-read-original-vector','observed':actual})
  # Actual graph assignment writer waits through the fixture's buffered release.
  import threading,time
  writer=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self.addCleanup(writer.close)
  writer_pid=writer.execute('SELECT pg_backend_pid()').fetchone()[0];errors=[]
  def revoke_assignment():
   try:writer.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':False}),int(aliases['AA'].id),int(assignment['typeId'])))
   except Exception as exc:errors.append(type(exc).__name__)
  self.admin.execute('BEGIN');self.admin.execute('LOCK TABLE truss.object,truss.edge,truss.type_def,truss.prop_def,truss.rel_def,truss.rel_endpoint IN SHARE MODE')
  thread=threading.Thread(target=revoke_assignment);thread.start()
  try:
   deadline=time.monotonic()+5;waiting=None
   while time.monotonic()<deadline:
    waiting=self.admin.execute("SELECT mode,granted FROM pg_locks WHERE pid=%s AND relation='truss.object'::regclass AND mode='RowExclusiveLock'",(writer_pid,)).fetchone()
    if waiting==('RowExclusiveLock',False):break
    time.sleep(.01)
   self.assertEqual(waiting,('RowExclusiveLock',False));observations.append({'id':'graph-assignment-revoker-native-wait','writerPid':writer_pid,'observed':list(waiting)})
   with psycopg.connect(**params,autocommit=True) as guarded_reader:
    buffered=[r[0] for r in guarded_reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(buffered,['RA','RAB'])
   self.assertTrue(thread.is_alive());observations.append({'id':'buffered-graph-read-released-before-revoker-commit','observed':buffered,'boundary':'fixture records final buffered return before releasing native source locks'})
  finally:self.admin.rollback();thread.join(12)
  self.assertFalse(thread.is_alive());self.assertEqual(errors,[]);observations.append({'id':'graph-assignment-revoker-completes-after-release','observed':'committed'})
  with psycopg.connect(**params,autocommit=True) as fresh:
   actual=[r[0] for r in fresh.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,[]);observations.append({'id':'new-read-after-drained-graph-change-denies','observed':actual})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':True}),int(aliases['AA'].id),int(assignment['typeId'])))
  # Source-table exclusion cannot fence native role authority changes.
  control=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=5000');self.addCleanup(control.close)
  self.admin.execute('BEGIN');self.admin.execute('LOCK TABLE truss.object,truss.edge,truss.type_def,truss.prop_def,truss.rel_def,truss.rel_endpoint IN SHARE MODE')
  try:
   control.execute('ALTER ROLE alice BYPASSRLS')
   held=self.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND mode='ShareLock' AND granted AND relation IN ('truss.object'::regclass,'truss.edge'::regclass,'truss.type_def'::regclass,'truss.prop_def'::regclass,'truss.rel_def'::regclass,'truss.rel_endpoint'::regclass)").fetchone()[0];self.assertEqual(held,6);observations.append({'id':'native-role-change-commits-while-six-source-locks-held','observed':held})
   with psycopg.connect(**params,autocommit=True) as changed_reader:
    flags=changed_reader.execute('SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone();self.assertEqual(flags,(False,True));observations.append({'id':'changed-original-caller-bypass-attribute','observed':list(flags)})
    count=changed_reader.execute('SELECT count(*) FROM truss.object').fetchone()[0];self.assertEqual(count,13);observations.append({'id':'bypass-authority-defeats-source-lock-only-profile','observed':count,'qualification':'deliberate disposable authority-widening counterexample'})
  finally:
   control.execute('ALTER ROLE alice NOBYPASSRLS');self.admin.rollback()
  with psycopg.connect(**params,autocommit=True) as restored_reader:
   actual=[r[0] for r in restored_reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,['RA','RAB']);observations.append({'id':'restored-native-caller-authority-original-vector','observed':actual})
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']).write_text(json.dumps({'packet':packet,'sql':sql,'observations':observations,'publicCreatedIdentities':{alias:{'id':identity.id,'typeId':identity.type_id} for alias,identity in aliases.items()},'scope':'Actual public-created objects/edges, typed native joins to business keys and candidate typed Record/opaque Relationship membership lowering under ordinary native RLS. Private views are real graph projections, not seeded flat tables. Not complete source enrollment, held authority or released public API/security compiler admission.'},indent=2)+'\n')
if __name__=='__main__':
 import unittest;unittest.main()
