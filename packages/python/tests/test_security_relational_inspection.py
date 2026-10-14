"""Original pure inspection tests; empty captures are not population proof."""
import json,os,subprocess,unittest
from pathlib import Path
from security_relational_inspection import prepare_owned_relational_inspector

class RelationalInspectionTests(unittest.TestCase):
 def test_original_inspection_and_changed_producer_refusal(self):
  binary=os.environ.get('TRUSS_SECURITY_RELATIONAL_COMPILER_BINARY')
  if not binary:self.skipTest('Original relational producer required')
  root=Path(__file__).resolve().parents[3]
  request=(root/'docs/helix/04-build/evidence/security-graph-subject-registration-20261014/compiler-request.json').read_bytes()
  output=subprocess.run([binary],input=request,capture_output=True,check=True,timeout=15).stdout;packet=json.loads(output)
  operands=json.dumps({'version':'weft.security.operand-values/0.1-candidate','contextSha256':packet['queryContextSha256'],'scans':[{'scan':r['scan'],'rows':[]} for r in packet['operandReads']]}).encode()
  batch=json.dumps({'version':packet['resultContract']['encoding'],'resultContractSha256':packet['resultContractSha256'],'rows':[]}).encode()
  inspect=prepare_owned_relational_inspector(Path(binary).with_name('security_relational_result'))
  checked=json.loads(inspect(request,output,operands,batch));self.assertFalse(checked['securityReady']);self.assertTrue(checked['inspected'])
  corrupt=json.loads(output);corrupt['executionSql']+=' '
  with self.assertRaisesRegex(ValueError,'Original relational inspection refused'):inspect(request,json.dumps(corrupt).encode(),operands,batch)
