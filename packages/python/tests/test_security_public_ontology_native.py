"""Actual public graph ontology fixture; candidate lowering, not admitted security."""
import json,os,subprocess
from pathlib import Path
import psycopg
from truss import Ok
from truss.contracts import TextValue,BooleanValue
from truss.groups import CreateObject,CreateEdge,AuthoredValue,RootlessOwnership,AliasObjectReference,NullOrderKey,GroupSuccess,RequestNone
import test_group_create_native as groups
RECORDS={'Client':{'code':'string'},'Project':{'code':'string'},'Staff':{'code':'string','login':'string'},'Resource':{'code':'string','secret':'string'},'Assignment':{'code':'string','active':'boolean'}}
LINKS={'staff_assignment':('Staff','Assignment'),'assignment_project':('Assignment','Project'),'resource_project':('Resource','Project'),'project_client':('Project','Client')}
class PublicOntologySecurityTests(groups.PublicCreateGroupTests):
 for name in tuple(n for n in dir(groups.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None
 def setUp(self):
  self._security_connections=[]
  super().setUp()
 def _track_owned_connection(self,connection):
  self._security_connections.append(connection)
  self.addCleanup(connection.close)
 def _close_owned_connections(self):
  for connection in reversed(self._security_connections):
   if not connection.closed:connection.close()
 def test_owned_connections_close_before_schema_teardown(self):
  import time
  self.install();self.host.detach();self.admin.commit()
  self.admin.execute('CREATE SCHEMA ontology_fixture;CREATE TABLE ontology_fixture.cleanup_probe(value text)')
  owned=psycopg.connect(self.info.connection_uri,autocommit=True);self._track_owned_connection(owned);pid=owned.execute('SELECT pg_backend_pid()').fetchone()[0];owned.execute('BEGIN');owned.execute('TABLE ontology_fixture.cleanup_probe').fetchall()
  locks=self.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=%s AND relation='ontology_fixture.cleanup_probe'::regclass",(pid,)).fetchone()[0];self.assertGreater(locks,0)
  self._close_owned_connections();self.assertTrue(owned.closed)
  remaining=1;wait_until=time.monotonic()+5
  while time.monotonic()<wait_until:
   remaining=self.admin.execute('SELECT count(*) FROM pg_stat_activity WHERE pid=%s',(pid,)).fetchone()[0]
   if remaining==0:break
   time.sleep(.02)
  self.assertEqual(remaining,0);self.admin.execute("SET lock_timeout='250ms'");self.admin.execute('DROP SCHEMA ontology_fixture CASCADE');self.admin.execute("SET lock_timeout='0'")
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']+'.cleanup.json').write_text(json.dumps({'observations':[{'id':'owned-fixture-transaction-holds-native-schema-lock','observed':locks},{'id':'owned-fixture-close-precedes-schema-drop','observed':{'closed':owned.closed,'remainingBackend':remaining}}],'scope':'Explicit owned fixture connection only; not production caller transaction recovery or unknown-outcome cleanup.'},indent=2)+'\n')
 def tearDown(self):
  self._close_owned_connections()
  self.admin.rollback();self.admin.execute('DROP SCHEMA IF EXISTS relational_fixture CASCADE;DROP SCHEMA IF EXISTS ontology_fixture CASCADE')
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
  for code in ['RA','RB','RAB','RO']:node('Resource',code,secret='raw-'+code)
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
  writer=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(writer)
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
  control=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=5000');self._track_owned_connection(control)
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
  # Exercise the existing installation-wide authority guard's original SQL.
  contracts=Path(__file__).resolve().parents[3]/'docs/helix/02-design/contracts'
  self.admin.execute((contracts/'installation-policy-guard-v0.1.proposal.sql').read_text())
  installation_bytes=self.admin.execute('SELECT installation_id::text FROM truss.catalog_runtime_installation').fetchone()[0].encode();profile_bytes=b'ontology-authority-guard-fixture/0.1'
  self.admin.execute('INSERT INTO truss.policy_generation_guard VALUES(1,%s,%s,1)',(installation_bytes,profile_bytes))
  acquire=(contracts/'installation-policy-guard-acquire-v0.1.proposal.sql').read_text()
  advance=(contracts/'installation-policy-generation-advance-v0.1.proposal.sql').read_text()
  for ordinal in [1,2,3]:advance=advance.replace('$'+str(ordinal),'%s')
  authority_writer=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(authority_writer)
  authority_pid=authority_writer.execute('SELECT pg_backend_pid()').fetchone()[0];authority_errors=[];advanced=[]
  def controlled_role_change():
   try:
    authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();authority_writer.execute('ALTER ROLE alice BYPASSRLS');rows=authority_writer.execute(advance,(installation_bytes,profile_bytes,1)).fetchall()
    if rows!=[('1',installation_bytes.hex(),profile_bytes.hex(),'2')]:raise ValueError('Original generation advance refused')
    advanced.extend(rows);authority_writer.execute('COMMIT')
   except Exception as exc:authority_errors.append(type(exc).__name__);authority_writer.rollback()
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE').fetchone();guard_cursor=self.admin.execute(acquire);captured=guard_cursor.fetchall();self.assertEqual(captured,[('1',installation_bytes.hex(),profile_bytes.hex(),'1')]);observations.append({'id':'original-proposed-guard-acquisition','observed':[list(row) for row in captured]})
  decoder_packet={'columns':[{'name':column.name,'typeOid':str(column.type_code)} for column in guard_cursor.description],'rows':[list(row) for row in captured],'expected':{'installationIdentityHex':installation_bytes.hex(),'policyProfileHex':profile_bytes.hex()}}
  decoder=subprocess.run(['/opt/homebrew/bin/bun',str(Path(__file__).resolve().parents[3]/'tests/fixtures/security-authority-guard-decode.ts')],input=json.dumps(decoder_packet),text=True,capture_output=True,timeout=30);self.assertEqual(decoder.returncode,0,decoder.stderr);decoded=json.loads(decoder.stdout);self.assertEqual(decoded['generation'],'1');observations.append({'id':'actual-native-guard-descriptors-and-row-decoded','input':decoder_packet,'observed':decoded,'qualification':'local decoding, not a lease'})
  holder_pid=self.admin.execute('SELECT pg_backend_pid()').fetchone()[0];authority_thread=threading.Thread(target=controlled_role_change);authority_thread.start()
  try:
   deadline=time.monotonic()+5;blockers=[]
   while time.monotonic()<deadline:
    blockers=self.admin.execute('SELECT pg_blocking_pids(%s)',(authority_pid,)).fetchone()[0]
    if holder_pid in blockers:break
    time.sleep(.01)
   self.assertIn(holder_pid,blockers);observations.append({'id':'participating-native-role-changer-waits-on-authority-guard','blockerPid':holder_pid,'observed':blockers})
   with psycopg.connect(**params,autocommit=True) as admitted_fixture_reader:
    actual=[r[0] for r in admitted_fixture_reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,['RA','RAB']);self.assertTrue(authority_thread.is_alive());observations.append({'id':'guarded-buffered-result-before-authority-change','observed':actual})
  finally:self.admin.rollback();authority_thread.join(12)
  self.assertFalse(authority_thread.is_alive());self.assertEqual(authority_errors,[]);self.assertEqual(advanced,[('1',installation_bytes.hex(),profile_bytes.hex(),'2')]);observations.append({'id':'controlled-role-effect-and-generation-advance-commit','observed':[list(row) for row in advanced]})
  fresh_guard=self.admin.execute(acquire).fetchall();self.assertEqual(fresh_guard,[('1',installation_bytes.hex(),profile_bytes.hex(),'2')]);observations.append({'id':'next-authority-observation-sees-new-generation','observed':[list(row) for row in fresh_guard]})
  flags=self.admin.execute("SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname='alice'").fetchone();self.assertEqual(flags,(False,True));observations.append({'id':'new-generation-requires-original-caller-bypass-exclusion','observed':list(flags),'qualification':'new generation is not authorization'})
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();authority_writer.execute('ALTER ROLE alice NOBYPASSRLS');restored_generation=authority_writer.execute(advance,(installation_bytes,profile_bytes,2)).fetchall();self.assertEqual(restored_generation,[('1',installation_bytes.hex(),profile_bytes.hex(),'3')]);authority_writer.execute('COMMIT');observations.append({'id':'controlled-restoration-preserves-generation-continuity','observed':[list(row) for row in restored_generation]})
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();authority_writer.execute('ALTER ROLE alice BYPASSRLS')
  stale=authority_writer.execute(advance,(installation_bytes,profile_bytes,2)).fetchall();self.assertEqual(stale,[]);observations.append({'id':'stale-expected-generation-refuses-advance','observed':stale});authority_writer.rollback()
  flags=self.admin.execute("SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname='alice'").fetchone();generation=self.admin.execute('SELECT generation::text FROM truss.policy_generation_guard WHERE singleton=1').fetchone()[0];self.assertEqual(flags,(False,False));self.assertEqual(generation,'3');observations.append({'id':'failed-controlled-delta-rolls-back-role-and-generation','observed':{'flags':list(flags),'generation':generation}})
  for invalid_identity,invalid_profile,kind in [(b'foreign-installation',profile_bytes,'installation'),(installation_bytes,b'foreign-profile','profile')]:
   authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone()
   rows=authority_writer.execute(advance,(invalid_identity,invalid_profile,3)).fetchall();self.assertEqual(rows,[]);authority_writer.rollback();observations.append({'id':'foreign-authority-'+kind+'-refuses-generation-advance','observed':rows})
  with psycopg.connect(**params,autocommit=True) as ordinary:
   with self.assertRaises(psycopg.errors.InsufficientPrivilege) as failure:ordinary.execute('UPDATE truss.policy_generation_guard SET generation=1')
   self.assertEqual(failure.exception.sqlstate,'42501');observations.append({'id':'ordinary-authority-generation-reset-denied','observed':'42501'})
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();authority_writer.execute('UPDATE truss.policy_generation_guard SET generation=9223372036854775807 WHERE singleton=1');authority_writer.execute('ALTER ROLE alice BYPASSRLS')
  exhausted=authority_writer.execute(advance,(installation_bytes,profile_bytes,9223372036854775807)).fetchall();self.assertEqual(exhausted,[]);observations.append({'id':'authority-generation-maximum-refuses-instead-of-wrap','observed':exhausted})
  maximum=authority_writer.execute('SELECT generation::text FROM truss.policy_generation_guard WHERE singleton=1').fetchone()[0];self.assertEqual(maximum,'9223372036854775807');observations.append({'id':'maximum-generation-remains-exact-before-rollback','observed':maximum});authority_writer.rollback()
  flags=self.admin.execute("SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname='alice'").fetchone();generation=self.admin.execute('SELECT generation::text FROM truss.policy_generation_guard WHERE singleton=1').fetchone()[0];self.assertEqual(flags,(False,False));self.assertEqual(generation,'3');observations.append({'id':'exhausted-authority-delta-rolls-back-role-and-generation','observed':{'flags':list(flags),'generation':generation}})
  # Losing the original coordinator cannot authorize its buffered result.
  coordinator=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(coordinator)
  coordinator_pid=coordinator.execute('SELECT pg_backend_pid()').fetchone()[0];coordinator.execute('BEGIN');coordinator.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE').fetchone();held_generation=coordinator.execute(acquire).fetchall();self.assertEqual(held_generation,[('1',installation_bytes.hex(),profile_bytes.hex(),'3')])
  data_reader=psycopg.connect(**params,autocommit=True);self._track_owned_connection(data_reader);data_reader.execute('BEGIN');data_reader.execute("CREATE TEMP TABLE prior_data_work(value text);INSERT INTO prior_data_work VALUES('kept')")
  pending_buffer=[r[0] for r in data_reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))]
  self.assertEqual(pending_buffer,['RA','RAB']);lost_errors=[];lost_advance=[]
  def change_after_coordinator_loss():
   try:
    authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();authority_writer.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':False}),int(aliases['AA'].id),int(assignment['typeId'])))
    rows=authority_writer.execute(advance,(installation_bytes,profile_bytes,3)).fetchall()
    if rows!=[('1',installation_bytes.hex(),profile_bytes.hex(),'4')]:raise ValueError('Original generation advance refused')
    lost_advance.extend(rows);authority_writer.execute('COMMIT')
   except Exception as exc:lost_errors.append(type(exc).__name__);authority_writer.rollback()
  loss_thread=threading.Thread(target=change_after_coordinator_loss);loss_thread.start()
  try:
   deadline=time.monotonic()+5;blockers=[]
   while time.monotonic()<deadline:
    blockers=self.admin.execute('SELECT pg_blocking_pids(%s)',(authority_pid,)).fetchone()[0]
    if coordinator_pid in blockers:break
    time.sleep(.01)
   self.assertIn(coordinator_pid,blockers);observations.append({'id':'authority-writer-waits-on-original-coordinator','observed':blockers,'coordinatorPid':coordinator_pid})
   successful_probe=coordinator.execute('SELECT 1').fetchone();self.assertEqual(successful_probe,(1,));observations.append({'id':'coordinator-positive-probe-before-native-loss','observed':list(successful_probe),'qualification':'positive probe alone does not cover subsequent release'})
   stale_buffer=list(pending_buffer)
   terminated=self.admin.execute('SELECT pg_terminate_backend(%s)',(coordinator_pid,)).fetchone()[0];self.assertIs(terminated,True);observations.append({'id':'owned-original-coordinator-terminated','observed':True})
   with self.assertRaises(psycopg.OperationalError) as loss:coordinator.execute('SELECT 1')
   observations.append({'id':'original-coordinator-native-liveness-probe-fails','observed':{'kind':type(loss.exception).__name__,'sqlState':loss.exception.sqlstate}})
  finally:
   coordinator.close();loss_thread.join(12)
  self.assertFalse(loss_thread.is_alive());self.assertEqual(lost_errors,[]);self.assertEqual(lost_advance,[('1',installation_bytes.hex(),profile_bytes.hex(),'4')]);observations.append({'id':'authority-change-commits-after-native-coordinator-loss','observed':[list(row) for row in lost_advance]})
  self.assertEqual(data_reader.info.transaction_status,psycopg.pq.TransactionStatus.INTRANS);prior=data_reader.execute('TABLE prior_data_work').fetchall();self.assertEqual(prior,[('kept',)]);observations.append({'id':'coordinator-loss-preserves-original-data-transaction-work','observed':[list(row) for row in prior]});data_reader.rollback()
  pending_buffer=[];observations.append({'id':'lost-coordinator-buffer-withheld-by-fixture','observed':pending_buffer,'qualification':'explicit fixture release arbitration, not a production lease'})
  with psycopg.connect(**params,autocommit=True) as fresh:
   actual=[r[0] for r in fresh.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,[]);observations.append({'id':'new-read-after-coordinator-loss-observes-revocation','observed':actual})
   self.assertEqual(stale_buffer,['RA','RAB']);self.assertNotEqual(stale_buffer,actual);observations.append({'id':'positive-liveness-probe-retains-stale-buffer-counterexample','observed':{'bufferBeforeLoss':stale_buffer,'freshAfterRevocation':actual},'qualification':'would leak if published using only the earlier positive probe; actual fixture withheld it'})
  # Same logical Record/Relationship condition over independent raw tables.
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();authority_writer.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':True}),int(aliases['AA'].id),int(assignment['typeId'])));rows=authority_writer.execute(advance,(installation_bytes,profile_bytes,4)).fetchall();self.assertEqual(rows,[('1',installation_bytes.hex(),profile_bytes.hex(),'5')]);authority_writer.execute('COMMIT')
  # Durable outstanding publication survives native coordinator death.
  self.admin.execute((contracts/'installation-publication-claim-v0.2.tombstone.proposal.sql').read_text())
  def claim_sql(name,count):
   source=(contracts/name).read_text()
   for ordinal in range(1,count+1):source=source.replace('$'+str(ordinal),'%s')
   return source
  register=claim_sql('installation-publication-claim-register-v0.2.tombstone.proposal.sql',4)
  settle=claim_sql('installation-publication-claim-settle-v0.2.tombstone.proposal.sql',4)
  claim_advance=claim_sql('installation-policy-generation-advance-v0.3.tombstone.proposal.sql',3)
  operation_bytes=b'fixture-original-publication-1'
  claim_coordinator=psycopg.connect(self.info.connection_uri,autocommit=True);self._track_owned_connection(claim_coordinator)
  claim_pid=claim_coordinator.execute('SELECT pg_backend_pid()').fetchone()[0]
  claim_coordinator.execute('BEGIN');claim_coordinator.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');claim_coordinator.execute(acquire).fetchall()
  registered=claim_coordinator.execute(register,(operation_bytes,installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(registered,[(operation_bytes.hex(),)]);claim_coordinator.execute('COMMIT')
  observations.append({'id':'durable-publication-claim-commit-confirmed','observed':registered})
  self.assertIs(self.admin.execute('SELECT pg_terminate_backend(%s)',(claim_pid,)).fetchone()[0],True)
  outstanding=self.admin.execute("SELECT pg_catalog.encode(operation_identity_bytes,'hex'),generation::text FROM truss.policy_publication_claim").fetchall();self.assertEqual(outstanding,[(operation_bytes.hex(),'5')]);observations.append({'id':'publication-claim-survives-native-coordinator-loss','observed':outstanding})
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone()
  blocked=authority_writer.execute(claim_advance,(installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(blocked,[]);authority_writer.execute('ROLLBACK');observations.append({'id':'outstanding-publication-refuses-participating-authority-advance','observed':blocked})
  for wrong in [(b'foreign-operation',installation_bytes,profile_bytes,5),(operation_bytes,b'foreign-installation',profile_bytes,5),(operation_bytes,installation_bytes,b'foreign-profile',5),(operation_bytes,installation_bytes,profile_bytes,4)]:
   self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();deleted=self.admin.execute(settle,wrong).fetchall();self.assertEqual(deleted,[]);self.admin.execute('ROLLBACK')
  observations.append({'id':'publication-claim-original-settlement-mismatch-refuses','observed':'four mismatches preserve original claim'})
  with psycopg.connect(**params,autocommit=True) as ordinary:
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):ordinary.execute('DELETE FROM truss.policy_publication_claim')
  observations.append({'id':'ordinary-publication-claim-reset-refuses','observed':'42501'})
  second_operation=b'fixture-original-publication-2'
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();second_registered=self.admin.execute(register,(second_operation,installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(second_registered,[(second_operation.hex(),)]);self.admin.execute('COMMIT');observations.append({'id':'overlapping-publication-claims-independently-register','observed':second_registered})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall()
  with self.assertRaises(psycopg.errors.UniqueViolation) as duplicate:self.admin.execute(register,(second_operation,installation_bytes,profile_bytes,5)).fetchall()
  self.assertEqual(duplicate.exception.sqlstate,'23505');self.admin.execute('ROLLBACK');observations.append({'id':'duplicate-original-publication-claim-refuses-replacement','observed':'23505'})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();stale_registered=self.admin.execute(register,(b'stale-publication',installation_bytes,profile_bytes,4)).fetchall();self.assertEqual(stale_registered,[]);self.admin.execute('ROLLBACK');observations.append({'id':'stale-publication-generation-cannot-register','observed':stale_registered})
  # Fixture establishes withheld completion; no production sink/issuer proof.
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();deleted=self.admin.execute(settle,(operation_bytes,installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(deleted,[(operation_bytes.hex(),)]);self.admin.execute('COMMIT');observations.append({'id':'original-publication-claim-settles-after-fixture-withholding','observed':deleted,'qualification':'fixture completion premise only'})
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();still_blocked=authority_writer.execute(claim_advance,(installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(still_blocked,[]);authority_writer.execute('ROLLBACK');observations.append({'id':'settling-one-publication-preserves-other-operation-exclusion','observed':still_blocked})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.assertEqual(self.admin.execute(settle,(second_operation,installation_bytes,profile_bytes,5)).fetchall(),[(second_operation.hex(),)]);self.admin.execute('ROLLBACK')
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim WHERE NOT settled').fetchone(),(1,));observations.append({'id':'rolled-back-publication-settlement-retains-claim','observed':1})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.assertEqual(self.admin.execute(settle,(second_operation,installation_bytes,profile_bytes,5)).fetchall(),[(second_operation.hex(),)]);self.admin.execute('COMMIT')
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();advanced=authority_writer.execute(claim_advance,(installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(advanced,[('1',installation_bytes.hex(),profile_bytes.hex(),'6')]);authority_writer.execute('ROLLBACK');observations.append({'id':'settled-publication-allows-participating-advance','observed':advanced,'qualification':'rolled back to preserve generation5; no production authority-delta proof'})
  retained=self.admin.execute("SELECT pg_catalog.encode(operation_identity_bytes,'hex'),generation::text,settled FROM truss.policy_publication_claim ORDER BY operation_identity_bytes").fetchall();self.assertEqual(retained,[(operation_bytes.hex(),'5',True),(second_operation.hex(),'5',True)]);observations.append({'id':'settled-publication-identities-retain-native-tombstones','observed':retained})
  for replay in [operation_bytes,second_operation]:
   self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall()
   with self.assertRaises(psycopg.errors.UniqueViolation) as duplicate:self.admin.execute(register,(replay,installation_bytes,profile_bytes,5)).fetchall()
   self.assertEqual(duplicate.exception.sqlstate,'23505');self.admin.execute('ROLLBACK')
  observations.append({'id':'settled-original-operation-token-replay-refuses','observed':'two23505 refusals; no replacement claims'})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();repeated_settlement=self.admin.execute(settle,(operation_bytes,installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(repeated_settlement,[]);self.admin.execute('ROLLBACK');observations.append({'id':'settled-original-operation-cannot-settle-twice','observed':repeated_settlement})
  # A pending registration SHARE scope drains before writer's fresh claim check.
  pending_operation=b'fixture-pending-publication'
  pending_owner=psycopg.connect(self.info.connection_uri,autocommit=True);self._track_owned_connection(pending_owner)
  pending_pid=pending_owner.execute('SELECT pg_backend_pid()').fetchone()[0]
  pending_owner.execute('BEGIN');pending_owner.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');pending_owner.execute(acquire).fetchall();self.assertEqual(pending_owner.execute(register,(pending_operation,installation_bytes,profile_bytes,5)).fetchall(),[(pending_operation.hex(),)])
  pending_errors=[];pending_advances=[]
  def advance_after_pending_registration():
   try:
    authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();pending_advances.extend(authority_writer.execute(claim_advance,(installation_bytes,profile_bytes,5)).fetchall());authority_writer.execute('ROLLBACK')
   except BaseException as error:pending_errors.append(type(error).__name__);authority_writer.execute('ROLLBACK')
  pending_thread=threading.Thread(target=advance_after_pending_registration);pending_thread.start()
  try:
   blockers=[];wait_until=time.monotonic()+8
   while time.monotonic()<wait_until:
    blockers=self.admin.execute('SELECT pg_blocking_pids(%s)',(authority_pid,)).fetchone()[0]
    if pending_pid in blockers:break
    time.sleep(.02)
   self.assertIn(pending_pid,blockers);observations.append({'id':'authority-writer-drains-pending-publication-registration','observed':blockers})
   pending_owner.execute('COMMIT')
  finally:
   pending_owner.rollback();pending_thread.join(12)
  self.assertFalse(pending_thread.is_alive());self.assertEqual(pending_errors,[]);self.assertEqual(pending_advances,[]);observations.append({'id':'fresh-post-drain-authority-check-sees-committed-claim','observed':pending_advances})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.assertEqual(self.admin.execute(settle,(pending_operation,installation_bytes,profile_bytes,5)).fetchall(),[(pending_operation.hex(),)]);self.admin.execute('COMMIT')
  # Capacity source: retained tombstones count; serialization precedes fresh count.
  capacity_lock=(contracts/'installation-publication-claim-capacity-lock-v0.1.proposal.sql').read_text()
  capacity_register=(contracts/'installation-publication-claim-register-v0.3.capacity.proposal.sql').read_text()
  for ordinal in range(1,6):capacity_register=capacity_register.replace('$'+str(ordinal),'%(p'+str(ordinal)+')s')
  def capacity_execute(connection,parameters):return connection.execute(capacity_register,{'p'+str(i):value for i,value in enumerate(parameters,1)})
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(3,))
  for cap,token in [(3,b'full-registry'),(0,b'zero-capacity'),(-1,b'negative-capacity'),(1048577,b'oversized-capacity'),(4,b'x'*2049)]:
   self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.admin.execute(capacity_lock);refused=capacity_execute(self.admin,(token,installation_bytes,profile_bytes,5,cap)).fetchall();self.assertEqual(refused,[]);self.admin.execute('ROLLBACK')
  observations.append({'id':'publication-capacity-and-token-bounds-refuse-before-registration','observed':'five zero-row refusals; retained tombstones preserved'})
  capacity_owner=psycopg.connect(self.info.connection_uri,autocommit=True);self._track_owned_connection(capacity_owner);capacity_pid=capacity_owner.execute('SELECT pg_backend_pid()').fetchone()[0]
  capacity_waiter=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(capacity_waiter);capacity_waiter_pid=capacity_waiter.execute('SELECT pg_backend_pid()').fetchone()[0]
  capacity_owner.execute('BEGIN');capacity_owner.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');capacity_owner.execute(acquire).fetchall();capacity_owner.execute(capacity_lock);last_registered=capacity_execute(capacity_owner,(b'last-capacity-slot',installation_bytes,profile_bytes,5,4)).fetchall();self.assertEqual(last_registered,[(b'last-capacity-slot'.hex(),)])
  capacity_errors=[];capacity_rows=[]
  def register_after_capacity_drain():
   try:
    capacity_waiter.execute('BEGIN');capacity_waiter.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');capacity_waiter.execute(acquire).fetchall();capacity_waiter.execute(capacity_lock);capacity_rows.extend(capacity_execute(capacity_waiter,(b'racing-capacity-slot',installation_bytes,profile_bytes,5,4)).fetchall());capacity_waiter.execute('ROLLBACK')
   except BaseException as error:capacity_errors.append(type(error).__name__);capacity_waiter.execute('ROLLBACK')
  capacity_thread=threading.Thread(target=register_after_capacity_drain);capacity_thread.start()
  try:
   blockers=[];wait_until=time.monotonic()+8
   while time.monotonic()<wait_until:
    blockers=self.admin.execute('SELECT pg_blocking_pids(%s)',(capacity_waiter_pid,)).fetchone()[0]
    if capacity_pid in blockers:break
    time.sleep(.02)
   self.assertIn(capacity_pid,blockers);observations.append({'id':'publication-capacity-registrants-native-serialization','observed':blockers});capacity_owner.execute('COMMIT')
  finally:capacity_owner.rollback();capacity_thread.join(12)
  self.assertFalse(capacity_thread.is_alive());self.assertEqual(capacity_errors,[]);self.assertEqual(capacity_rows,[]);self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(4,));observations.append({'id':'fresh-capacity-check-refuses-racing-last-slot','observed':{'rows':capacity_rows,'retained':4}})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.assertEqual(self.admin.execute(settle,(b'last-capacity-slot',installation_bytes,profile_bytes,5)).fetchall(),[(b'last-capacity-slot'.hex(),)]);self.admin.execute('COMMIT')
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.admin.execute(capacity_lock);self.assertEqual(capacity_execute(self.admin,(b'after-capacity-settlement',installation_bytes,profile_bytes,5,4)).fetchall(),[]);self.admin.execute('ROLLBACK');observations.append({'id':'settlement-cannot-reopen-retained-token-capacity','observed':'zero rows after settled fourth identity'})
  # Failed capacity acquisition rolls back only its savepoint, not caller work.
  for interruption in ['timeout','cancel']:
   capacity_owner.execute('BEGIN');capacity_owner.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');capacity_owner.execute(acquire).fetchall();capacity_owner.execute(capacity_lock)
   interrupted=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(interrupted);interrupted_pid=interrupted.execute('SELECT pg_backend_pid()').fetchone()[0]
   interrupted.execute('BEGIN');interrupted.execute('CREATE TEMP TABLE prior_capacity_work(value text)');interrupted.execute("INSERT INTO prior_capacity_work VALUES('kept')");interrupted.execute('SAVEPOINT capacity_attempt');interrupted.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');interrupted.execute(acquire).fetchall()
   interruption_states=[];interruption_thread=None
   try:
    if interruption=='timeout':
     interrupted.execute("SET LOCAL lock_timeout='150ms'")
     with self.assertRaises(psycopg.errors.LockNotAvailable) as error:interrupted.execute(capacity_lock)
     interruption_states.append(error.exception.sqlstate)
    else:
     def wait_for_capacity_lock():
      try:interrupted.execute(capacity_lock);interruption_states.append('unexpected-success')
      except psycopg.Error as error:interruption_states.append(error.sqlstate)
     interruption_thread=threading.Thread(target=wait_for_capacity_lock);interruption_thread.start();blockers=[];wait_until=time.monotonic()+8
     while time.monotonic()<wait_until:
      blockers=self.admin.execute('SELECT pg_blocking_pids(%s)',(interrupted_pid,)).fetchone()[0]
      if capacity_pid in blockers:break
      time.sleep(.02)
     self.assertIn(capacity_pid,blockers);self.assertIs(self.admin.execute('SELECT pg_cancel_backend(%s)',(interrupted_pid,)).fetchone()[0],True);interruption_thread.join(12);self.assertFalse(interruption_thread.is_alive())
    self.assertEqual(interruption_states,['55P03' if interruption=='timeout' else '57014']);self.assertEqual(interrupted.info.transaction_status,psycopg.pq.TransactionStatus.INERROR);observations.append({'id':'publication-capacity-'+interruption+'-native-refusal','observed':interruption_states})
    interrupted.execute('ROLLBACK TO SAVEPOINT capacity_attempt');self.assertEqual(interrupted.info.transaction_status,psycopg.pq.TransactionStatus.INTRANS);self.assertEqual(interrupted.execute('TABLE prior_capacity_work').fetchall(),[('kept',)])
    locks=self.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=%s AND relation IN ('truss.schema_head'::regclass,'truss.policy_generation_guard'::regclass,'truss.policy_publication_claim'::regclass)",(interrupted_pid,)).fetchone()[0];self.assertEqual(locks,0);self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(4,));observations.append({'id':'publication-capacity-'+interruption+'-savepoint-preserves-prior-work','observed':{'partialLocks':locks,'retainedClaims':4,'priorWork':'kept'}})
   finally:
    capacity_owner.rollback()
    if interruption_thread is not None:interruption_thread.join(12)
    interrupted.rollback();interrupted.close()
  # Source capacity from original protected native profile, not a fifth argument.
  self.admin.execute((contracts/'installation-publication-capacity-profile-v0.1.proposal.sql').read_text());self.admin.execute('INSERT INTO truss.policy_publication_capacity VALUES(1,%s,%s,6)',(installation_bytes,profile_bytes))
  profile_register=(contracts/'installation-publication-claim-register-v0.4.profile.proposal.sql').read_text()
  for ordinal in range(1,5):profile_register=profile_register.replace('$'+str(ordinal),'%(p'+str(ordinal)+')s')
  def profile_execute(connection,parameters):return connection.execute(profile_register,{'p'+str(i):value for i,value in enumerate(parameters,1)})
  for mutation in ["DELETE FROM truss.policy_publication_capacity","UPDATE truss.policy_publication_capacity SET installation_identity_bytes='foreign'::bytea","UPDATE truss.policy_publication_capacity SET policy_profile_bytes='foreign'::bytea","UPDATE truss.policy_publication_capacity SET max_retained=4"]:
   self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();self.admin.execute(mutation);self.admin.execute(capacity_lock);refused=profile_execute(self.admin,(b'profile-bound-operation',installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(refused,[]);self.admin.execute('ROLLBACK')
  observations.append({'id':'native-capacity-profile-missing-mismatched-full-refuses','observed':'four zero-row refusals; fixture mutations rolled back'})
  with psycopg.connect(**params,autocommit=True) as ordinary:
   with self.assertRaises(psycopg.errors.InsufficientPrivilege) as failure:ordinary.execute('UPDATE truss.policy_publication_capacity SET max_retained=100')
   self.assertEqual(failure.exception.sqlstate,'42501')
  observations.append({'id':'ordinary-native-capacity-profile-change-refuses','observed':'42501'})
  from security_commit_loss_proxy import CommitResponseDropProxy
  commit_proxy=CommitResponseDropProxy(psycopg.conninfo.conninfo_to_dict(self.info.connection_uri));self.addCleanup(commit_proxy.close)
  uncertain_owner=psycopg.connect(self.info.connection_uri,host='127.0.0.1',port=commit_proxy.port,sslmode='disable',gssencmode='disable',autocommit=True);self._track_owned_connection(uncertain_owner)
  uncertain_owner.execute('BEGIN');uncertain_owner.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');uncertain_owner.execute(acquire).fetchall();uncertain_owner.execute(capacity_lock);self.assertEqual(profile_execute(uncertain_owner,(b'original-commit-ack-loss',installation_bytes,profile_bytes,5)).fetchall(),[(b'original-commit-ack-loss'.hex(),)]);commit_proxy.armed.set()
  with self.assertRaises(psycopg.OperationalError) as ack_loss:uncertain_owner.execute('COMMIT')
  self.assertIsNone(ack_loss.exception.sqlstate);self.assertTrue(commit_proxy.dropped.wait(2));commit_proxy.close();self.assertEqual(commit_proxy.errors,[]);observations.append({'id':'original-registration-native-commit-response-dropped','observed':{'nativeCommand':'COMMIT','sqlState':ack_loss.exception.sqlstate},'qualification':'stock driver transport failure; no manufactured native SQLSTATE'})
  observe_claim=claim_sql('installation-publication-claim-observe-v0.1.proposal.sql',1)
  def decode_native_claim(token,settled=None):
   cursor=self.admin.execute(observe_claim,(token,));native_rows=cursor.fetchall()
   native_packet={'columns':[{'name':c.name,'typeOid':str(c.type_code)} for c in cursor.description],'rows':[list(row) for row in native_rows],'expected':{'operationIdentityHex':token.hex(),'installationIdentityHex':installation_bytes.hex(),'policyProfileHex':profile_bytes.hex(),'generation':'5'}}
   runner=str(Path(__file__).resolve().parents[3]/'tests/fixtures/security-publication-claim-decode.ts')
   decoded=subprocess.run(['/opt/homebrew/bin/bun',runner],input=json.dumps(native_packet),text=True,capture_output=True,timeout=30);self.assertEqual(decoded.returncode,0,decoded.stderr);value=json.loads(decoded.stdout)
   self.assertEqual(value,{'state':'not-observed'} if settled is None else {'state':'observed',**native_packet['expected'],'settled':settled})
   wrong=json.loads(json.dumps(native_packet));wrong['expected']['operationIdentityHex']='ff'
   if settled is not None:self.assertNotEqual(subprocess.run(['/opt/homebrew/bin/bun',runner],input=json.dumps(wrong),text=True,capture_output=True,timeout=30).returncode,0)
   return native_packet,value
  # No re-insertion/disclosure: drain original registrants and freshly reconcile.
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone()
  reconciled=self.admin.execute("SELECT pg_catalog.encode(installation_identity_bytes,'hex'),pg_catalog.encode(policy_profile_bytes,'hex'),generation::text,settled FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s",(b'original-commit-ack-loss',)).fetchall();self.assertEqual(reconciled,[(installation_bytes.hex(),profile_bytes.hex(),'5',False)]);native_packet,claim_decoded=decode_native_claim(b'original-commit-ack-loss',False);absent_packet,absent_decoded=decode_native_claim(b'never-registered-original');self.admin.execute('COMMIT');observations.append({'id':'lost-registration-ack-reconciles-exact-original-durable-claim','observed':reconciled});observations.append({'id':'native-original-claim-recovery-carriers-decode','input':native_packet,'observed':claim_decoded});observations.append({'id':'native-missing-original-claim-is-only-not-observed','input':absent_packet,'observed':absent_decoded})
  # Fixture ledger dispatched no data query; conclusively withheld, then settle.
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.assertEqual(self.admin.execute(settle,(b'original-commit-ack-loss',installation_bytes,profile_bytes,5)).fetchall(),[(b'original-commit-ack-loss'.hex(),)]);self.admin.execute('COMMIT')
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();settled_packet,settled_decoded=decode_native_claim(b'original-commit-ack-loss',True);self.admin.execute('COMMIT');observations.append({'id':'native-original-settled-claim-recovery-carriers-decode','input':settled_packet,'observed':settled_decoded})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.admin.execute(capacity_lock)
  with self.assertRaises(psycopg.errors.UniqueViolation) as replay:profile_execute(self.admin,(b'original-commit-ack-loss',installation_bytes,profile_bytes,5)).fetchall()
  self.assertEqual(replay.exception.sqlstate,'23505');self.admin.execute('ROLLBACK');observations.append({'id':'lost-registration-ack-never-replaced-original-token','observed':'original settled tombstone refuses23505'})
  publication_owner=psycopg.connect(self.info.connection_uri,autocommit=True);self._track_owned_connection(publication_owner);publication_pid=publication_owner.execute('SELECT pg_backend_pid()').fetchone()[0]
  for failure_mode in ['explicit_rollback','native_failure']:
   recovery_thread=None;recovery_rows=[];recovery_errors=[]
   publication_owner.execute('BEGIN');publication_owner.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');publication_owner.execute(acquire).fetchall();publication_owner.execute(capacity_lock)
   try:
    pending_registration=profile_execute(publication_owner,(b'profile-bound-operation',installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(pending_registration,[(b'profile-bound-operation'.hex(),)])
    self.assertEqual(publication_owner.execute('SELECT settled FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s',(b'profile-bound-operation',)).fetchone(),(False,));self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s',(b'profile-bound-operation',)).fetchone(),(0,))
    if failure_mode=='explicit_rollback':
     recovery_reader=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(recovery_reader);recovery_pid=recovery_reader.execute('SELECT pg_backend_pid()').fetchone()[0]
     def recover_after_original_drain():
      try:
       recovery_reader.execute('BEGIN');recovery_reader.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');recovery_reader.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();recovery_rows.extend(recovery_reader.execute(observe_claim,(b'profile-bound-operation',)).fetchall());recovery_reader.execute('COMMIT')
      except BaseException as error:recovery_errors.append(type(error).__name__);recovery_reader.rollback()
     recovery_thread=threading.Thread(target=recover_after_original_drain);recovery_thread.start();blockers=[];wait_until=time.monotonic()+8
     while time.monotonic()<wait_until:
      blockers=self.admin.execute('SELECT pg_blocking_pids(%s)',(recovery_pid,)).fetchone()[0]
      if publication_pid in blockers:break
      time.sleep(.02)
     self.assertIn(publication_pid,blockers);observations.append({'id':'original-claim-recovery-drains-invisible-pending-registration','observed':{'blockers':blockers,'unguardedVisibleRows':0}})
    if failure_mode=='native_failure':
     with self.assertRaises(psycopg.errors.DivisionByZero) as error:publication_owner.execute('SELECT 1/0')
     self.assertEqual(error.exception.sqlstate,'22012');self.assertEqual(publication_owner.info.transaction_status,psycopg.pq.TransactionStatus.INERROR)
   finally:
    publication_owner.rollback()
    if recovery_thread is not None:recovery_thread.join(12)
   if recovery_thread is not None:
    self.assertFalse(recovery_thread.is_alive());self.assertEqual(recovery_errors,[]);self.assertEqual(recovery_rows,[]);observations.append({'id':'fresh-original-claim-recovery-after-drained-rollback-is-not-observed','observed':recovery_rows,'qualification':'native absence after known rollback; decoder still supplies no issuer/abort proof'})
   self.assertEqual(publication_owner.info.transaction_status,psycopg.pq.TransactionStatus.IDLE);self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s',(b'profile-bound-operation',)).fetchone(),(0,));self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(5,));observations.append({'id':'profile-registration-'+failure_mode+'-preserves-capacity-and-original-token','observed':{'retained':5,'originalTokenRows':0,'commit':'not-published'},'qualification':'confirmed rollback only; no unknown-commit retry'})
  publication_owner.execute('BEGIN');publication_owner.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');publication_owner.execute(acquire).fetchall();publication_owner.execute(capacity_lock);profile_registered=profile_execute(publication_owner,(b'profile-bound-operation',installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(profile_registered,[(b'profile-bound-operation'.hex(),)]);publication_owner.execute('COMMIT');observations.append({'id':'native-profile-capacity-registers-original-next-slot','observed':profile_registered})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.admin.execute(capacity_lock);refused=profile_execute(self.admin,(b'profile-bound-overflow',installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(refused,[]);self.admin.execute('ROLLBACK');observations.append({'id':'native-profile-capacity-exhaustion-refuses','observed':refused})
  read_params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);read_params['user']='alice'
  def protected_codes():
   with psycopg.connect(**read_params,autocommit=True) as reader:return [r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))]
  real_buffer=protected_codes();self.assertEqual(real_buffer,['RA','RAB']);observations.append({'id':'durable-registered-operation-buffers-real-protected-read','observed':list(real_buffer)})
  self.assertIs(self.admin.execute('SELECT pg_terminate_backend(%s)',(publication_pid,)).fetchone()[0],True)
  with self.assertRaises(psycopg.OperationalError):publication_owner.execute('SELECT 1')
  self.assertEqual(self.admin.execute('SELECT settled FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s',(b'profile-bound-operation',)).fetchone(),(False,));observations.append({'id':'real-protected-buffer-original-coordinator-loss-retains-claim','observed':'unsettled'})
  def participating_assignment_change(active,expected_generation,fault=None):
   authority_writer.execute('BEGIN')
   try:
    authority_writer.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone()
    if authority_writer.execute('SELECT EXISTS(SELECT 1 FROM truss.policy_publication_claim WHERE NOT settled)').fetchone()[0]:authority_writer.execute('ROLLBACK');return 'refused'
    authority_writer.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':active}),int(aliases['AA'].id),int(assignment['typeId'])))
    if fault=='after_effects':
     self.assertEqual(authority_writer.execute('SELECT props->%s FROM truss.object WHERE id=%s AND type_id=%s',(active_id,int(aliases['AA'].id),int(assignment['typeId']))).fetchone(),({'kind':'boolean','value':False},));authority_writer.execute('SELECT 1/0')
    advanced=authority_writer.execute(claim_advance,(installation_bytes,profile_bytes,expected_generation)).fetchall();self.assertEqual(advanced,[('1',installation_bytes.hex(),profile_bytes.hex(),str(expected_generation+1))])
    if fault=='after_generation':
     self.assertEqual(authority_writer.execute('SELECT generation::text FROM truss.policy_generation_guard WHERE singleton=1').fetchone(),(str(expected_generation+1),));authority_writer.execute('SELECT 1/0')
    authority_writer.execute('COMMIT');return advanced
   except BaseException:authority_writer.rollback();raise
  self.assertEqual(participating_assignment_change(False,5),'refused');self.assertEqual(protected_codes(),['RA','RAB']);self.assertEqual(self.admin.execute('SELECT generation::text FROM truss.policy_generation_guard WHERE singleton=1').fetchone(),('5',));observations.append({'id':'durable-real-read-refuses-assignment-revocation-before-effects','observed':{'generation':'5','freshCodes':['RA','RAB']}})
  # Explicit fixture withholding is the completion premise, not a production sink.
  real_buffer=[];observations.append({'id':'durable-real-read-withholds-buffer-before-original-settlement','observed':real_buffer,'qualification':'fixture completion only'})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.assertEqual(self.admin.execute(settle,(b'profile-bound-operation',installation_bytes,profile_bytes,5)).fetchall(),[(b'profile-bound-operation'.hex(),)]);self.admin.execute('COMMIT')
  for fault in ['after_effects','after_generation']:
   with self.assertRaises(psycopg.errors.DivisionByZero) as failure:participating_assignment_change(False,5,fault=fault)
   self.assertEqual(failure.exception.sqlstate,'22012');self.assertEqual(authority_writer.info.transaction_status,psycopg.pq.TransactionStatus.IDLE)
   self.assertEqual(self.admin.execute('SELECT props->%s FROM truss.object WHERE id=%s AND type_id=%s',(active_id,int(aliases['AA'].id),int(assignment['typeId']))).fetchone(),({'kind':'boolean','value':True},));self.assertEqual(self.admin.execute('SELECT generation::text FROM truss.policy_generation_guard WHERE singleton=1').fetchone(),('5',));self.assertEqual(protected_codes(),['RA','RAB']);observations.append({'id':'durable-assignment-'+fault+'-native-failure-rolls-back-effect-and-generation','observed':{'sqlState':'22012','generation':'5','active':True,'freshCodes':['RA','RAB']}})
  committed=participating_assignment_change(False,5);self.assertEqual(committed,[('1',installation_bytes.hex(),profile_bytes.hex(),'6')]);observations.append({'id':'durable-real-read-settlement-permits-committed-assignment-revocation','observed':committed})
  fresh_codes=protected_codes();self.assertEqual(fresh_codes,[]);observations.append({'id':'durable-real-read-fresh-admission-after-revocation-denies','observed':fresh_codes})
  restored=participating_assignment_change(True,6);self.assertEqual(restored,[('1',installation_bytes.hex(),profile_bytes.hex(),'7')]);self.assertEqual(protected_codes(),['RA','RAB']);observations.append({'id':'durable-real-read-controlled-restoration-advances-generation','observed':restored})
  self.admin.execute('CREATE SCHEMA relational_fixture;CREATE TABLE relational_fixture.client(code text PRIMARY KEY);CREATE TABLE relational_fixture.project(code text PRIMARY KEY);CREATE TABLE relational_fixture.staff(code text PRIMARY KEY,login text NOT NULL);CREATE TABLE relational_fixture.resource(code text PRIMARY KEY,secret text NOT NULL);CREATE TABLE relational_fixture.assignment(code text PRIMARY KEY,active boolean NOT NULL)')
  for table,codes in [('client',['C']),('project',['A','B']),('resource',['RA','RB','RAB','RO'])]:
   for code in codes:
    if table=='resource':self.admin.execute('INSERT INTO relational_fixture.resource VALUES(%s,%s)',(code,'raw-'+code))
    else:self.admin.execute('INSERT INTO relational_fixture.'+table+' VALUES(%s)',(code,))
  for login in ['alice','bob','outsider']:self.admin.execute('INSERT INTO relational_fixture.staff VALUES(%s,%s)',('staff-'+login,login))
  for code,active in [('AA',True),('AB',False),('BB',True)]:self.admin.execute('INSERT INTO relational_fixture.assignment VALUES(%s,%s)',(code,active))
  for link,(source,target) in LINKS.items():
   self.admin.execute('CREATE TABLE relational_fixture.'+link+'(occurrence_id text PRIMARY KEY,source_code text NOT NULL REFERENCES relational_fixture.'+source.lower()+'(code),target_code text NOT NULL REFERENCES relational_fixture.'+target.lower()+'(code))')
   for index,(left,right) in enumerate(connections[link]):self.admin.execute('INSERT INTO relational_fixture.'+link+' VALUES(%s,%s,%s)',('raw-'+link+str(index),left,right))
  self.admin.execute('GRANT USAGE ON SCHEMA relational_fixture TO ontology_facts;GRANT SELECT ON ALL TABLES IN SCHEMA relational_fixture TO ontology_facts;GRANT CREATE ON SCHEMA relational_fixture TO ontology_facts')
  self.admin.execute('CREATE FUNCTION relational_fixture.decision_bound(text,text) RETURNS text LANGUAGE SQL SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$ '+sql['flatFold']['sql']+' $$;REVOKE ALL ON FUNCTION relational_fixture.decision_bound(text,text) FROM PUBLIC;ALTER FUNCTION relational_fixture.decision_bound(text,text) OWNER TO ontology_facts')
  self.admin.execute("CREATE FUNCTION relational_fixture.eligible(text) RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ DECLARE n bigint;subject_key text;decision text;BEGIN IF current_setting('transaction_isolation')<>'read committed' THEN RAISE EXCEPTION 'security authority profile unavailable' USING ERRCODE='0A000';END IF;SELECT count(*),min(code) INTO n,subject_key FROM relational_fixture.staff WHERE login=SESSION_USER::text;IF n<>1 THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;decision:=relational_fixture.decision_bound($1,subject_key);IF decision IS NULL OR decision NOT IN ('permit','deny') THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;RETURN decision='permit';END $$;REVOKE ALL ON FUNCTION relational_fixture.eligible(text) FROM PUBLIC;ALTER FUNCTION relational_fixture.eligible(text) OWNER TO ontology_facts;REVOKE CREATE ON SCHEMA relational_fixture FROM ontology_facts")
  self.admin.execute('ALTER TABLE relational_fixture.resource ENABLE ROW LEVEL SECURITY;ALTER TABLE relational_fixture.resource FORCE ROW LEVEL SECURITY;CREATE POLICY resource_membership ON relational_fixture.resource TO alice,bob,outsider USING(relational_fixture.eligible(code))')
  for login in ['alice','bob','outsider']:
   self.admin.execute('GRANT USAGE ON SCHEMA relational_fixture TO '+login+';GRANT SELECT ON relational_fixture.resource TO '+login+';GRANT EXECUTE ON FUNCTION relational_fixture.eligible(text) TO '+login)
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    flat=[r[0] for r in reader.execute('SELECT code FROM relational_fixture.resource ORDER BY code')];graph=[r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(flat,expected[login]);self.assertEqual(graph,expected[login]);observations.append({'id':'same-policy-raw-and-graph-oracle-'+login,'expected':expected[login],'raw':flat,'graph':graph})
    raw_count=reader.execute('SELECT count(*) FROM relational_fixture.resource').fetchone()[0];graph_count=reader.execute('SELECT count(*) FROM truss.object').fetchone()[0];self.assertEqual(raw_count,len(expected[login]));self.assertEqual(graph_count,len(expected[login]));observations.append({'id':'same-policy-native-count-'+login,'raw':raw_count,'graph':graph_count})
    for selected in ['RA','RB','RO']:
     wanted=[selected] if selected in expected[login] else []
     raw_lookup=[row[0] for row in reader.execute('SELECT code FROM relational_fixture.resource WHERE code=%s',(selected,))];graph_lookup=[row[0] for row in reader.execute("SELECT props->%s->>'text' FROM truss.object WHERE props->%s->>'text'=%s",(key,key,selected))];self.assertEqual(raw_lookup,wanted);self.assertEqual(graph_lookup,wanted);observations.append({'id':'same-policy-native-key-lookup-'+login+'-'+selected,'raw':raw_lookup,'graph':graph_lookup})
    for offset in [0,1,2]:
     wanted=expected[login][offset:offset+1]
     raw_page=[row[0] for row in reader.execute('SELECT code FROM relational_fixture.resource ORDER BY code LIMIT 1 OFFSET %s',(offset,))];graph_page=[row[0] for row in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text' LIMIT 1 OFFSET %s",(key,key,offset))];self.assertEqual(raw_page,wanted);self.assertEqual(graph_page,wanted);observations.append({'id':'same-policy-native-sorted-page-'+login+'-'+str(offset),'raw':raw_page,'graph':graph_page})
    raw_pairs=reader.execute('SELECT count(*) FROM relational_fixture.resource a CROSS JOIN relational_fixture.resource b').fetchone()[0];graph_pairs=reader.execute('SELECT count(*) FROM truss.object a CROSS JOIN truss.object b').fetchone()[0];self.assertEqual(raw_pairs,len(expected[login])**2);self.assertEqual(graph_pairs,len(expected[login])**2);observations.append({'id':'same-policy-native-self-join-count-'+login,'raw':raw_pairs,'graph':graph_pairs})
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute('SELECT * FROM relational_fixture.assignment')
    observations.append({'id':'raw-private-assignment-table-denied-'+login,'observed':'42501'})
  # Activate constant-transformed field disclosure; no raw bag/column grants.
  for namespace,disclosure in [('ontology_fixture',sql['graphDisclosure']),('relational_fixture',sql['flatDisclosure'])]:
   self.admin.execute('GRANT CREATE ON SCHEMA '+namespace+' TO ontology_facts')
   self.admin.execute('CREATE FUNCTION '+namespace+'.disclosure_bound(text,text) RETURNS TABLE(decision text,disclosure jsonb) LANGUAGE SQL SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$ '+disclosure['sql']+' $$;REVOKE ALL ON FUNCTION '+namespace+'.disclosure_bound(text,text) FROM PUBLIC;ALTER FUNCTION '+namespace+'.disclosure_bound(text,text) OWNER TO ontology_facts')
   body="DECLARE n bigint;subject_key text;r record;d record;mask jsonb;BEGIN IF current_setting('transaction_isolation')<>'read committed' THEN RAISE EXCEPTION 'security authority profile unavailable' USING ERRCODE='0A000';END IF;SELECT count(*),min(s.code) INTO n,subject_key FROM "+namespace+".staff s WHERE s.login=SESSION_USER::text;IF n<>1 THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;FOR r IN SELECT q.code FROM "+namespace+".resource q LOOP SELECT * INTO STRICT d FROM "+namespace+".disclosure_bound(r.code,subject_key);IF d.decision='deny' THEN CONTINUE;END IF;IF d.decision IS DISTINCT FROM 'permit' THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;SELECT entry->'disposition' INTO STRICT mask FROM jsonb_array_elements(d.disclosure) entry WHERE entry->'field'=jsonb_build_object('documentId','adoc','moduleId','m','elementId','Resource-secret');IF mask#>>'{transformed,transform}' IS DISTINCT FROM 'constant' OR mask#>>'{transformed,version}' IS DISTINCT FROM '0.1.0' OR mask#>>'{transformed,literal,string}' IS NULL THEN RAISE EXCEPTION 'security disclosure unavailable' USING ERRCODE='55000';END IF;RETURN QUERY SELECT r.code::text,mask#>>'{transformed,literal,string}',mask;END LOOP;END"
   self.admin.execute('CREATE FUNCTION '+namespace+'.masked_resources() RETURNS TABLE(code text,secret text,disposition jsonb) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ '+body+' $$;REVOKE ALL ON FUNCTION '+namespace+'.masked_resources() FROM PUBLIC;ALTER FUNCTION '+namespace+'.masked_resources() OWNER TO ontology_facts;REVOKE CREATE ON SCHEMA '+namespace+' FROM ontology_facts')
  self.admin.execute('CREATE POLICY complete_private_resource_disclosure ON relational_fixture.resource FOR SELECT TO ontology_facts USING(true)')
  for login in ['alice','bob','outsider']:
   self.admin.execute('REVOKE SELECT(props) ON truss.object FROM '+login+';REVOKE SELECT ON relational_fixture.resource FROM '+login+';GRANT SELECT(code) ON relational_fixture.resource TO '+login+';GRANT EXECUTE ON FUNCTION ontology_fixture.masked_resources(),relational_fixture.masked_resources() TO '+login)
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    for namespace in ['ontology_fixture','relational_fixture']:
     rows=reader.execute('SELECT code,secret,disposition FROM '+namespace+'.masked_resources() ORDER BY code').fetchall();self.assertEqual([row[0] for row in rows],expected[login]);self.assertTrue(all(row[1]=='MASKED' and row[2]['transformed']['literal']['string']=='MASKED' for row in rows));observations.append({'id':'native-constant-disclosure-'+namespace+'-'+login,'observed':[[row[0],row[1],row[2]] for row in rows]})
     raw_filter=reader.execute('SELECT count(*) FROM '+namespace+".masked_resources() WHERE secret='raw-RA'").fetchone()[0];self.assertEqual(raw_filter,0);observations.append({'id':'query-uses-disclosed-value-'+namespace+'-'+login,'observed':raw_filter})
    for statement in ['SELECT props FROM truss.object','SELECT secret FROM relational_fixture.resource']:
     with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute(statement)
    observations.append({'id':'raw-field-and-bag-denied-after-mask-activation-'+login,'observed':'42501'})
  original_graph=self.admin.execute('SELECT secret FROM ontology_fixture.resource WHERE code=%s',('RA',)).fetchone()[0];original_raw=self.admin.execute('SELECT secret FROM relational_fixture.resource WHERE code=%s',('RA',)).fetchone()[0];self.assertEqual((original_graph,original_raw),('raw-RA','raw-RA'));observations.append({'id':'read-transform-preserves-canonical-values','observed':[original_graph,original_raw]})
  # Withholding has metadata and no public secret column/value carrier.
  for namespace,disclosure in [('ontology_fixture',sql['graphWithheld']),('relational_fixture',sql['flatWithheld'])]:
   self.admin.execute('GRANT CREATE ON SCHEMA '+namespace+' TO ontology_facts;CREATE FUNCTION '+namespace+'.withheld_bound(text,text) RETURNS TABLE(decision text,disclosure jsonb) LANGUAGE SQL SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$ '+disclosure['sql']+' $$;REVOKE ALL ON FUNCTION '+namespace+'.withheld_bound(text,text) FROM PUBLIC;ALTER FUNCTION '+namespace+'.withheld_bound(text,text) OWNER TO ontology_facts')
   body="DECLARE n bigint;subject_key text;r record;d record;state jsonb;BEGIN IF current_setting('transaction_isolation')<>'read committed' THEN RAISE EXCEPTION 'security authority profile unavailable' USING ERRCODE='0A000';END IF;SELECT count(*),min(s.code) INTO n,subject_key FROM "+namespace+".staff s WHERE s.login=SESSION_USER::text;IF n<>1 THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;FOR r IN SELECT q.code FROM "+namespace+".resource q LOOP SELECT * INTO STRICT d FROM "+namespace+".withheld_bound(r.code,subject_key);IF d.decision='deny' THEN CONTINUE;END IF;IF d.decision IS DISTINCT FROM 'permit' THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;SELECT entry->'disposition' INTO STRICT state FROM jsonb_array_elements(d.disclosure) entry WHERE entry->'field'=jsonb_build_object('documentId','adoc','moduleId','m','elementId','Resource-secret');IF state IS DISTINCT FROM '\"withheld\"'::jsonb THEN RAISE EXCEPTION 'security disclosure unavailable' USING ERRCODE='55000';END IF;RETURN QUERY SELECT r.code::text,jsonb_build_object('field',jsonb_build_object('documentId','adoc','moduleId','m','elementId','Resource-secret'),'disposition',state);END LOOP;END"
   self.admin.execute('CREATE FUNCTION '+namespace+'.withheld_resources() RETURNS TABLE(code text,disposition jsonb) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ '+body+' $$;REVOKE ALL ON FUNCTION '+namespace+'.withheld_resources() FROM PUBLIC;ALTER FUNCTION '+namespace+'.withheld_resources() OWNER TO ontology_facts;REVOKE CREATE ON SCHEMA '+namespace+' FROM ontology_facts')
  for login in ['alice','bob','outsider']:
   self.admin.execute('REVOKE EXECUTE ON FUNCTION ontology_fixture.masked_resources(),relational_fixture.masked_resources() FROM '+login+';GRANT EXECUTE ON FUNCTION ontology_fixture.withheld_resources(),relational_fixture.withheld_resources() TO '+login)
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    for namespace in ['ontology_fixture','relational_fixture']:
     rows=reader.execute('SELECT code,disposition FROM '+namespace+'.withheld_resources() ORDER BY code').fetchall();self.assertEqual([row[0] for row in rows],expected[login]);self.assertTrue(all(row[1]=={'field':{'documentId':'adoc','moduleId':'m','elementId':'Resource-secret'},'disposition':'withheld'} for row in rows));observations.append({'id':'native-withheld-disposition-'+namespace+'-'+login,'observed':[list(row) for row in rows]})
     with self.assertRaises(psycopg.errors.UndefinedColumn):reader.execute('SELECT secret FROM '+namespace+'.withheld_resources()')
     observations.append({'id':'withheld-property-operator-has-no-value-carrier-'+namespace+'-'+login,'observed':'42703'})
     with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute('SELECT * FROM '+namespace+'.masked_resources()')
     observations.append({'id':'prior-transform-endpoint-revoked-'+namespace+'-'+login,'observed':'42501'})
  # Conflicting candidate never publishes over the protected withholding surface.
  for namespace,candidate in [('ontology_fixture',sql['graphConflict']),('relational_fixture',sql['flatConflict'])]:
   original=self.admin.execute("SELECT pg_get_functiondef(oid),proacl::text,proowner::text FROM pg_proc WHERE oid=%s::regprocedure",(namespace+'.withheld_resources()',)).fetchone()
   self.admin.execute('BEGIN')
   try:
    self.admin.execute('CREATE FUNCTION '+namespace+'.conflicting_candidate(text,text) RETURNS TABLE(decision text,disclosure jsonb) LANGUAGE SQL SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$ '+candidate['sql']+' $$;REVOKE ALL ON FUNCTION '+namespace+'.conflicting_candidate(text,text) FROM PUBLIC')
    candidate_result=self.admin.execute('SELECT * FROM '+namespace+'.conflicting_candidate(%s,%s)',('RA','staff-alice')).fetchone();self.assertEqual(candidate_result,('conflict',[]));observations.append({'id':'incompatible-native-masks-refuse-before-publication-'+namespace,'observed':list(candidate_result)})
   finally:self.admin.rollback()
   current=self.admin.execute("SELECT pg_get_functiondef(oid),proacl::text,proowner::text FROM pg_proc WHERE oid=%s::regprocedure",(namespace+'.withheld_resources()',)).fetchone();self.assertEqual(current,original);observations.append({'id':'conflict-refusal-preserves-prior-body-acl-owner-'+namespace,'observed':'exact-original'})
   exists=self.admin.execute('SELECT to_regprocedure(%s)',(namespace+'.conflicting_candidate(text,text)',)).fetchone()[0];self.assertIsNone(exists);observations.append({'id':'conflicting-candidate-rollback-leaves-no-routine-'+namespace,'observed':None})
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='alice'
   with psycopg.connect(**params,autocommit=True) as reader:
    rows=reader.execute('SELECT code,disposition FROM '+namespace+'.withheld_resources() ORDER BY code').fetchall();self.assertEqual([row[0] for row in rows],['RA','RAB']);self.assertTrue(all(row[1]['disposition']=='withheld' for row in rows));observations.append({'id':'prior-withholding-still-executes-after-conflict-refusal-'+namespace,'observed':[list(row) for row in rows]})
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']).write_text(json.dumps({'packet':packet,'sql':sql,'observations':observations,'publicCreatedIdentities':{alias:{'id':identity.id,'typeId':identity.type_id} for alias,identity in aliases.items()},'scope':'Actual public-created objects/edges, typed native joins to business keys and candidate typed Record/opaque Relationship membership lowering under ordinary native RLS. Private views are real graph projections, not seeded flat tables. Not complete source enrollment, held authority or released public API/security compiler admission.'},indent=2)+'\n')
if __name__=='__main__':
 import unittest;unittest.main()
