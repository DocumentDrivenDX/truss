"""Original compiler/profile guard coupling; no security-ready physical profile.
@covers US-056-AC6
@covers US-056-AC9
"""
import copy,json,os,sys,unittest
from pathlib import Path
import psycopg
from truss import Ok,Error,adopt_psycopg_host
from truss.weft import CompileRefusal
from truss._security_mapping import SecurityMappingBoundary,prepare_security_mapping_in_transaction
from truss._security_home_installation import bootstrap_security_homes_in_transaction
import test_catalog_runtime_native as catalog
FIXTURE=Path(__file__).parent/'fixtures/security-mapping-request.json'
def encoded(value):return json.dumps(value,separators=(',',':'),ensure_ascii=False).encode()
class MappingNativeTests(catalog.PublicCatalogRuntimeTests):
 for name in tuple(n for n in dir(catalog.PublicCatalogRuntimeTests) if n.startswith('test_')):locals()[name]=None
 @classmethod
 def setUpClass(cls):
  path=os.environ.get('TRUSS_SECURITY_MAPPING_WEFT_MODULE_DIR')
  if not path:raise RuntimeError('Original Weft mapping extension path is a required native qualification input')
  sys.path.insert(0,path);import weft
  if Path(weft.__file__).resolve()!=(Path(path)/'weft.so').resolve():raise RuntimeError('Original mapping extension required')
  cls.original=staticmethod(weft.prepare_security_mapping_json)
  super().setUpClass()
 def ready_mapping(self,compiler=None):
  self.install();self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);self.tx=self.host.adopt_transaction().value
  source=json.loads(FIXTURE.read_text());self.reference=encoded(source);self.calls=[]
  def prepare(text):self.calls.append(text);return self.original(text) if compiler is None else compiler(text)
  self.boundary=SecurityMappingBoundary(prepare,self.reference);self.identity=self.installation.installation_id.encode()
  self.assertIsInstance(bootstrap_security_homes_in_transaction(self.host,self.tx,installation_identity=self.identity,authored_profile=self.boundary.original_profile,max_retained=8),Ok)
  self.admin.execute("CREATE TEMP TABLE prior_mapping_work(value text);INSERT INTO prior_mapping_work VALUES('kept')")
  return source
 def prepare(self,request=None,generation=1):
  return prepare_security_mapping_in_transaction(self.host,self.tx,boundary=self.boundary,installation_identity=self.identity,expected_generation=generation,original_request=self.reference if request is None else encoded(request))
 def test_original_native_profile_and_compiler_handoff(self):
  self.ready_mapping();before=self.admin.execute("SELECT current_setting('search_path')").fetchone()
  result=self.prepare();self.assertIsInstance(result,Ok);self.assertFalse(result.value.security_ready);self.assertEqual(len(self.calls),1)
  response=json.loads(result.value.original_response);self.assertEqual(response['handoff']['binding']['backendId'],'truss.postgresql');self.assertEqual(len(response['handoff']['uses']),6)
  self.assertEqual(self.admin.execute("SELECT current_setting('search_path')").fetchone(),before)
  self.assertEqual(self.admin.execute('SELECT value FROM prior_mapping_work').fetchall(),[('kept',)])
 def test_source_substitutions_refuse_before_compiler(self):
  source=self.ready_mapping()
  for key in ('policyJson','ontologyJson','queryProfileJson','bindingJson','backendVersion','targetProfile'):
   changed=copy.deepcopy(source);changed[key]+=' ';result=self.prepare(changed);self.assertIsInstance(result,Error);self.assertEqual(self.calls,[])
  changed=copy.deepcopy(source);changed['modules'][0]['documentJson']+=' ';self.assertIsInstance(self.prepare(changed),Error);self.assertEqual(self.calls,[])
  self.assertEqual(self.admin.execute('SELECT value FROM prior_mapping_work').fetchall(),[('kept',)])
 def test_native_profile_generation_missing_guard_and_acl_refuse(self):
  self.ready_mapping()
  for statement in ["UPDATE truss.policy_generation_guard SET policy_profile_bytes=decode('00','hex')","UPDATE truss.policy_generation_guard SET generation=2",'DELETE FROM truss.policy_generation_guard','GRANT SELECT ON truss.policy_generation_guard TO consumer','GRANT SELECT (policy_profile_bytes) ON truss.policy_generation_guard TO consumer','GRANT UPDATE (generation) ON truss.policy_generation_guard TO consumer']:
   self.admin.execute('SAVEPOINT fixture_change');self.admin.execute(statement)
   self.assertIsInstance(self.prepare(),Error);self.assertEqual(self.calls,[]);self.admin.execute('ROLLBACK TO SAVEPOINT fixture_change');self.admin.execute('RELEASE SAVEPOINT fixture_change')
  self.assertIsInstance(self.prepare(generation=True),Error);self.assertEqual(self.calls,[])
  self.assertEqual(self.admin.execute('SELECT value FROM prior_mapping_work').fetchall(),[('kept',)])
 def test_response_substitution_and_late_native_generation_roll_back(self):
  def substituted(text):
   response=json.loads(self.original(text));response['handoff']['sqlSha256']='0'*64;return json.dumps(response)
  self.ready_mapping(substituted);self.assertIsInstance(self.prepare(),Error);self.assertEqual(len(self.calls),1)
  self.assertEqual(self.admin.execute('SELECT value FROM prior_mapping_work').fetchall(),[('kept',)])
  def late(text):
   self.admin.execute('UPDATE truss.policy_generation_guard SET generation=2');return self.original(text)
  self.calls=[]
  def measured(text):self.calls.append(text);return late(text)
  self.boundary=SecurityMappingBoundary(measured,self.reference)
  self.assertIsInstance(self.prepare(),Error);self.assertEqual(len(self.calls),1)
  self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(1,))
  self.assertEqual(self.admin.execute('SELECT value FROM prior_mapping_work').fetchall(),[('kept',)])
 def test_native_guard_writer_waits_through_outer_settlement(self):
  import threading,time
  from psycopg.conninfo import conninfo_to_dict
  self.ready_mapping()
  # Publish setup before the competing connection probes the guard. The lock
  # must come from this helper, not uncommitted bootstrap DDL or insertion.
  self.host.detach();self.admin.commit();self.admin.execute('BEGIN')
  self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);self.tx=self.host.adopt_transaction().value
  writer=psycopg.connect(**conninfo_to_dict(self.info.connection_uri),autocommit=True,options='-c statement_timeout=10000');observer=psycopg.connect(**conninfo_to_dict(self.info.connection_uri),autocommit=True)
  self.addCleanup(writer.close);self.addCleanup(observer.close)
  pid=writer.info.backend_pid;holder=self.admin.info.backend_pid;outcomes=[]
  def update():
   try:writer.execute('BEGIN');writer.execute('UPDATE truss.policy_generation_guard SET generation=2');writer.commit();outcomes.append('committed')
   except BaseException as error:outcomes.append(type(error).__name__)
  thread=threading.Thread(target=update,daemon=True)
  def blocked():return observer.execute('SELECT %s::int=ANY(pg_catalog.pg_blocking_pids(%s))',(holder,pid)).fetchone()==(True,)
  def measured(text):
   self.calls.append(text);thread.start();deadline=time.monotonic()+5
   while not blocked():
    if time.monotonic()>deadline:raise AssertionError('Original native guard holder did not block writer')
    time.sleep(.01)
   return self.original(text)
  self.boundary=SecurityMappingBoundary(measured,self.reference)
  try:
   result=self.prepare();self.assertIsInstance(result,Ok);self.assertFalse(result.value.security_ready);self.assertTrue(blocked());self.assertEqual(outcomes,[])
   self.host.detach();self.admin.commit();thread.join(5);self.assertFalse(thread.is_alive());self.assertEqual(outcomes,['committed'])
   self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
   self.assertIsInstance(self.prepare(generation=1),Error);self.assertEqual(len(self.calls),1)
  finally:
   self.admin.rollback();thread.join(5)
 def test_malformed_handoff_and_changed_path_cleanup(self):
  def missing(text):
   response=json.loads(self.original(text));del response['handoff']['applicationPlan'];return json.dumps(response)
  self.ready_mapping(missing);self.assertIsInstance(self.prepare(),Error)
  self.calls=[]
  before=self.admin.execute("SELECT current_setting('search_path')").fetchone()
  self.admin.execute('CREATE SCHEMA mapping_operator_attack')
  self.admin.execute("CREATE FUNCTION mapping_operator_attack.fail_eq(smallint,integer) RETURNS boolean LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'controlled operator' USING ERRCODE='P0001'; END $$")
  self.admin.execute('CREATE OPERATOR mapping_operator_attack.= (LEFTARG=smallint, RIGHTARG=integer, FUNCTION=mapping_operator_attack.fail_eq)')
  self.admin.execute('SAVEPOINT hostile_path_probe')
  self.admin.execute("SELECT set_config('search_path','mapping_operator_attack, pg_catalog',true)")
  with self.assertRaises(psycopg.Error) as caught:self.admin.execute('SELECT 1::smallint=1::integer')
  self.assertEqual(caught.exception.sqlstate,'P0001')
  self.admin.execute('ROLLBACK TO SAVEPOINT hostile_path_probe');self.admin.execute('RELEASE SAVEPOINT hostile_path_probe')
  def changed_path(text):
   self.calls.append(text);self.admin.execute("SELECT set_config('search_path','mapping_operator_attack, pg_catalog',true)");return self.original(text)
  self.boundary=SecurityMappingBoundary(changed_path,self.reference)
  self.assertIsInstance(self.prepare(),Ok);self.assertEqual(len(self.calls),1)
  self.assertEqual(self.admin.execute("SELECT current_setting('search_path')").fetchone(),before)
  self.assertEqual(self.admin.execute('SELECT value FROM prior_mapping_work').fetchall(),[('kept',)])
 def test_started_deferred_cleanup_contains_native_effects(self):
  retained=[]
  def deferred(text):
   def response():
    try:yield 'unsupported'
    finally:
     self.admin.execute('UPDATE truss.policy_generation_guard SET generation=2')
     raise KeyboardInterrupt('controlled deferred cleanup')
   result=response();next(result);retained.append(result);return result
  self.ready_mapping(deferred)
  with self.assertRaises(KeyboardInterrupt):self.prepare()
  self.assertEqual(len(self.calls),1)
  self.assertEqual(len(retained),1);self.assertIsNone(retained[0].gi_frame)
  self.assertEqual(self.host._custody.last_attempt.phase,'contained')
  self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(1,))
  self.assertEqual(self.admin.execute('SELECT value FROM prior_mapping_work').fetchall(),[('kept',)])
 def test_ordinary_connection_cannot_invoke_administrative_mapping_guard(self):
  self.ready_mapping();self.host.detach();self.admin.commit()
  connection,host,assembly,tx=self.consumer()
  connection.execute("CREATE TEMP TABLE ordinary_prior_mapping_work(value text);INSERT INTO ordinary_prior_mapping_work VALUES('kept')")
  result=prepare_security_mapping_in_transaction(host,tx,boundary=self.boundary,installation_identity=self.identity,expected_generation=1,original_request=self.reference)
  self.assertIsInstance(result,Error);self.assertEqual(self.calls,[])
  self.assertEqual(connection.execute('SELECT value FROM ordinary_prior_mapping_work').fetchall(),[('kept',)])
