"""Original compiler correspondence controls; no native admission evidence."""
import json,os,subprocess,unittest
from pathlib import Path
from dataclasses import replace
from truss._security_guarded_source import capture_guarded_source_comparison,require_same_guarded_source

class GuardedSourceTests(unittest.TestCase):
 def test_original_query_separation_and_source_mutations(self):
  binary=os.environ.get('TRUSS_SECURITY_GUARDED_COMPILER_BINARY')
  if not binary:self.skipTest('Original guarded compiler required')
  root=Path(__file__).resolve().parents[3]
  request=(root/'docs/helix/04-build/evidence/security-graph-subject-registration-20261014/compiler-request.json').read_bytes()
  def compile(raw):return subprocess.run([binary],input=raw,capture_output=True,check=True,timeout=15).stdout
  output=compile(request);comparison=capture_guarded_source_comparison(request,output)
  alternative=json.loads(request);alternative['sql']='SELECT r.resourceId FROM Resource r'
  other=json.dumps(alternative,separators=(',',':')).encode();other_output=compile(other)
  self.assertEqual(require_same_guarded_source(comparison,other,other_output),comparison)
  self.assertNotEqual(json.loads(output)['queryContextSha256'],json.loads(other_output)['queryContextSha256'])
  for field,value in (('securityReady',True),('nativeAdmission','admitted'),('sourceRequestSha256','0'*64),('sourceContextSha256','0'*64),('permit','forged')):
   with self.subTest(field=field):
    corrupt=json.loads(output);corrupt[field]=value
    with self.assertRaises(ValueError):capture_guarded_source_comparison(request,json.dumps(corrupt).encode())
  for field in ('sql','principal','epoch'):
   with self.subTest(capsuleField=field):
    corrupt=json.loads(output);capsule=json.loads(corrupt['sourceContextJson']);capsule[field]='forged'
    from hashlib import sha256
    corrupt['sourceContextJson']=json.dumps(capsule);corrupt['sourceContextSha256']=sha256(corrupt['sourceContextJson'].encode()).hexdigest()
    with self.assertRaises(ValueError):capture_guarded_source_comparison(request,json.dumps(corrupt).encode())
  with self.assertRaises(ValueError):require_same_guarded_source(replace(comparison,source_sha256='0'*64),request,output)
