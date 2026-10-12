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
  restored=self.admin.execute(sql['validitySql']).fetchone()[0];self.assertEqual(restored,'true');observations.append({'id':'restored-original-source','observed':restored})
  Path('/private/tmp/truss-graph-abac-native.json').write_text(json.dumps({'packet':packet,'sql':sql,'observations':observations,'scope':'Actual public catalog/group creation with excluded assessor candidate projection and expression. Not ordinary graph policy/source-authority admission. Global validity must precede filtering.','cleanup':'Native unittest fixture cleanup'},indent=2)+'\n')
if __name__=='__main__':
 import unittest;unittest.main()
