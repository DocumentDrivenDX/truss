# SPDX-License-Identifier: MIT OR Apache-2.0
"""Immutable package verification is cached; native authorization never is."""
from concurrent.futures import ThreadPoolExecutor
from importlib.resources import files
import unittest
from unittest.mock import patch
from truss import catalog_runtime as runtime


class RuntimeReleaseCacheTests(unittest.TestCase):
    def setUp(self):
        runtime._verified_release.cache_clear()
        self.addCleanup(runtime._verified_release.cache_clear)

    def test_warm_access_performs_no_filesystem_reads_and_returns_fresh_manifest(self):
        manifest,digest,sources=runtime._release()
        original_release=manifest['releaseId']
        manifest['releaseId']='caller mutation'
        manifest['files'].clear()
        with patch.object(runtime,'files',side_effect=AssertionError('Warm package must not be read')):
            again,again_digest,again_sources=runtime._release()
        self.assertEqual(again['releaseId'],original_release)
        self.assertTrue(again['files'])
        self.assertEqual(again_digest,digest)
        self.assertIs(again_sources,sources)
        self.assertIsInstance(sources,tuple)

    def test_concurrent_first_use_verifies_one_complete_release(self):
        with patch.object(runtime,'files',wraps=files) as reads:
            with ThreadPoolExecutor(max_workers=8) as workers:
                results=list(workers.map(lambda _:runtime._release(),range(16)))
        self.assertEqual(reads.call_count,1)
        self.assertTrue(all(result==results[0] for result in results))
        self.assertEqual(len({id(result[0]) for result in results}),16)

    def test_corruption_refuses_and_failure_is_not_cached(self):
        root=files('truss').joinpath('_catalog_runtime')
        class CorruptRoot:
            def joinpath(self,name):
                if name!='layout.sql':return root.joinpath(name)
                class CorruptSource:
                    def read_bytes(self):return b'corrupt runtime source'
                return CorruptSource()
        class Package:
            def joinpath(self,name):
                if name!='_catalog_runtime':raise AssertionError(name)
                return CorruptRoot()
        with patch.object(runtime,'files',return_value=Package()):
            with self.assertRaisesRegex(ValueError,'Catalog release source changed'):
                runtime._release()
        self.assertEqual(runtime._verified_release.cache_info().currsize,0)
        self.assertTrue(runtime._release()[0]['files'])


if __name__=='__main__':unittest.main()
