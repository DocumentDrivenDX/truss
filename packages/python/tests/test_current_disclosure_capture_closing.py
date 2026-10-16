"""Private recapture comparison only; supplied values are not native evidence."""
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
import unittest
from truss._current_disclosure_facts import CurrentDisclosureFactCapture,verify_current_disclosure_capture_with_cursor

class CaptureClosingTests(unittest.TestCase):
 def setUp(self):
  self.checks=[]
  self.cursor=SimpleNamespace(_deadline=SimpleNamespace(check=lambda:self.checks.append('check')))
  self.capture=CurrentDisclosureFactCapture(object(),b'[{"exact":9007199254740993}]',b'[]',
      (('1','2','3',b'receipt',b'namespace',b'tuple'),),b'[]',b'[]',(('4','5','6','1','2','7','8'),))
 def test_original_recapture_must_match_every_component(self):
  changes={'sources':object(),'facts_bytes':b'[]','coverage_bytes':b'[{}]','rows':(),
           'graphs_bytes':b'[{}]','graph_coverage_bytes':b'[{}]','graph_rows':()}
  with patch('truss._current_disclosure_facts.capture_current_disclosure_facts_with_cursor',return_value=self.capture) as capture:
   self.assertIsNone(verify_current_disclosure_capture_with_cursor(self.cursor,self.capture,bun_executable='selected-bun'))
   capture.assert_called_once_with(self.cursor,bun_executable='selected-bun')
  self.assertEqual(self.checks,['check','check'])
  for name,value in changes.items():
   with self.subTest(component=name),patch('truss._current_disclosure_facts.capture_current_disclosure_facts_with_cursor',return_value=replace(self.capture,**{name:value})):
    with self.assertRaisesRegex(ValueError,'changed before closing'):
     verify_current_disclosure_capture_with_cursor(self.cursor,self.capture)
 def test_raw_or_subclass_or_missing_capture_cannot_claim_graph_closing(self):
  from truss._current_query_facts import CurrentQueryFactCapture
  class Derived(CurrentDisclosureFactCapture):pass
  for capture in (None,{},CurrentQueryFactCapture(object(),b'[]',b'[]',()),Derived(*[getattr(self.capture,n) for n in self.capture.__dataclass_fields__])):
   with self.subTest(type=type(capture)),patch('truss._current_disclosure_facts.capture_current_disclosure_facts_with_cursor') as native:
    with self.assertRaisesRegex(ValueError,'capture profile required'):
     verify_current_disclosure_capture_with_cursor(self.cursor,capture)
    native.assert_not_called()
 def test_recapture_failure_and_expiry_are_not_normalized_to_success(self):
  with patch('truss._current_disclosure_facts.capture_current_disclosure_facts_with_cursor',side_effect=ValueError('incomplete census')):
   with self.assertRaisesRegex(ValueError,'incomplete census'):verify_current_disclosure_capture_with_cursor(self.cursor,self.capture)
  for fail_at in (1,2):
   calls=[]
   def deadline():
    calls.append(None)
    if len(calls)==fail_at:raise TimeoutError('closing expired')
   self.cursor._deadline.check=deadline
   with self.subTest(fail_at=fail_at),patch('truss._current_disclosure_facts.capture_current_disclosure_facts_with_cursor',return_value=self.capture) as native:
    with self.assertRaises(TimeoutError):verify_current_disclosure_capture_with_cursor(self.cursor,self.capture)
    self.assertEqual(native.call_count,fail_at-1)

if __name__=='__main__':unittest.main()
