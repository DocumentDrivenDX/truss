"""Original relationship preflight/inspection boundary, not native custody."""
import json,os,subprocess,unittest
from pathlib import Path
from security_relationship_codecs import prepare_owned_relationship_codec_checker
from security_relationship_inspection import prepare_owned_relationship_inspector
from security_relationship_capture import capture_relationship_operands

class RelationshipBoundaryTests(unittest.TestCase):
 def test_separate_original_codec_inspector_and_preflight(self):
  binary=os.environ.get('TRUSS_SECURITY_RELATIONSHIP_COMPILER_BINARY')
  if not binary:self.skipTest('Separate original relationship producer required')
  folder=Path(__file__).resolve().parents[3]/'docs/helix/04-build/evidence/security-public-relationship-request-20261014'
  checker=prepare_owned_relationship_codec_checker(Path(binary).with_name('security_relationship_codecs'))
  inspect=prepare_owned_relationship_inspector(Path(binary).with_name('security_relationship_result'))
  for suffix in ('','-observation-denied'):
   with self.subTest(variant=suffix):
    request=(folder/('compiler-request'+suffix+'.json')).read_bytes()
    output=subprocess.run([binary],input=request,capture_output=True,check=True,timeout=15).stdout;packet=json.loads(output)
    self.assertEqual(json.loads(checker(request,output))['nativeSessionAdmission'],'required')
    scans=[{'scan':r['scan'],'rows':[]} for r in packet['operandReads']]
    self.assertEqual({r['scan'] for r in scans},{'s0','t0'})
    operands=json.dumps({'version':'weft.security.operand-values/0.1-candidate','contextSha256':packet['queryContextSha256'],'scans':scans}).encode()
    self.assertEqual(json.loads(checker(request,output,operands))['operandCount'],0)
    batch=json.dumps({'version':packet['resultContract']['encoding'],'resultContractSha256':packet['resultContractSha256'],'rows':[]}).encode()
    self.assertIs(json.loads(inspect(request,output,operands,batch))['inspected'],True)
    class NoSQL:
     def execute(self,*args,**kwargs):raise AssertionError('SQL before codec preflight')
    def preflight_then_stop(*args):checker(*args);raise ValueError('test stops after original preflight')
    with self.assertRaisesRegex(ValueError,'test stops after original preflight'):capture_relationship_operands(NoSQL(),request,output,1,preflight_then_stop)
    altered=json.loads(output);altered['executionSql']+=' '
    with self.assertRaises(ValueError):inspect(request,json.dumps(altered).encode(),operands,batch)
