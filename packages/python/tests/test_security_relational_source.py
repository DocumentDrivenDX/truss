# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original relational source separation and cross-version refusal."""
import json,os,subprocess,unittest
from pathlib import Path
from truss._security_relational_source import capture_relational_source_comparison
from truss._security_guarded_source import capture_guarded_source_comparison

class RelationalSourceTests(unittest.TestCase):
 def test_original_sources_and_protocol_separation(self):
  binary=os.environ.get('TRUSS_SECURITY_RELATIONAL_COMPILER_BINARY')
  if not binary:self.skipTest('Original relational compiler required')
  root=Path(__file__).resolve().parents[3]
  request=(root/'docs/helix/04-build/evidence/security-graph-subject-registration-20261014/compiler-request.json').read_bytes()
  def compile(raw):return subprocess.run([binary],input=raw,capture_output=True,check=True,timeout=15).stdout
  output=compile(request);source=capture_relational_source_comparison(request,output)
  alternative=json.loads(request);alternative['sql']="SELECT r.resourceId FROM Resource r WHERE r.resourceId = 'RB'"
  other=json.dumps(alternative,separators=(',',':')).encode();other_output=compile(other)
  self.assertEqual(capture_relational_source_comparison(other,other_output),source)
  self.assertNotEqual(json.loads(output)['queryContextSha256'],json.loads(other_output)['queryContextSha256'])
  with self.assertRaises(ValueError):capture_guarded_source_comparison(request,output)
  legacy=Path(binary).with_name('security_guarded_candidate')
  legacy_output=subprocess.run([str(legacy)],input=request,capture_output=True,check=True,timeout=15).stdout
  with self.assertRaises(ValueError):capture_relational_source_comparison(request,legacy_output)
  for demand in ('nativeAdmission','nativeCodecAdmission','nativePopulationAndSelection','releaseProtection'):
   changed=json.loads(output);changed[demand]='admitted'
   with self.subTest(demand=demand),self.assertRaises(ValueError):capture_relational_source_comparison(request,json.dumps(changed).encode())
