"""Original codec preflight controls; no native population/authority claim."""
import os,json,subprocess,unittest
from pathlib import Path
from security_relational_codecs import prepare_owned_relational_codec_checker

class RelationalCodecTests(unittest.TestCase):
 def test_parameter_and_capture_preflight(self):
  binary=os.environ.get('TRUSS_SECURITY_RELATIONAL_COMPILER_BINARY')
  if not binary:self.skipTest('Original relational producer required')
  root=Path(__file__).resolve().parents[3]
  request=(root/'docs/helix/04-build/evidence/security-graph-subject-registration-20261014/compiler-request.json').read_bytes()
  output=subprocess.run([binary],input=request,capture_output=True,check=True,timeout=15).stdout;packet=json.loads(output)
  check=prepare_owned_relational_codec_checker(Path(binary).with_name('security_postgresql_codecs'))
  self.assertEqual(json.loads(check(request,output))['parameterCount'],1)
  operands=json.dumps({'version':'weft.security.operand-values/0.1-candidate','contextSha256':packet['queryContextSha256'],'scans':[{'scan':r['scan'],'rows':[]} for r in packet['operandReads']]}).encode()
  self.assertEqual(json.loads(check(request,output,operands))['operandCount'],0)
  changed=json.loads(operands);changed['contextSha256']='0'*64
  with self.assertRaisesRegex(ValueError,'Original PostgreSQL codec preflight refused'):check(request,output,json.dumps(changed).encode())
