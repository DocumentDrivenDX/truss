# SPDX-License-Identifier: MIT OR Apache-2.0
"""Packaged computation custody only; no native authority or held-file proof."""
import json,pathlib,shutil,tempfile,unittest
from unittest.mock import patch
from truss._current_disclosure_computation import verify_current_disclosure_owner_assets

class DisclosureCohortTests(unittest.TestCase):
 def test_enrolled_assets_verify_and_each_source_stage_mutation_refuses(self):
  enrolled=verify_current_disclosure_owner_assets()
  with tempfile.TemporaryDirectory(prefix='truss-disclosure-assets-') as directory:
   package=pathlib.Path(directory);assets=package/'_current_disclosure_owner'
   shutil.copytree(str(enrolled),assets)
   with patch('truss._current_disclosure_computation.files',return_value=package):
    self.assertEqual(verify_current_disclosure_owner_assets(),assets)
    for name in ('consumer-manifest.json','manifest.json','current-native-disclosure-child.mjs','notices/ajv/LICENSE'):
     path=assets/name;original=path.read_bytes()
     try:
      path.write_bytes(original+b'\nchanged-source')
      with self.subTest(source=name),self.assertRaises(ValueError):
       verify_current_disclosure_owner_assets()
     finally:path.write_bytes(original)
     self.assertEqual(verify_current_disclosure_owner_assets(),assets)

class RawCaptureProfileTests(unittest.TestCase):
 def test_raw_capture_has_explicit_empty_graph_profile_and_refuses_core_relationships(self):
  from truss._current_query_facts import CurrentQueryFactCapture,_recipes
  from test_current_disclosure_graphs import fixture
  sources,_,_,_=fixture()
  initial=json.loads(sources.initialize_bytes);initial['sources']['ontology']['context']=[]
  sources.initialize_bytes=json.dumps(initial).encode()
  # The existing raw collector must refuse even a zero-row core relationship.
  with self.assertRaisesRegex(ValueError,'Native graph fact capture remains required'):
   _recipes(sources)
  captured=CurrentQueryFactCapture(sources,b'[]',b'[]',())
  self.assertEqual(captured.graphs_bytes,b'[]')
  self.assertEqual(captured.graph_coverage_bytes,b'[]')

if __name__=='__main__':unittest.main()
