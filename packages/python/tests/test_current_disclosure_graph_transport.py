# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual packaged semantic child; supplied facts, no SQL or native admission."""
import copy,json,os,pathlib,unittest
from truss._current_disclosure_wire import disclosure_fact_cut,frame_digest
from truss._current_disclosure_computation import open_current_disclosure_computation
from truss._current_disclosure_pipe import VERSION

fixture=pathlib.Path(__file__).with_name('fixtures')/'current-disclosure/native-graph-capture.json'
wire=lambda value:json.dumps(value,ensure_ascii=True,separators=(',',':')).encode()

@unittest.skipUnless(os.environ.get('TRUSS_GRAPH_TRANSPORT_COMPONENT_QUALIFICATION')=='1',
                     'requires explicit packaged semantic child component qualification')
class GraphTransportTests(unittest.TestCase):
 def _check_packet(self,packet):
  corpus=json.loads(fixture.read_bytes())
  cut=copy.deepcopy(packet['cut'])
  populations={name:wire(cut.pop(name)) for name in ('facts','coverage','graphs','graphCoverage')}
  raw=disclosure_fact_cut(cut,facts=populations['facts'],coverage=populations['coverage'],
    graphs=populations['graphs'],graph_coverage=populations['graphCoverage'])
  initial=wire(corpus['initialize']);receipt=frame_digest(initial)
  request=wire({'version':VERSION,'kind':'evaluate-disclosure','requestId':'evaluate',
                'sourceReceipt':receipt})[:-1]+b',"cut":'+raw+b'}'
  with open_current_disclosure_computation(bun_executable=os.environ.get('TRUSS_DISCLOSURE_BUN','/opt/homebrew/bin/bun'),timeout_seconds=20) as child:
   self.assertEqual(json.loads(child.exchange(initial,source_receipt=receipt))['kind'],'initialized')
   result=json.loads(child.exchange(request,source_receipt=receipt))
   self.assertEqual(result['kind'],'disclosure-evaluated')
   self.assertEqual(result['result']['status'],'rendered')
   self.assertEqual([r['key'][0]['string'] for r in result['result']['resources']],packet['expectedKeys'])
  self.assertTrue(child._cleanup_complete)

 def test_original_graph_ontology_decisions_use_all_captured_populations(self):
  for packet in json.loads(fixture.read_bytes())['packets']:
   if not packet['id'].startswith('parallel:'):
    with self.subTest(packet=packet['id']):self._check_packet(packet)

 def test_parallel_alice_preserves_required_behavior(self):
  self._check_packet(json.loads(fixture.read_bytes())['packets'][3])
 def test_parallel_bob_preserves_required_behavior(self):
  self._check_packet(json.loads(fixture.read_bytes())['packets'][4])
 def test_parallel_outsider_preserves_required_behavior(self):
  self._check_packet(json.loads(fixture.read_bytes())['packets'][5])

if __name__=='__main__':unittest.main()
