# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original inspector/publication correspondence, not native admission."""
import json,os,subprocess,unittest
from pathlib import Path
from security_ontology_guarded_read import _inspected_query_publication

class QueryPublicationTests(unittest.TestCase):
 def test_inspected_bytes_are_frozen_and_substitution_refuses(self):
  binary=os.environ.get('TRUSS_SECURITY_GUARDED_COMPILER_BINARY')
  if not binary:self.skipTest('Original guarded compiler required')
  root=Path(__file__).resolve().parents[3]
  request=(root/'docs/helix/04-build/evidence/security-graph-subject-registration-20261014/compiler-request.json').read_text()
  output=subprocess.run([binary],input=request.encode(),capture_output=True,check=True,timeout=15).stdout.decode()
  query=json.loads(output)['query']
  batch=json.dumps({'version':'weft.security.cells/0.1.0','resultContractSha256':query['resultContractSha256'],'rows':[]},separators=(',',':'))
  checker=Path(binary).with_name('security_guarded_result')
  inspected=subprocess.run([str(checker)],input=json.dumps({'version':'weft.truss.security.guarded-result/0.1-candidate','sourceRequestJson':request,'sourceOutputJson':output,'batchJson':batch}).encode(),capture_output=True,check=True,timeout=15).stdout.decode()
  receipt={'request':request,'output':output,'batch':batch,'resultCheck':inspected}
  published=_inspected_query_publication(receipt)
  self.assertEqual(json.loads(published)['batchJson'],batch)
  receipt['batch']=batch+' '
  with self.assertRaisesRegex(ValueError,'Original inspected query publication correspondence required'):_inspected_query_publication(receipt)
  self.assertEqual(json.loads(published)['batchJson'],batch)
  receipt['batch']=batch;check=json.loads(inspected);check['securityReady']=0;receipt['resultCheck']=json.dumps(check)
  with self.assertRaises(ValueError):_inspected_query_publication(receipt)

  for key,limit in (('request',4000000),('batch',4000000),('resultCheck',65536)):
   with self.subTest(overflow=key):
    oversized={'request':request,'output':output,'batch':batch,'resultCheck':inspected}
    oversized[key]='x'*(limit+1)
    with self.assertRaisesRegex(ValueError,'Bounded inspected query publication required'):_inspected_query_publication(oversized)
