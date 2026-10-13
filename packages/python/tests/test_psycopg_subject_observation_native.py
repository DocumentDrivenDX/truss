"""Original Python host/source owner observation, not protected native admission.
@covers US-056-AC2
@covers US-056-AC10
"""
import json,os,tempfile,unittest,sys
from pathlib import Path
from dataclasses import replace,FrozenInstanceError
import psycopg
from truss import LocalPostgres
from truss.execution import Ok,Error
from truss.psycopg_host import adopt_psycopg_host
from truss._psycopg_subject_observation import _SubjectSelection,_observe_ordinary_subject

class SubjectObservationNativeTests(unittest.TestCase):
 def test_original_psycopg_subject_and_source_correspondence(self):
  directory=os.environ.get('TRUSS_SUBJECT_OWNER_MODULE_DIR')
  if not directory:raise RuntimeError('Original rebuilt subject-inspection extension required')
  sys.path.insert(0,directory)
  import weft
  self.assertEqual(Path(weft.__file__).resolve(),(Path(directory)/'weft.so').resolve())
  request=Path(__file__).with_name('fixtures').joinpath('security-mapping-request.json').read_bytes()
  source=json.loads(request)['modules'][0]['documentJson'].encode()
  cases=[]
  with tempfile.TemporaryDirectory(prefix='python-subject-',dir='/private/tmp') as directory:
   with LocalPostgres(Path(directory)/'data') as runtime:
    params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
    with psycopg.connect(**params,autocommit=True) as admin:
     admin.execute('CREATE ROLE subject_alice LOGIN;CREATE ROLE subject_bob LOGIN;CREATE ROLE subject_delegate;GRANT subject_delegate TO subject_alice;CREATE SCHEMA subject_diag')
     admin.execute("""CREATE TABLE subject_diag.staff(actor name PRIMARY KEY,key text NOT NULL);
      INSERT INTO subject_diag.staff VALUES('subject_alice','Δ'||chr(65279)||'9007199254740993');
      CREATE FUNCTION subject_diag.observe(actor text) RETURNS TABLE(staff_id text)
       LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$ SELECT key FROM subject_diag.staff s WHERE s.actor::text=$1 AND $1=SESSION_USER::text $$;
      CREATE FUNCTION subject_diag.observe_name(actor name) RETURNS TABLE(staff_id text)
       LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$ SELECT key FROM subject_diag.staff s WHERE s.actor=$1 AND $1=SESSION_USER $$;
      CREATE FUNCTION subject_diag.wrong_oid(actor text) RETURNS TABLE(staff_id name) LANGUAGE sql AS $$ SELECT 'alice'::name $$;
      CREATE FUNCTION subject_diag.null_key(actor text) RETURNS TABLE(staff_id text) LANGUAGE sql AS $$ SELECT NULL::text $$;
      CREATE FUNCTION subject_diag.many(actor text) RETURNS TABLE(staff_id text) LANGUAGE sql AS $$ SELECT 'a'::text UNION ALL SELECT 'b'::text $$;
      GRANT USAGE ON SCHEMA subject_diag TO subject_alice,subject_bob,subject_delegate""")
     base=_SubjectSelection(request,source,'m','Staff','pk','subject_alice','subject_diag','observe',('staff_id',))
     expected=admin.execute('SELECT key FROM subject_diag.staff').fetchone()[0]
     inspector=weft.inspect_security_mapping_subject_key_json
     def operation(user='subject_alice',isolation='repeatable_read',readonly=True,selection=base,role=None,loader=None):
      values=dict(params);values['user']=user;values['options']='-c statement_timeout=2000'
      connection=psycopg.connect(**values)
      if loader:connection.adapters.register_loader(19,loader)
      try:
       connection.execute('BEGIN ISOLATION LEVEL '+isolation.replace('_',' ')+(' READ ONLY' if readonly else ' READ WRITE'))
       if role:connection.execute('SET ROLE '+role)
       host=adopt_psycopg_host(connection)
       transaction=host.adopt_transaction(isolation=isolation,access_mode='read_only' if readonly else 'read_write')
       self.assertIsInstance(transaction,Ok)
       result=_observe_ordinary_subject(host,transaction.value,selection,inspector)
       return connection,host,transaction.value,result
      except BaseException:
       connection.close();raise
     for selection in [base,replace(base,routine='observe_name',actor_carrier='name')]:
      connection,host,transaction,result=operation(selection=selection)
      try:
       self.assertIsInstance(result,Ok);observation=result.value
       self.assertEqual(observation.values,(expected,));self.assertEqual(observation.utf8_hex,(expected.encode().hex(),))
       self.assertEqual(observation.identity,('m','Staff','pk'))
       with self.assertRaises(FrozenInstanceError):observation.principal='other'
       # Caller still owns original transaction; historical evidence remains after rollback.
       self.assertEqual(connection.execute('SHOW transaction_read_only').fetchone(),('on',))
       connection.rollback();connection.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
       self.assertIsInstance(_observe_ordinary_subject(host,transaction,selection,inspector),Error)
       self.assertEqual(observation.values,(expected,));cases.append(selection.actor_carrier+' and stale handle')
      finally:host.detach();connection.close()
     negatives=[('unbound caller',dict(user='subject_bob',selection=replace(base,principal='subject_bob'))),
                ('wrong caller',dict(user='subject_bob')),('superuser',dict(user=params['user'],selection=replace(base,principal=params['user']))),
                ('effective role',dict(role='subject_delegate')),('read committed',dict(isolation='read_committed')),
                ('read write',dict(readonly=False)),('wrong OID',dict(selection=replace(base,routine='wrong_oid'))),
                ('null key',dict(selection=replace(base,routine='null_key'))),('multiple keys',dict(selection=replace(base,routine='many'))),
                ('wrong columns',dict(selection=replace(base,columns=('foreign',))))]
     for name,options in negatives:
      connection,host,transaction,result=operation(**options)
      try:self.assertIsInstance(result,Error,name);cases.append(name)
      finally:host.detach();connection.close()
     from psycopg.adapt import Loader
     decoded=[]
     class ForeignNameLoader(Loader):
      def load(self,data):decoded.append(True);raise AssertionError('Foreign loader invoked')
     connection,host,transaction,result=operation(selection=replace(base,routine='wrong_oid'),loader=ForeignNameLoader)
     try:
      self.assertIsInstance(result,Error);self.assertEqual(decoded,[]);cases.append('foreign loader refused before decode')
     finally:host.detach();connection.close()
     for name,selection in [('non-subject Record',replace(base,record='Resource')),('wrong source',replace(base,original_document=source+b' ')),('wrong Key',replace(base,key='foreign'))]:
      connection,host,transaction,result=operation()
      try:
       with self.assertRaises(ValueError):_observe_ordinary_subject(host,transaction,selection,inspector)
       cases.append(name)
      finally:host.detach();connection.close()
     connection,host,transaction,result=operation()
     other,other_host,other_transaction,_=operation()
     try:
      self.assertIsInstance(_observe_ordinary_subject(host,other_transaction,base,inspector),Error)
      cases.append('foreign original handle')
     finally:host.detach();connection.close();other_host.detach();other.close()
     entered=[]
     async def deferred(*args):entered.append(True)
     connection,host,transaction,result=operation()
     try:
      with self.assertRaises(ValueError):_observe_ordinary_subject(host,transaction,base,deferred)
      self.assertEqual(entered,[]);cases.append('deferred inspector refused before invocation')
      with self.assertRaises(ValueError):_observe_ordinary_subject(host,transaction,base,lambda *_:'{"interfaceVersion":"weft-security-subject-selection/0.1.0","status":"inspected","securityReady":0}')
      cases.append('numeric false response refused')
     finally:host.detach();connection.close()
     output=os.environ.get('TRUSS_PYTHON_SUBJECT_EVIDENCE')
     if output:Path(output).write_text(json.dumps({'cases':cases,'serverVersion':admin.execute('SHOW server_version').fetchone()[0],'nativeExpected':expected,'scope':'Stock psycopg caller-owned stable read-only operation; original Weft source selection; trusted helper fixture/local trust authentication; no key domain encoding/subject existence/current authority/protected release'},indent=2)+'\n')
