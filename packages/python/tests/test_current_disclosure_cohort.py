# SPDX-License-Identifier: MIT OR Apache-2.0
"""Packaged computation custody only; no native authority or held-file proof."""
import json,pathlib,shutil,tempfile,unittest
from unittest.mock import patch
from truss._current_disclosure_computation import verify_current_disclosure_owner_assets

class DisclosureCohortTests(unittest.TestCase):
 def test_query_and_disclosure_cohorts_pair_platform_wheel_and_native_hashes(self):
  from truss._current_query_originals import _CONSUMER_COHORTS as query_cohorts,_match_consumer
  from truss._current_disclosure_originals import _CONSUMER_COHORTS as disclosure_cohorts,check_disclosure_originals,CurrentDisclosureOriginals
  from truss._current_query_evaluation import wire
  from pathlib import Path
  import json
  from unittest.mock import patch
  expected={
   'def824d16bc00f9deb50c7c63bc08a728cff631eef25cf2616032b761e1c679c':'36224fd006f525e26e79ad2504bee7ffd75439ce1c8367564cfeb7c826e736a4',
   '8226b0cbc17b611abaaff30357aad7230e135fa713c8d3d4e05e0536a6d9a2c3':'de3289ad3d8779bd2e347c15379596495acb08381741991935b6f85c7a24b2fc',
  }
  for cohorts in (query_cohorts,disclosure_cohorts):
   self.assertEqual({row['weftWheelSha256']:row['weftModuleSha256'] for row in cohorts},expected)
   baseline={key:value for key,value in cohorts[0].items() if key not in ('weftWheelSha256','weftModuleSha256')}
   self.assertTrue(all({key:value for key,value in row.items() if key not in ('weftWheelSha256','weftModuleSha256')}==baseline for row in cohorts))
  self.assertEqual(list(disclosure_cohorts[0]),[
   'profile','umfRevision','umfBundleSha256','umfManifestSha256','embeddedRuntime',
   'embeddedProfile','embeddedV8Version','embeddedManifestSha256','weftRevision','weftVersion',
   'weftWheelSha256','weftModuleSha256','weftShimSha256','graphSha256','childProtocol','resultAbi'])
  # Whole-cohort comparison rejects a plausible but crossed wheel/module pair.
  selected=query_cohorts[0]
  crossed={**selected,'weftWheelSha256':query_cohorts[1]['weftWheelSha256']}
  with patch('truss._current_query_originals._actual_consumer',return_value=selected):
   _match_consumer(selected)
   with self.assertRaisesRegex(ValueError,'Unsupported exact query consumer selection'):
    _match_consumer(crossed)
  selected=disclosure_cohorts[0]
  crossed={**selected,'weftWheelSha256':disclosure_cohorts[1]['weftWheelSha256']}
  fixture=json.loads(Path(__file__).with_name('fixtures').joinpath('current-disclosure/source-correspondence.json').read_bytes())
  originals=CurrentDisclosureOriginals(wire(fixture['opaqueSources']),json.dumps(crossed).encode())
  with patch('truss._current_disclosure_originals._actual_disclosure_consumer',return_value=selected):
   with self.assertRaisesRegex(ValueError,'Exact original disclosure consumer required'):
    check_disclosure_originals(originals,wire(fixture['initialize']),wire(fixture['acceptedRequest']))

 def test_unknown_actual_module_digest_refuses_for_both_consumers(self):
  from truss._current_query_originals import _actual_consumer_json
  from truss._current_disclosure_originals import _actual_disclosure_consumer_json
  from truss._current_query_originals import _actual_weft_module_sha256
  _actual_consumer_json.cache_clear();_actual_disclosure_consumer_json.cache_clear()
  try:
   with patch('truss._current_query_originals._actual_weft_module_sha256',return_value='0'*64):
    with self.assertRaisesRegex(ValueError,'Actual selected original Weft ABI2 module required'):
     _actual_consumer_json()
   with patch('truss._current_disclosure_originals._actual_weft_module_sha256',return_value='0'*64):
    with self.assertRaisesRegex(ValueError,'Explicit reviewed disclosure consumer required'):
     _actual_disclosure_consumer_json()
  finally:
   _actual_consumer_json.cache_clear();_actual_disclosure_consumer_json.cache_clear();_actual_weft_module_sha256.cache_clear()

 def test_native_module_and_asset_hashes_are_computed_once_per_process(self):
  from hashlib import sha256
  from pathlib import Path
  from importlib.resources import files
  import weft.weft as native
  from truss._current_query_originals import _actual_consumer,_actual_consumer_json,_actual_weft_module_sha256
  from truss._current_query_originals import _CONSUMER_COHORTS as query_cohorts
  from truss._current_disclosure_originals import _actual_disclosure_consumer,_actual_disclosure_consumer_json,_CONSUMER_COHORTS as disclosure_cohorts
  from truss._current_query_computation import clear_current_query_owner_asset_cache
  from truss._current_disclosure_computation import verify_current_disclosure_owner_assets
  _actual_consumer_json.cache_clear();_actual_disclosure_consumer_json.cache_clear();_actual_weft_module_sha256.cache_clear()
  clear_current_query_owner_asset_cache();verify_current_disclosure_owner_assets.cache_clear()
  native_path=Path(native.__file__)
  query_root=Path(files('truss').joinpath('_current_query_owner'))
  manifest_path=query_root/'manifest.json';child_path=query_root/'current-query-child.mjs'
  original=Path.read_bytes;reads={}
  query_selections=[]
  def counted(path):
   if path in (native_path,manifest_path,child_path):reads[path]=reads.get(path,0)+1
   return original(path)
  with patch.object(Path,'read_bytes',counted):
   for _ in range(3):
    selection=_actual_consumer()
    from truss._current_query_originals import _match_consumer
    _match_consumer(selection)
    query_selections.append(selection)
   first_disclosure=_actual_disclosure_consumer();second_disclosure=_actual_disclosure_consumer()
  self.assertEqual(reads,{native_path:1,manifest_path:1,child_path:1})
  self.assertTrue(all(item==query_selections[0] for item in query_selections))
  self.assertEqual(first_disclosure,second_disclosure)
  self.assertEqual(sha256(native_path.read_bytes()).hexdigest(),selection['weftModuleSha256'])
  self.assertEqual(selection['weftRevision'],'db1e0dc5b1ec6aec0f12646421cefc314989d974')
  query_wheels={row['weftModuleSha256']:row['weftWheelSha256'] for row in query_cohorts}
  disclosure_wheels={row['weftModuleSha256']:row['weftWheelSha256'] for row in disclosure_cohorts}
  self.assertEqual(selection['weftWheelSha256'],query_wheels[selection['weftModuleSha256']])
  self.assertEqual(first_disclosure['weftRevision'],'db1e0dc5b1ec6aec0f12646421cefc314989d974')
  self.assertEqual(first_disclosure['weftVersion'],'0.4.48')
  self.assertEqual(first_disclosure['weftWheelSha256'],disclosure_wheels[first_disclosure['weftModuleSha256']])

 def test_enrolled_assets_are_identified_once_per_process_and_rechecked_after_restart(self):
  self.addCleanup(verify_current_disclosure_owner_assets.cache_clear)
  enrolled=verify_current_disclosure_owner_assets()
  with tempfile.TemporaryDirectory(prefix='truss-disclosure-assets-') as directory:
   package=pathlib.Path(directory);assets=package/'_current_disclosure_owner'
   shutil.copytree(str(enrolled),assets)
   with patch('truss._current_disclosure_computation.files',return_value=package):
    verify_current_disclosure_owner_assets.cache_clear()
    self.assertEqual(verify_current_disclosure_owner_assets(),assets)
    for name in ('consumer-manifest.json','manifest.json','current-native-disclosure-child.mjs','notices/ajv/LICENSE'):
     path=assets/name;original=path.read_bytes()
     try:
      path.write_bytes(original+b'\nchanged-source')
      with self.subTest(source=name):
       # A running process retains the package identity selected at startup.
       self.assertEqual(verify_current_disclosure_owner_assets(),assets)
       # A process restart performs a fresh full hash before reuse.
       verify_current_disclosure_owner_assets.cache_clear()
       with self.assertRaises(ValueError):
        verify_current_disclosure_owner_assets()
     finally:
      path.write_bytes(original)
     verify_current_disclosure_owner_assets.cache_clear()
     self.assertEqual(verify_current_disclosure_owner_assets(),assets)

 def test_query_assets_use_the_same_restart_scoped_identity(self):
  from truss._current_query_computation import verify_current_query_owner_assets,clear_current_query_owner_asset_cache
  self.addCleanup(clear_current_query_owner_asset_cache)
  enrolled=verify_current_query_owner_assets()
  with tempfile.TemporaryDirectory(prefix='truss-query-assets-') as directory:
   package=pathlib.Path(directory);assets=package/'_current_query_owner'
   shutil.copytree(str(enrolled),assets)
   with patch('truss._current_query_computation.files',return_value=package):
    clear_current_query_owner_asset_cache()
    self.assertEqual(verify_current_query_owner_assets(),assets)
    path=assets/'current-query-child.mjs';original=path.read_bytes()
    try:
     path.write_bytes(original+b'\nchanged-source')
     self.assertEqual(verify_current_query_owner_assets(),assets)
     clear_current_query_owner_asset_cache()
     with self.assertRaises(ValueError):verify_current_query_owner_assets()
    finally:path.write_bytes(original)
    clear_current_query_owner_asset_cache()
    self.assertEqual(verify_current_query_owner_assets(),assets)

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
