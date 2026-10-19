# SPDX-License-Identifier: MIT OR Apache-2.0
"""Supplied population correspondence controls; no native capture authority."""
import copy,json,os,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from truss._current_disclosure_context_capture import _join_population,_inputs,ContextDisclosureCapture,verify_context_disclosure_with_cursor
from truss._current_disclosure_originals import CurrentDisclosureOriginals
from truss._current_disclosure_evaluation import evaluate_and_stage_current_disclosure
ROOT=Path(__file__).resolve().parents[3]/'docs/helix/04-build/evidence'
wire=lambda x:json.dumps(x,separators=(',',':')).encode()

class PopulationTests(unittest.TestCase):
 def setUp(self):
  defs=ROOT/'native-graph-definition-join-20261016';base=ROOT/'actual-graph-requirements-20261016'
  self.definitions=SimpleNamespace(report=(defs/'graph-report.json').read_bytes(),model=SimpleNamespace(report=(defs/'model-report.json').read_bytes(),requirements=(base/'issued-model-requirements.json').read_bytes()),requirements=(base/'issued-graph-requirements.json').read_bytes())
  import zipfile
  archive=ROOT/'graph-closing-recapture-20261016/native-inputs-and-results.zip'
  # Original source campaign is retained under its manifest-relative paths.
  with zipfile.ZipFile(archive) as z:
   names=z.namelist()
   def load(name):return z.read(next(n for n in names if n.endswith('native-inputs-base/'+name)))
   locators=json.loads(load('native-locators.json'))
   request=json.loads((base/'original-request.json').read_bytes())
   sources=SimpleNamespace(source_profile='truss-current-disclosure-sources/0.1-candidate',query_originals=CurrentDisclosureOriginals(wire(request['opaqueSources']),b'{}'),accepted_request_bytes=(base/'retained-native-accepted-request.json').read_bytes())
   self.captured=SimpleNamespace(sources=sources,facts_bytes=load('facts.json'),coverage_bytes=load('coverage.json'),rows=tuple(tuple(r) for r in locators['objects']),graphs_bytes=load('graphs.json'),graph_coverage_bytes=load('graph-coverage.json'),graph_rows=tuple(tuple(r) for r in locators['edges']))
 def test_complete_fourteen_objects_twelve_edges_and_parallel_occurrence(self):
  _join_population(self.definitions,self.captured)
  c=copy.copy(self.captured);rows=list(c.graph_rows);row=list(rows[0]);row[0]='999999';rows.append(tuple(row));c.graph_rows=tuple(rows)
  logical=json.loads(c.graphs_bytes);extra=copy.deepcopy(logical[0]);extra['witness']['id']='999999';logical.append(extra);c.graphs_bytes=wire(logical)
  _join_population(self.definitions,c)
 def test_coverage_field_order_is_not_key_component_order(self):
  c=copy.copy(self.captured);coverage=json.loads(c.coverage_bytes)
  for row in coverage:row['fields'].reverse()
  c.coverage_bytes=wire(coverage);_join_population(self.definitions,c)
  for edit in [lambda a:a[0]['fields'].append(copy.deepcopy(a[0]['fields'][0])),lambda a:a[0]['fields'][0].update(elementId='foreign'),lambda a:a[0]['fields'][0].update(moduleId='foreign')]:
   bad=copy.deepcopy(coverage);edit(bad);c.coverage_bytes=wire(bad)
   with self.assertRaises(ValueError):_join_population(self.definitions,c)
 def test_missing_coverage_duplicate_coverage_and_wrong_complete_flag_refuse(self):
  for name in ['coverage_bytes','graph_coverage_bytes']:
   for edit in [lambda a:a.pop(),lambda a:a.append(copy.deepcopy(a[0])),lambda a:a[0].update(complete=1)]:
    c=copy.copy(self.captured);value=json.loads(getattr(c,name));edit(value);setattr(c,name,wire(value))
    with self.subTest(name=name),self.assertRaises(ValueError):_join_population(self.definitions,c)
 def test_native_and_logical_occurrence_census_and_identity_refuse(self):
  for name in ['rows','graph_rows']:
   c=copy.copy(self.captured);setattr(c,name,getattr(c,name)[:-1])
   with self.subTest(name=name),self.assertRaises(ValueError):_join_population(self.definitions,c)
  for index,value in [(0,'foreign-witness'),(1,'9999'),(3,'9999'),(4,'9999'),(5,'9999'),(6,'9999')]:
   c=copy.copy(self.captured);rows=list(c.graph_rows);row=list(rows[0]);row[index]=value;rows[0]=tuple(row);c.graph_rows=tuple(rows)
   with self.subTest(index=index),self.assertRaises(ValueError):_join_population(self.definitions,c)
 def test_changed_logical_endpoint_key_witness_role_or_relationship_refuse(self):
  for edit in [lambda r:r['endpoints'][0].update(key=[{'string':'foreign'}]),lambda r:r['witness'].update(id='foreign'),lambda r:r['endpoints'][0].update(role='foreign'),lambda r:r['relationship'].update(relationshipId='foreign')]:
   c=copy.copy(self.captured);rows=json.loads(c.graphs_bytes);edit(rows[0]);c.graphs_bytes=wire(rows)
   with self.assertRaisesRegex(ValueError,'projection correspondence'):_join_population(self.definitions,c)
 def test_query_input_model_closure_parameters_and_profile_refuse(self):
  for params,docs in [({'x':1},('adoc',)),({},('foreign',))]:
   with self.assertRaises(ValueError):_inputs(self.captured.sources,'SELECT r.salary FROM Resource r',params,docs)
  sources=copy.copy(self.captured.sources);sources.source_profile='other'
  with self.assertRaises(ValueError):_inputs(sources,'x',{},('adoc',))
 def test_wrong_closing_profile_refuses_before_cursor_inspection(self):
  with self.assertRaisesRegex(ValueError,'Original context disclosure'):verify_context_disclosure_with_cursor(object(),self.captured)

@unittest.skipUnless(os.environ.get('TRUSS_GRAPH_JOIN_WEFT_QUALIFICATION')=='1','explicit actual Graph wheel required')
class ActualContextTests(PopulationTests):
 for name in tuple(n for n in dir(PopulationTests) if n.startswith('test_')):locals()[name]=None
 def test_sql_substitution_refuses_without_repreparing_parent_or_child(self):
  import weft,weft.weft as native
  raw,_,_,_=_inputs(self.captured.sources,'SELECT r.salary FROM Resource r',{},('adoc',));parent=weft.prepare_application_lineage(raw.decode());current=parent.prepare_current_presence()
  self.definitions.model.current=current;self.definitions.model.parent=parent;self.definitions.requirements=current.graph_requirements_json().encode()
  wrapped=ContextDisclosureCapture(self.captured,self.definitions);cursor=SimpleNamespace(_deadline=SimpleNamespace(check=lambda:None))
  with patch.object(native,'prepare_application_lineage',side_effect=AssertionError('must retain original parent')),patch('truss._current_disclosure_evaluation.open_current_disclosure_computation',side_effect=AssertionError('must refuse before child')):
   with self.assertRaisesRegex(ValueError,'Original captured compiler context'):evaluate_and_stage_current_disclosure(cursor,wrapped,object(),sql='SELECT r.resourceId FROM Resource r',parameters={},document_ids=('adoc',),bun_executable='unused',maximum_rows=10,maximum_scan_rows=10,maximum_bytes=1000)
