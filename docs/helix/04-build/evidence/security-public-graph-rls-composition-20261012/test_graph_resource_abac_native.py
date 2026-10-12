"""Actual public-created graph values; candidate source correctness, not policy admission."""
import json,subprocess
from pathlib import Path
from dataclasses import replace
from truss import Ok
from truss.contracts import BooleanValue
from truss.groups import AuthoredValue,GroupSuccess,RequestNone
import test_group_create_native as groups
class GraphABACTests(groups.PublicCreateGroupTests):
 for name in tuple(n for n in dir(groups.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None
 def source(self,document):
  m=document['modules'][0];record=next(e for e in m['elements'] if e['id']=='A');m['elements'].append({'id':'A-flag','kind':'field','name':'flag','scalarType':'boolean','cardinality':'one','nullability':'required','extensions':{}});record['members'].append({'module':'m','element':'A-flag'})
 def test_public_graph_creation_and_original_source_validity(self):
  c,host,assembly,tx=self.ready(self.source)
  operations=tuple(replace(self.create(label=label,alias=label),values=self.create(label=label,alias=label).values+(AuthoredValue(name='flag',value=BooleanValue(value=flag)),)) for label,flag in [('yes',True),('no',False)])
  inp,_=self.input(assembly,tx,operations);result=assembly.apply_in_transaction(tx,inp,RequestNone(),documents=self.documents,bun_executable='/opt/homebrew/bin/bun');self.assertIsInstance(result,Ok);self.assertIsInstance(result.value,GroupSuccess);host.detach();c.commit()
  type_id=self.types[('adoc','A')].type_id
  props={row[0]:str(row[1]) for row in self.admin.execute('SELECT name,prop_id FROM truss.prop_def WHERE type_id=%s',(int(type_id),))};packet={'typeId':type_id,'valueId':props['A-value'],'labelId':props['A-label'],'flagId':props['flag']}
  run=subprocess.run(['/opt/homebrew/bin/bun','/private/tmp/truss-graph-abac-produce.ts'],input=json.dumps(packet),text=True,capture_output=True,timeout=30);self.assertEqual(run.returncode,0,run.stderr);sql=json.loads(run.stdout);observations=[]
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
  forged=direct.execute("SELECT public.graph_candidate('value','no',true)").fetchone()[0];self.assertIs(forged,True);observations.append({'id':'forged-expression-alone-is-not-authority','observed':forged})
  rows=direct.execute("SELECT id FROM truss.object WHERE id=%s AND public.graph_candidate('value','no',true)",(ids['no'],)).fetchall();self.assertEqual(rows,[]);observations.append({'id':'forged-argument-cannot-bypass-original-row-policy','observed':rows})
  admin_count=self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0];self.assertEqual(admin_count,2);observations.append({'id':'excluded-admin-bypass','observed':admin_count})
  rh.detach();rc.commit()
  Path('/private/tmp/truss-graph-abac-native.json').write_text(json.dumps({'packet':packet,'sql':sql,'observations':observations,'scope':'Actual public creation, candidate projection and forced native RLS with an ordinary direct graph reader. Current public get API refuses forced RLS because its complete-read profile sets row_security=off; no API RLS composition qualified. Isolated Boolean attribute fixture, not ontology membership or complete graph admission. Global source validity is excluded-assessor preflight and must precede filtering.','cleanup':'Native unittest fixture cleanup'},indent=2)+'\n')
if __name__=='__main__':
 import unittest;unittest.main()
