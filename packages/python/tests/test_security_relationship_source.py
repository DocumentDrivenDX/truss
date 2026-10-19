# SPDX-License-Identifier: MIT OR Apache-2.0
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

 def test_original_relationship_output_archives_and_exact_byte_drift(self):
  binary=os.environ.get('TRUSS_SECURITY_RELATIONSHIP_COMPILER_BINARY')
  if not binary:self.skipTest('Separate original relationship producer required')
  from dataclasses import replace
  from hashlib import sha256
  from truss._security_relationship_source import relationship_source_archives
  pin=sha256(Path(binary).read_bytes()).hexdigest()
  root=Path(__file__).resolve().parents[3]
  evidence=root/'docs/helix/04-build/evidence/security-public-relationship-request-20261014'
  physical=(evidence/'physical-request.json').read_bytes();assessment=(evidence/'accepted-assessment.json').read_bytes()
  for suffix in ('','-observation-denied'):
   with self.subTest(variant=suffix):
    request=(evidence/('compiler-request'+suffix+'.json')).read_bytes()
    output=subprocess.run([binary],input=request,capture_output=True,check=True,timeout=15).stdout
    selected=PreparedRelationshipSecuritySource(physical,assessment,request,output)
    self.assertEqual(snapshot_relationship_security_source(selected),selected)
    self.assertEqual(len(relationship_source_archives(selected,b'original synthetic release archive')),7)
    with self.assertRaisesRegex(ValueError,'Distinct original relational source profile required'):capture_relational_source_comparison(request,output)
    with self.assertRaisesRegex(ValueError,'Exact original relationship physical source correspondence required'):snapshot_relationship_security_source(replace(selected,accepted_catalog_assessment=assessment+b' '))
    changed=json.loads(output);changed['sourceContextSha256']='0'*64
    with self.assertRaises(ValueError):snapshot_relationship_security_source(replace(selected,original_response=json.dumps(changed).encode()))
  self.assertEqual(sha256(Path(binary).read_bytes()).hexdigest(),pin)

 def test_distinct_catalog_archive_and_epoch_profile_binding(self):
  binary=os.environ.get('TRUSS_SECURITY_RELATIONSHIP_COMPILER_BINARY')
  if not binary:self.skipTest('Separate original relationship producer required')
  from hashlib import sha256
  from truss._security_catalog_source_installation import _catalog_mapping_snapshot,_catalog_source_archives
  from truss._security_catalog_source_binding import derive_catalog_source_epoch_profile
  from truss._psycopg_fact_cut import _FactRelationComparison,_FactColumnComparison
  from truss._psycopg_epoch_cut import _DDLBarrierComparison
  root=Path(__file__).resolve().parents[3]
  evidence=root/'docs/helix/04-build/evidence/security-public-relationship-request-20261014'
  request=(evidence/'compiler-request.json').read_bytes()
  output=subprocess.run([binary],input=request,capture_output=True,check=True,timeout=15).stdout
  source=PreparedRelationshipSecuritySource((evidence/'physical-request.json').read_bytes(),(evidence/'accepted-assessment.json').read_bytes(),request,output)
  self.assertEqual(_catalog_mapping_snapshot(source),source)
  self.assertTrue(all(entry[1].startswith('relationship:') for entry in _catalog_source_archives(source,b'synthetic release preimage')))
  # Pure recipe comparison only: these OIDs/bodies are not installed authority.
  column=_FactColumnComparison('id',1,20,-1,True,0)
  facts=tuple(_FactRelationComparison('truss',name,100+i,10,'synthetic guard body',(column,)) for i,name in enumerate(('object','edge','catalog_subject_map')))
  profile=json.loads(derive_catalog_source_epoch_profile(source,facts,_DDLBarrierComparison(10,20,'synthetic barrier body'),subject_source=b'synthetic subject source'))
  self.assertEqual(profile['interfaceVersion'],'truss-owned-relationship-source-profile/0.1-candidate')
  self.assertEqual(profile['compilerRequestSha256'],sha256(request).hexdigest())
  self.assertEqual(profile['compilerOutputSha256'],sha256(output).hexdigest())
  self.assertEqual(profile['sourceContextSha256'],json.loads(output)['sourceContextSha256'])
  self.assertEqual(len(profile['factCuts']),3)
