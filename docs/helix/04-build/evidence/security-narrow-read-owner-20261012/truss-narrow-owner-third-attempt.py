"""Public graph source-cut regression; disposable policy/setting experiment, not admission."""
import json,subprocess,os
from pathlib import Path
from dataclasses import replace
from truss import Ok
from truss.contracts import BooleanValue
from truss.groups import AuthoredValue,GroupSuccess,RequestNone
import test_group_create_native as groups
class GraphABACTests(groups.PublicCreateGroupTests):
 for name in tuple(n for n in dir(groups.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None
 def tearDown(self):
  self.admin.rollback();self.admin.execute('DROP FUNCTION IF EXISTS public.graph_read_wrapper();DROP FUNCTION IF EXISTS public.graph_read(text,text) CASCADE')
  super().tearDown()
 def source(self,document):
  m=document['modules'][0];record=next(e for e in m['elements'] if e['id']=='A');m['elements'].append({'id':'A-flag','kind':'field','name':'flag','scalarType':'boolean','cardinality':'one','nullability':'required','extensions':{}});record['members'].append({'module':'m','element':'A-flag'})
 def test_public_graph_creation_and_original_source_validity(self):
  c,host,assembly,tx=self.ready(self.source)
  operations=tuple(replace(self.create(label=label,alias=label),values=self.create(label=label,alias=label).values+(AuthoredValue(name='flag',value=BooleanValue(value=flag)),)) for label,flag in [('yes',True),('no',False)])
  inp,_=self.input(assembly,tx,operations);result=assembly.apply_in_transaction(tx,inp,RequestNone(),documents=self.documents,bun_executable='/opt/homebrew/bin/bun');self.assertIsInstance(result,Ok);self.assertIsInstance(result.value,GroupSuccess);host.detach();c.commit()
  type_id=self.types[('adoc','A')].type_id
  props={row[0]:str(row[1]) for row in self.admin.execute('SELECT name,prop_id FROM truss.prop_def WHERE type_id=%s',(int(type_id),))};packet={'typeId':type_id,'valueId':props['A-value'],'labelId':props['A-label'],'flagId':props['flag']}
  run=subprocess.run(['/opt/homebrew/bin/bun',str(Path(__file__).resolve().parents[3]/'tests/fixtures/security-public-graph-abac.ts')],input=json.dumps(packet),text=True,capture_output=True,timeout=30);self.assertEqual(run.returncode,0,run.stderr);sql=json.loads(run.stdout);observations=[]
  valid=self.admin.execute(sql['validitySql']).fetchone()[0];self.assertEqual(valid,'true');observations.append({'id':'original-public-graph-validity','observed':valid})
  self.admin.execute('CREATE FUNCTION public.graph_candidate(text,text,bool) RETURNS bool LANGUAGE SQL AS $$ SELECT '+sql['predicateSql']+' $$')
  self.addCleanup(self.admin.execute,'DROP FUNCTION public.graph_candidate(text,text,bool)')
  query='SELECT label FROM ('+sql['sourceSql']+') original_graph WHERE public.graph_candidate(value,label,flag) ORDER BY label'
  rows=self.admin.execute(query).fetchall();self.assertEqual(rows,[('yes',)]);observations.append({'id':'original-graph-eligible-values','expected':[['yes']],'observed':[list(r) for r in rows]})
  original=self.admin.execute('SELECT id,props FROM truss.object WHERE type_id=%s ORDER BY id',(int(type_id),)).fetchall();self.assertEqual(len(original),2)
  self.admin.execute('BEGIN');self.admin.execute("UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s",(props['flag'],'"true"',original[1][0]))
  invalid=self.admin.execute(sql['validitySql']).fetchone()[0];self.assertEqual(invalid,'false');observations.append({'id':'malformed-graph-field-refuses-global-preflight','observed':invalid})
  filtered=self.admin.execute(query).fetchall();observations.append({'id':'filter-alone-can-hide-invalid-source','observed':[list(r) for r in filtered]});self.admin.rollback()
  for case,value in [('wrong-tag',{'kind':'string','value':True}),('wrong-payload',{'kind':'boolean','value':'true'}),('extra-envelope-member',{'kind':'boolean','value':True,'extra':1}),('missing-payload',{'kind':'boolean'})]:
   self.admin.execute('BEGIN');self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s',(props['flag'],json.dumps(value),original[1][0]))
   observed=self.admin.execute(sql['validitySql']).fetchone()[0];self.assertEqual(observed,'false');observations.append({'id':case,'observed':observed});self.admin.execute(query).fetchall();self.admin.rollback()
  restored=self.admin.execute(sql['validitySql']).fetchone()[0];self.assertEqual(restored,'true');observations.append({'id':'restored-original-source','observed':restored})
  from truss import ObjectFound
  ids={r[1]:int(r[0]) for r in self.admin.execute('SELECT native_id,label FROM ('+sql['sourceSql']+') original_graph').fetchall()}
  before,bh,ba,bt=self.consumer()
  for label in ['yes','no']:
   read=ba.get_object_in_transaction(bt,document_id='adoc',module_id='m',record_id='A',object_id=ids[label]);self.assertIsInstance(read,Ok);self.assertIsInstance(read.value,ObjectFound);observations.append({'id':'public-get-before-policy-'+label,'observed':'ObjectFound'})
  bh.detach();before.commit()
  expressions=sql['rowExpressions'];policy='public.graph_candidate('+','.join(expressions[name] for name in ['value','label','flag'])+')'
  self.admin.execute('ALTER TABLE truss.object ENABLE ROW LEVEL SECURITY;ALTER TABLE truss.object FORCE ROW LEVEL SECURITY;CREATE POLICY graph_candidate_rows ON truss.object USING ('+policy+');CREATE ROLE graph_direct LOGIN NOSUPERUSER NOBYPASSRLS;GRANT USAGE ON SCHEMA truss TO graph_direct;GRANT SELECT ON truss.object TO graph_direct')
  import psycopg
  self.addCleanup(self.admin.execute,'DROP OWNED BY graph_direct;DROP ROLE graph_direct')
  connection=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);connection['user']='graph_direct'
  direct=psycopg.connect(**connection,autocommit=True);self.addCleanup(direct.close)
  version=self.admin.execute('SHOW server_version_num').fetchone()[0];self.assertEqual(version,'180006');observations.append({'id':'native-version','observed':version})
  inventory=self.admin.execute("SELECT c.relrowsecurity,c.relforcerowsecurity,r.rolsuper,r.rolbypassrls FROM pg_class c JOIN pg_roles r ON r.oid=c.relowner WHERE c.oid='truss.object'::regclass").fetchone();self.assertEqual(inventory,(True,True,False,False));observations.append({'id':'forced-policy-and-ordinary-table-owner','observed':list(inventory)})
  settings=self.admin.execute("SELECT proconfig FROM pg_proc WHERE oid='truss.get_object(text,text,text,bigint,integer,text,text)'::regprocedure").fetchone()[0];self.assertIn('row_security=off',settings);observations.append({'id':'original-public-get-settings','observed':settings})
  rc,rh,ra,rt=self.consumer();identity=direct.execute('SELECT session_user,current_user,pg_backend_pid()').fetchone();self.assertEqual(identity[:2],('graph_direct','graph_direct'));observations.append({'id':'ordinary-native-session','observed':list(identity)})
  flags=direct.execute('SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone();self.assertEqual(flags,(False,False));observations.append({'id':'ordinary-native-flags','observed':list(flags)})
  ordinary=direct.execute(query).fetchall();self.assertEqual(ordinary,[('yes',)]);observations.append({'id':'ordinary-direct-graph-rows','observed':[list(r) for r in ordinary]})
  count=direct.execute('SELECT count(*) FROM truss.object').fetchone()[0];self.assertEqual(count,1);observations.append({'id':'ordinary-direct-graph-count','observed':count})
  from truss import Error
  ids={r[1]:int(r[0]) for r in self.admin.execute('SELECT native_id,label FROM ('+sql['sourceSql']+') original_graph').fetchall()}
  for label in ['yes','no']:
   read=ra.get_object_in_transaction(rt,document_id='adoc',module_id='m',record_id='A',object_id=ids[label]);self.assertIsInstance(read,Error);self.assertEqual(read.error.sql_state,'42501');self.assertIn('row-level security policy',str(ra._host._custody.last_attempt.error));observations.append({'id':'ordinary-public-get-'+label+'-composition-refusal','observed':{'sqlState':read.error.sql_state,'outcome':'contained-refusal'}})
  # Experimental routine-setting change only in this disposable installation.
  self.admin.execute('ALTER FUNCTION truss.get_object(text,text,text,bigint,integer,text,text) SET row_security=on')
  from truss import ObjectFound,ObjectNotFound
  for label,expected in [('yes',ObjectFound),('no',ObjectNotFound)]:
   read=ra.get_object_in_transaction(rt,document_id='adoc',module_id='m',record_id='A',object_id=ids[label]);self.assertIsInstance(read,Ok);self.assertIsInstance(read.value,expected);observations.append({'id':'experimental-filtered-public-get-'+label,'observed':type(read.value).__name__})
  self.admin.execute('BEGIN');self.admin.execute('UPDATE truss.object SET props=props-%s WHERE id=%s',(props['flag'],ids['no']));self.admin.commit()
  complete=self.admin.execute(sql['validitySql']).fetchone()[0];self.assertEqual(complete,'false');observations.append({'id':'hidden-malformed-source-invalid','observed':complete})
  read=ra.get_object_in_transaction(rt,document_id='adoc',module_id='m',record_id='A',object_id=ids['yes']);self.assertIsInstance(read,Ok);self.assertIsInstance(read.value,ObjectFound);observations.append({'id':'filtered-public-get-alone-misses-hidden-malformation','observed':'ObjectFound','qualification':'counterexample to filtered read implying complete source'})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s',(props['flag'],json.dumps({'kind':'boolean','value':False}),ids['no']))
  # Bounded selected-source exclusion experiment; no role/policy authority claim.
  import threading,time
  writer=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self.addCleanup(writer.close)
  writer_pid=writer.execute('SELECT pg_backend_pid()').fetchone()[0];errors=[]
  def mutate_hidden():
   try:writer.execute('UPDATE truss.object SET props=props-%s WHERE id=%s',(props['flag'],ids['no']))
   except Exception as exc:errors.append(type(exc).__name__)
  self.admin.execute('BEGIN');self.admin.execute('LOCK TABLE truss.object,truss.prop_def,truss.type_def IN SHARE MODE')
  thread=threading.Thread(target=mutate_hidden);thread.start()
  try:
   deadline=time.monotonic()+5;waiting=None
   while time.monotonic()<deadline:
    waiting=self.admin.execute("SELECT mode,granted FROM pg_locks WHERE pid=%s AND relation='truss.object'::regclass AND mode='RowExclusiveLock'",(writer_pid,)).fetchone()
    if waiting==( 'RowExclusiveLock',False):break
    time.sleep(.01)
   self.assertEqual(waiting,('RowExclusiveLock',False));observations.append({'id':'concurrent-hidden-writer-native-lock-wait','writerPid':writer_pid,'observed':list(waiting)})
   held=self.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND mode='ShareLock' AND granted AND relation IN ('truss.object'::regclass,'truss.prop_def'::regclass,'truss.type_def'::regclass)").fetchone()[0];self.assertEqual(held,3);observations.append({'id':'complete-selected-source-locks-held','observed':held})
   valid=self.admin.execute(sql['validitySql']).fetchone()[0];self.assertEqual(valid,'true');observations.append({'id':'complete-preflight-during-writer-exclusion','observed':valid})
   read=ra.get_object_in_transaction(rt,document_id='adoc',module_id='m',record_id='A',object_id=ids['yes']);self.assertIsInstance(read,Ok);self.assertIsInstance(read.value,ObjectFound);self.assertTrue(thread.is_alive());observations.append({'id':'public-read-returns-before-hidden-writer-release','observed':'ObjectFound'})
  finally:
   self.admin.rollback();thread.join(12)
  self.assertFalse(thread.is_alive());self.assertEqual(errors,[]);observations.append({'id':'writer-completes-after-source-guard-release','observed':'committed'})
  valid=self.admin.execute(sql['validitySql']).fetchone()[0];self.assertEqual(valid,'false');observations.append({'id':'next-source-preflight-detects-post-release-malformation','observed':valid})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s',(props['flag'],json.dumps({'kind':'boolean','value':False}),ids['no']))
  # Partial acquisition failure must contain only the guard's savepoint work.
  guard=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self.addCleanup(guard.close)
  guard_pid=guard.execute('SELECT pg_backend_pid()').fetchone()[0]
  writer.execute('BEGIN');writer.execute('LOCK TABLE truss.object IN ROW EXCLUSIVE MODE')
  try:
   guard.execute('BEGIN');guard.execute("CREATE TEMP TABLE prior_guard_work(value text);INSERT INTO prior_guard_work VALUES('kept')");guard.execute('SAVEPOINT source_timeout');guard.execute("SET LOCAL lock_timeout='150ms'")
   with self.assertRaises(psycopg.errors.LockNotAvailable) as failure:guard.execute('LOCK TABLE truss.prop_def,truss.type_def,truss.object IN SHARE MODE')
   self.assertEqual(failure.exception.sqlstate,'55P03');observations.append({'id':'source-exclusion-finite-lock-timeout','observed':failure.exception.sqlstate,'readIssued':False})
   guard.execute('ROLLBACK TO SAVEPOINT source_timeout')
   held=guard.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND mode='ShareLock' AND granted AND relation IN ('truss.object'::regclass,'truss.prop_def'::regclass,'truss.type_def'::regclass)").fetchone()[0];self.assertEqual(held,0);observations.append({'id':'timeout-savepoint-releases-partial-source-locks','observed':held})
   prior=guard.execute('TABLE prior_guard_work').fetchall();self.assertEqual(prior,[('kept',)]);observations.append({'id':'timeout-preserves-prior-transaction-work','observed':[list(r) for r in prior]})
   guard.execute('SAVEPOINT source_cancel');guard.execute("SET LOCAL lock_timeout='10s'");cancel_errors=[]
   def acquire_for_cancel():
    try:guard.execute('LOCK TABLE truss.prop_def,truss.type_def,truss.object IN SHARE MODE')
    except psycopg.Error as exc:cancel_errors.append(exc.sqlstate)
   cancel_thread=threading.Thread(target=acquire_for_cancel);cancel_thread.start()
   try:
    deadline=time.monotonic()+5;waiting=None
    while time.monotonic()<deadline:
     waiting=self.admin.execute("SELECT mode,granted FROM pg_locks WHERE pid=%s AND relation='truss.object'::regclass AND mode='ShareLock'",(guard_pid,)).fetchone()
     if waiting==('ShareLock',False):break
     time.sleep(.01)
    self.assertEqual(waiting,('ShareLock',False));observations.append({'id':'cancel-guard-native-lock-wait','observed':list(waiting)})
    partial=self.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=%s AND mode='ShareLock' AND granted AND relation IN ('truss.prop_def'::regclass,'truss.type_def'::regclass)",(guard_pid,)).fetchone()[0];self.assertEqual(partial,2);observations.append({'id':'cancel-guard-holds-two-partial-source-locks','observed':partial})
   finally:
    guard.cancel();cancel_thread.join(12)
   self.assertFalse(cancel_thread.is_alive());self.assertEqual(cancel_errors,['57014']);observations.append({'id':'source-exclusion-cancellation','observed':cancel_errors,'readIssued':False})
   guard.execute('ROLLBACK TO SAVEPOINT source_cancel')
   held=guard.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND mode='ShareLock' AND granted AND relation IN ('truss.object'::regclass,'truss.prop_def'::regclass,'truss.type_def'::regclass)").fetchone()[0];self.assertEqual(held,0);observations.append({'id':'cancel-savepoint-releases-partial-source-locks','observed':held})
   prior=guard.execute('TABLE prior_guard_work').fetchall();self.assertEqual(prior,[('kept',)]);observations.append({'id':'cancel-preserves-prior-transaction-work','observed':[list(r) for r in prior]})
   guard.execute('COMMIT')
  finally:
   guard.rollback();writer.rollback()
  self.admin.execute('ALTER FUNCTION truss.get_object(text,text,text,bigint,integer,text,text) SET row_security=off')
  settings=self.admin.execute("SELECT proconfig FROM pg_proc WHERE oid='truss.get_object(text,text,text,bigint,integer,text,text)'::regprocedure").fetchone()[0];self.assertIn('row_security=off',settings);observations.append({'id':'original-complete-read-settings-restored','observed':settings})
  # Narrow read-owner feasibility; fixed test entrypoint, not a released API.
  rh.detach();rc.commit() # Drain earlier reads before native policy DDL.
  self.admin.execute('CREATE ROLE graph_read_owner NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;GRANT USAGE ON SCHEMA truss TO graph_read_owner;GRANT SELECT(id,type_id,props) ON truss.object TO graph_read_owner')
  self.addCleanup(self.admin.execute,'DROP OWNED BY graph_read_owner;DROP ROLE graph_read_owner')
  self.admin.execute("CREATE POLICY graph_read_context ON truss.object AS RESTRICTIVE FOR SELECT TO graph_read_owner USING(current_user='graph_read_owner' AND session_user='consumer')")
  body='SELECT q.label FROM ('+sql['sourceSql']+') q WHERE q.value OPERATOR(pg_catalog.=) $1 AND q.label OPERATOR(pg_catalog.=) $2'
  self.admin.execute('CREATE FUNCTION public.graph_read(text,text) RETURNS TABLE(label text) LANGUAGE SQL SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=on AS $$ '+body+' $$;REVOKE ALL ON FUNCTION public.graph_read(text,text) FROM PUBLIC;GRANT EXECUTE ON FUNCTION public.graph_read(text,text) TO consumer;GRANT CREATE ON SCHEMA public TO graph_read_owner;ALTER FUNCTION public.graph_read(text,text) OWNER TO graph_read_owner;REVOKE CREATE ON SCHEMA public FROM graph_read_owner')
  owner=self.admin.execute("SELECT r.rolcanlogin,r.rolinherit,r.rolsuper,r.rolcreatedb,r.rolcreaterole,r.rolreplication,r.rolbypassrls,p.prosecdef,p.proconfig FROM pg_roles r JOIN pg_proc p ON p.proowner=r.oid WHERE p.oid='public.graph_read(text,text)'::regprocedure").fetchone();self.assertEqual(owner[:8],(False,False,False,False,False,False,False,True));self.assertIn('row_security=on',owner[8]);observations.append({'id':'narrow-read-owner-and-routine-settings','observed':list(owner)})
  privileges=self.admin.execute("SELECT has_table_privilege('graph_read_owner','truss.object','SELECT'),has_column_privilege('graph_read_owner','truss.object','props','SELECT'),has_column_privilege('graph_read_owner','truss.object','retained','SELECT'),has_table_privilege('graph_read_owner','truss.object','INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN'),has_table_privilege('graph_read_owner','truss.journal','SELECT'),has_sequence_privilege('graph_read_owner','truss.id_seq','USAGE,SELECT,UPDATE'),has_schema_privilege('graph_read_owner','truss','CREATE'),has_schema_privilege('graph_read_owner','public','CREATE')").fetchone();self.assertEqual(privileges,(False,True,False,False,False,False,False,False));observations.append({'id':'narrow-read-owner-native-privileges','observed':list(privileges)})
  rc,rh,ra,rt=self.consumer()
  for label,expected in [('yes',[('yes',)]),('no',[]),('not-present',[])]:
   rows=rc.execute('SELECT label FROM public.graph_read(%s,%s)',('value',label)).fetchall();self.assertEqual(rows,expected);observations.append({'id':'narrow-owner-original-caller-lookup-'+label,'observed':[list(r) for r in rows]})
  rows=rc.execute('SELECT label FROM public.graph_read(%s,%s)',("value' OR true --",'no')).fetchall();self.assertEqual(rows,[]);observations.append({'id':'narrow-owner-exact-key-parameter','observed':rows})
  membership=rc.execute("SELECT pg_has_role(session_user,'graph_read_owner','MEMBER'),has_function_privilege(session_user,'public.graph_read(text,text)','EXECUTE')").fetchone();self.assertEqual(membership,(False,True));observations.append({'id':'ordinary-caller-invokes-without-owner-membership','observed':list(membership)})
  probe_params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);probe_params['user']='consumer'
  with psycopg.connect(**probe_params,autocommit=True) as probe:
   for name,statement in [('set-read-owner','SET ROLE graph_read_owner'),('direct-property-bag','SELECT props FROM truss.object'),('direct-retained','SELECT retained FROM truss.object'),('direct-journal','SELECT * FROM truss.journal')]:
    with self.assertRaises(psycopg.errors.InsufficientPrivilege) as failure:probe.execute(statement)
    self.assertEqual(failure.exception.sqlstate,'42501');observations.append({'id':'ordinary-narrow-owner-boundary-'+name,'observed':failure.exception.sqlstate})
  with self.assertRaises(psycopg.errors.InsufficientPrivilege) as failure:direct.execute("SELECT * FROM public.graph_read('value','yes')")
  self.assertEqual(failure.exception.sqlstate,'42501');observations.append({'id':'ungranted-original-caller-entrypoint-refuses','observed':failure.exception.sqlstate})
  self.admin.execute('CREATE ROLE graph_wrapper_owner NOLOGIN NOINHERIT NOSUPERUSER NOBYPASSRLS;GRANT EXECUTE ON FUNCTION public.graph_read(text,text) TO graph_wrapper_owner;CREATE FUNCTION public.graph_read_wrapper() RETURNS TABLE(label text) LANGUAGE SQL SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ SELECT label FROM public.graph_read('value','yes') $$;REVOKE ALL ON FUNCTION public.graph_read_wrapper() FROM PUBLIC;GRANT EXECUTE ON FUNCTION public.graph_read_wrapper() TO consumer,graph_direct;GRANT CREATE ON SCHEMA public TO graph_wrapper_owner;ALTER FUNCTION public.graph_read_wrapper() OWNER TO graph_wrapper_owner;REVOKE CREATE ON SCHEMA public FROM graph_wrapper_owner')
  self.addCleanup(self.admin.execute,'DROP OWNED BY graph_wrapper_owner;DROP ROLE graph_wrapper_owner')
  rows=rc.execute('SELECT label FROM public.graph_read_wrapper()').fetchall();self.assertEqual(rows,[('yes',)]);observations.append({'id':'nested-definer-keeps-authorized-original-caller','observed':[list(r) for r in rows]})
  rows=direct.execute('SELECT label FROM public.graph_read_wrapper()').fetchall();self.assertEqual(rows,[]);observations.append({'id':'nested-definer-cannot-substitute-owner-for-original-caller','observed':rows})
  forged=direct.execute("SELECT public.graph_candidate('value','no',true)").fetchone()[0];self.assertIs(forged,True);observations.append({'id':'forged-expression-alone-is-not-authority','observed':forged})
  rows=direct.execute("SELECT id FROM truss.object WHERE id=%s AND public.graph_candidate('value','no',true)",(ids['no'],)).fetchall();self.assertEqual(rows,[]);observations.append({'id':'forged-argument-cannot-bypass-original-row-policy','observed':rows})
  admin_count=self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0];self.assertEqual(admin_count,2);observations.append({'id':'excluded-admin-bypass','observed':admin_count})
  rh.detach();rc.commit()
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']).write_text(json.dumps({'packet':packet,'sql':sql,'observations':observations,'scope':'Actual public creation, candidate projection and forced native RLS with an ordinary direct graph reader. Current public get API refuses forced RLS because its complete-read profile sets row_security=off; no API RLS composition qualified. Isolated Boolean attribute fixture, not ontology membership or complete graph admission. Global source validity is excluded-assessor preflight and must precede filtering.','cleanup':'Native unittest fixture cleanup'},indent=2)+'\n')
if __name__=='__main__':
 import unittest;unittest.main()
