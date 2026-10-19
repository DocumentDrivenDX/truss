# SPDX-License-Identifier: MIT OR Apache-2.0
"""Compiler-backed pre-SQL refusal; no native authentication claim."""
import json,os,unittest,subprocess
from pathlib import Path
from truss._security_guarded_source import capture_guarded_source_comparison,GuardedSourceComparison
from security_ontology_compiled_read import prepare_owned_graph_compiler

class GuardedPreflightTests(unittest.TestCase):
 def test_wrong_original_source_refuses_before_cursor(self):
  binary=os.environ.get('TRUSS_SECURITY_GUARDED_COMPILER_BINARY')
  if not binary:self.skipTest('Original guarded compiler required')
  root=Path(__file__).resolve().parents[3]
  evidence=root/'docs/helix/04-build/evidence/security-graph-subject-registration-20261014'
  original=(evidence/'compiler-request.json').read_bytes()
  output=subprocess.run([binary],input=original,capture_output=True,check=True,timeout=15).stdout
  comparison=capture_guarded_source_comparison(original,output)
  # A valid digest over different original bytes is still the wrong source.
  from hashlib import sha256
  wrong=comparison.source_bytes+b' '
  comparison=GuardedSourceComparison(wrong,sha256(wrong).hexdigest())
  compiler=prepare_owned_graph_compiler(binary,str(Path(binary).with_name('security_guarded_result')),guarded=True,source_comparison=comparison)
  class NoSQL:
   calls=0
   def execute(self,*args,**kwargs):
    self.calls+=1
    raise AssertionError('Compiled SQL reached native cursor before source comparison')
  cursor=NoSQL()
  request=(evidence/'physical-request.json').read_bytes()
  binding=json.loads(json.loads(original)['bindingJson'])
  assessment=binding['inventoryJson'].encode()
  with self.assertRaisesRegex(ValueError,'Original selected guarded source changed'):
   compiler(cursor,request,(assessment,), 'Bob',{})
  self.assertEqual(cursor.calls,0)
  with self.assertRaises(ValueError):prepare_owned_graph_compiler(binary,str(Path(binary).with_name('security_guarded_result')),guarded=True)
