"""Original UMF owner dependency coverage, not physical or issuer qualification."""
import hashlib,json,unittest
from pathlib import Path
from truss._security_fact_coverage import _FactBindingDeclaration,_inspect_fact_coverage
ROOT=Path(__file__).resolve().parents[3]
RAW=(ROOT/'docs/helix/04-build/evidence/security-fact-requirements/requirements.json').read_bytes()
DIGEST=hashlib.sha256(RAW).hexdigest()

class SecurityFactCoverageTests(unittest.TestCase):
 def test_original_owner_association_only_leaves_eight_live_fields_missing(self):
  refs=json.loads(RAW)['dependencies']['associations']
  declarations=tuple(_FactBindingDeclaration('association',tuple(r[k] for k in ('documentId','moduleId','elementId')),'declared-native-graph') for r in refs)
  result=_inspect_fact_coverage(RAW,DIGEST,declarations)
  self.assertEqual(len(result.required),10);self.assertEqual(len(result.missing),8)
  self.assertEqual([r[1][2] for r in result.missing],['active','assignmentProject','assignmentStaff','ownerProject','ownerResource','projectId','resourceId','staffId'])
  self.assertEqual([k for k,r in result.required],['field']*8+['association']*2)
  self.assertFalse(result.admitted)
 def test_declared_complete_coverage_still_does_not_admit_a_profile(self):
  required=_inspect_fact_coverage(RAW,DIGEST,()).required
  declarations=tuple(_FactBindingDeclaration(k,r,'opaque-unqualified-provider') for k,r in required)
  result=_inspect_fact_coverage(RAW,DIGEST,declarations)
  self.assertEqual(result.missing,());self.assertEqual(len(result.bindings),10);self.assertFalse(result.admitted)
 def test_foreign_or_duplicate_binding_refuses(self):
  entry=_FactBindingDeclaration('field',('domain','m','active'),'declared')
  for declarations in ((entry,entry),(_FactBindingDeclaration('field',('foreign','m','active'),'declared'),)):
   with self.assertRaises(ValueError):_inspect_fact_coverage(RAW,DIGEST,declarations)
 def test_missing_dependency_list_is_not_empty(self):
  artifact=json.loads(RAW);del artifact['dependencies']['fields'];raw=json.dumps(artifact).encode()
  with self.assertRaises(ValueError):_inspect_fact_coverage(raw,hashlib.sha256(raw).hexdigest(),())
 def test_changed_original_artifact_and_duplicate_json_keys_refuse(self):
  with self.assertRaises(ValueError):_inspect_fact_coverage(RAW+b' ',DIGEST,())
  raw=RAW.replace(b'"dependencies":',b'"dependencies":{},"dependencies":',1)
  with self.assertRaises(ValueError):_inspect_fact_coverage(raw,hashlib.sha256(raw).hexdigest(),())
 def test_opaque_qualified_reference_spelling_is_preserved(self):
  artifact=json.loads(RAW);artifact['dependencies']={'fields':[{'documentId':'d / .','moduleId':'m/','elementId':'e\u0301'}],'associations':[]};raw=json.dumps(artifact).encode();digest=hashlib.sha256(raw).hexdigest()
  result=_inspect_fact_coverage(raw,digest,())
  self.assertEqual(result.required,(('field',('d / .','m/','e\u0301')),))
  with self.assertRaises(ValueError):_inspect_fact_coverage(raw,digest,(_FactBindingDeclaration('field',('d / .','m/','é'),'declared'),))
