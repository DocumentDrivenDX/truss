"""Original preflight ordering control; native completeness is still required."""
import os,json,subprocess,unittest
from pathlib import Path
from security_relational_capture import capture_relational_operands
from security_relational_codecs import prepare_owned_relational_codec_checker

class RelationalCaptureTests(unittest.TestCase):
 def test_preflight_precedes_every_cursor_statement(self):
  binary=os.environ.get('TRUSS_SECURITY_RELATIONAL_COMPILER_BINARY')
  if not binary:self.skipTest('Original relational producer required')
  root=Path(__file__).resolve().parents[3]
  request=(root/'docs/helix/04-build/evidence/security-graph-subject-registration-20261014/compiler-request.json').read_bytes()
  output=subprocess.run([binary],input=request,capture_output=True,check=True,timeout=15).stdout
  checker=prepare_owned_relational_codec_checker(Path(binary).with_name('security_postgresql_codecs'))
  calls=[]
  def stop_after_actual_preflight(*args):
   checker(*args);calls.append('original-preflight')
   raise ValueError('test stops after original preflight')
  class NoSQL:
   def execute(self,*args,**kwargs):raise AssertionError('SQL before preflight')
  with self.assertRaisesRegex(ValueError,'test stops after original preflight'):
   capture_relational_operands(NoSQL(),request,output,1,stop_after_actual_preflight)
  self.assertEqual(calls,['original-preflight'])
