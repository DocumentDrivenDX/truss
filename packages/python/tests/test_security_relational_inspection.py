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
  provided=json.loads(operands)
  provided['scans'][0]['rows']=[{'nativeRowId':'1','operands':[]}]
  nonempty=json.loads(inspect(request,output,json.dumps(provided).encode(),batch))
  self.assertEqual(nonempty['operandCounts'][provided['scans'][0]['scan']],1)
  corrupt=json.loads(output);corrupt['executionSql']+=' '
  with self.assertRaisesRegex(ValueError,'Original relational inspection refused'):inspect(request,json.dumps(corrupt).encode(),operands,batch)

  # Corrupt only the inspector acknowledgment; original input remains intact.
  from unittest.mock import patch
  from types import SimpleNamespace
  original_run=subprocess.run
  def wrong_counts(*args,**kwargs):
   result=original_run(*args,**kwargs)
   changed=json.loads(result.stdout);changed['operandCounts']={}
   return SimpleNamespace(returncode=0,stdout=json.dumps(changed).encode())
  with patch('security_relational_inspection.subprocess.run',wrong_counts),self.assertRaisesRegex(ValueError,'Original relational operand counts required'):
   inspect(request,output,operands,batch)
