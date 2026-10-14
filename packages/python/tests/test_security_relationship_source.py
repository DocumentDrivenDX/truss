"""Distinct archive refusal controls; positive owner traversal output pending."""
import json,os,subprocess,unittest
from pathlib import Path
from truss._security_relational_source import capture_relational_source_comparison
from truss._security_graph_source import PreparedGraphSecuritySource,snapshot_graph_security_source
from truss._security_relationship_source import PreparedRelationshipSecuritySource,snapshot_relationship_security_source,capture_relationship_source_comparison

class RelationshipSourceTests(unittest.TestCase):
 def test_historical_output_and_archive_cannot_authorize_relationship_source(self):
  binary=os.environ.get('TRUSS_SECURITY_RELATIONAL_COMPILER_BINARY')
  if not binary:self.skipTest('Original relational producer required')
  root=Path(__file__).resolve().parents[3]
  old=(root/'docs/helix/04-build/evidence/security-graph-subject-registration-20261014/compiler-request.json').read_bytes()
  output=subprocess.run([binary],input=old,capture_output=True,check=True,timeout=15).stdout
  with self.assertRaisesRegex(ValueError,'Distinct original relationship source versions required'):capture_relationship_source_comparison(old,output)
  evidence=root/'docs/helix/04-build/evidence/security-public-relationship-request-20261014'
  new=(evidence/'compiler-request.json').read_bytes();physical=(evidence/'physical-request.json').read_bytes();assessment=(evidence/'accepted-assessment.json').read_bytes()
  with self.assertRaisesRegex(ValueError,'Distinct original relational source profile required'):capture_relational_source_comparison(new,output)
  with self.assertRaisesRegex(ValueError,'Original guarded source correspondence required'):capture_relationship_source_comparison(new,output)
  selected=PreparedRelationshipSecuritySource(physical,assessment,new,output)
  with self.assertRaises(ValueError):snapshot_relationship_security_source(selected)
  with self.assertRaisesRegex(ValueError,'Original graph source archive required'):snapshot_graph_security_source(selected)
  historical=PreparedGraphSecuritySource(physical,output,assessment,new)
  with self.assertRaisesRegex(ValueError,'Original physical graph and compiler source correspondence required'):snapshot_graph_security_source(historical)
  with self.assertRaisesRegex(ValueError,'Distinct original relationship source archive required'):snapshot_relationship_security_source(historical)
