"""Real packaged UMF + native Weft bridge; explicitly simulated SQL cursor.

Opt in with TRUSS_DISCLOSURE_COMPONENT_QUALIFICATION=1 and the reviewed
presence wheel installed. No SQL executes and no native authority is proved.
"""
import os,json,pathlib,time,types,unittest
from unittest.mock import patch
import truss._current_disclosure_evaluation as evaluation
import truss._current_disclosure_stage as staging
from truss._current_disclosure_originals import prepare_current_disclosure_originals,check_disclosure_originals,_actual_disclosure_consumer
from truss._current_query_sources import _DISCLOSURE_PROFILE,_initialize
from truss._current_query_evaluation import wire
from _current_disclosure_simulated_cursor import StageCursor,Raw
fixture=pathlib.Path(__file__).with_name('fixtures')/'current-disclosure'
corpus=json.loads((fixture/'actual-atomic-transport.json').read_bytes())
vectors=json.loads((fixture/'native-disclosure-child-vectors.json').read_bytes())
packets={p['id']:p for p in vectors['packets']}
class Cursor(StageCursor):
 def execute(self,query,parameters=None,**kw):
  if query=='SELECT pg_catalog.pg_current_xact_id()::pg_catalog.text':self.out=('fixture-generation',);return self
  return super().execute(query,parameters,**kw)
@unittest.skipUnless(os.environ.get('TRUSS_DISCLOSURE_COMPONENT_QUALIFICATION')=='1','requires explicitly selected reviewed local presence wheel')
class DisclosureCompilerIntegrationTests(unittest.TestCase):
 def setUp(self):
  _actual_disclosure_consumer()
 def test_actual_held_evaluation_compiler_and_checker(self):
  passed=refused=fresh_generation=0
  for case in corpus['cases']:
   packet=packets[case['id']];source=vectors['sources'][packet['sourceIndex']]
   expected=case['result']
   if case['id'].startswith('stale-generation:'):
    # The host does not accept either fixture generation token. It supplies
    # one current native generation to both fields. Compare the unchanged
    # facts/subject/sources to an independent matching non-stale vector.
    normalized=lambda cut:{k:v for k,v in cut.items() if k not in ('generation','expectedGeneration')}
    matches=[p for p in vectors['packets'] if not p['id'].startswith('stale-generation:') and p['sourceIndex']==packet['sourceIndex'] and p['selection']==packet['selection'] and normalized(p['cut'])==normalized(packet['cut'])]
    assert matches and all(p['result']==matches[0]['result'] for p in matches)
    expected=matches[0]['result'];fresh_generation+=1
   initial=wire({'kind':'initialize','requestId':'registered','sources':{**{k:source[k] for k in ('policy','catalog','closure','ontology')},'associationBindings':[],'extensionSelection':{}}})
   sources=types.SimpleNamespace(source_profile=_DISCLOSURE_PROFILE,query_originals=prepare_current_disclosure_originals(wire(case['request']['opaqueSources'])),accepted_request_bytes=wire({'modules':case['request']['modules']}),initialize_bytes=initial,source_receipt=_initialize(initial))
   check_disclosure_originals(sources.query_originals,initial,sources.accepted_request_bytes)
   captured=types.SimpleNamespace(sources=sources,facts_bytes=wire(packet['cut']['facts']),coverage_bytes=wire(packet['cut']['coverage']))
   subject=types.SimpleNamespace(key=packet['cut']['subject']['key'][0]['string'])
   cursor=Cursor('good');cursor._deadline.end=time.monotonic()+60
   with self.subTest(case=case['id']),patch.object(staging,'RawCursor',Raw),patch.object(staging,'_text_rows',return_value=[('pg_temp_7',)]):
    def invoke():return evaluation.evaluate_and_stage_current_disclosure(cursor,captured,subject,sql=case['request']['sql'],parameters={},document_ids=tuple(m['pin']['documentId'] for m in case['request']['modules']),bun_executable='/opt/homebrew/bin/bun',maximum_rows=4096,maximum_scan_rows=4096,maximum_bytes=8_000_000)
    if expected['status']=='rendered':
     result=invoke();result.require_original_parent();self.assertEqual(json.loads(result.staged.reconstructed_batch),expected['batch']);self.assertTrue(cursor.dropped);passed+=1
    else:
     with self.assertRaises(ValueError):invoke()
     self.assertFalse(cursor.dropped);refused+=1
  self.assertEqual((passed,refused,fresh_generation),(46,20,6))

if __name__=='__main__':unittest.main()
