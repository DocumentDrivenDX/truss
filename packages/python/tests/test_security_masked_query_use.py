"""@covers US-056-AC6
Original compiler query-use admission controls, not native backend acceptance.
"""
import hashlib,json,os,subprocess,unittest
from pathlib import Path

class MaskedQueryUseTests(unittest.TestCase):
 def test_withheld_field_cannot_drive_collection_operators(self):
  binary=os.environ.get('TRUSS_SECURITY_RELATIONAL_COMPILER_BINARY')
  if not binary:self.skipTest('Original relational compiler required')
  binary=Path(binary);pin=hashlib.sha256(binary.read_bytes()).digest()
  root=Path(__file__).resolve().parents[3]
  source=root/'docs/helix/04-build/evidence/security-graph-subject-registration-20261014/compiler-request.json'
  request=json.loads(source.read_bytes());source_pin=hashlib.sha256(source.read_bytes()).digest()
  pairs=(
   ('filter',"SELECT r.resourceId FROM Resource r WHERE r.salary = 200","SELECT r.resourceId FROM Resource r WHERE r.resourceId = 'RB'"),
   ('sort','SELECT r.resourceId FROM Resource r ORDER BY r.salary','SELECT r.resourceId FROM Resource r ORDER BY r.resourceId'),
   ('group','SELECT r.salary, COUNT(*) AS n FROM Resource r GROUP BY r.salary','SELECT r.resourceId, COUNT(*) AS n FROM Resource r GROUP BY r.resourceId'),
   ('join','SELECT r.resourceId AS left_id, s.resourceId AS right_id FROM Resource r JOIN Resource s ON r.salary = s.salary','SELECT r.resourceId AS left_id, s.resourceId AS right_id FROM Resource r JOIN Resource s ON r.resourceId = s.resourceId'),
   ('aggregate','SELECT SUM(r.salary) AS total FROM Resource r','SELECT COUNT(*) AS total FROM Resource r'))
  for operator,forbidden,permitted in pairs:
   with self.subTest(operator=operator):
    request['sql']=forbidden
    refused=subprocess.run([str(binary)],input=json.dumps(request).encode(),capture_output=True,timeout=15)
    self.assertNotEqual(refused.returncode,0);self.assertEqual(refused.stdout,b'')
    diagnostic=json.loads(refused.stderr)
    self.assertEqual(diagnostic['code'],'WFT-SECURITY-QUERY-PROFILE')
    self.assertEqual(diagnostic['phase'],'model')
    request['sql']=permitted
    accepted=subprocess.run([str(binary)],input=json.dumps(request).encode(),capture_output=True,timeout=15)
    self.assertEqual(accepted.returncode,0,accepted.stderr.decode())
    packet=json.loads(accepted.stdout)
    self.assertIs(packet['securityReady'],False)
    self.assertEqual(packet['nativeAdmission'],'required')
    self.assertEqual(packet['nativePopulationAndSelection'],'required')
  self.assertEqual(hashlib.sha256(binary.read_bytes()).digest(),pin)
  self.assertEqual(hashlib.sha256(source.read_bytes()).digest(),source_pin)
