# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure Weft result reuse never changes inputs or lends mutable artifacts."""
import json
import unittest
from unittest.mock import Mock,patch
from truss import _query_cache as cache


class QueryCompileCacheTests(unittest.TestCase):
    def setUp(self):
        with cache._lock:
            cache._entries.clear();cache._bytes=0
        self.addCleanup(self.set_cache_empty)

    def set_cache_empty(self):
        with cache._lock:
            cache._entries.clear();cache._bytes=0

    def test_exact_hit_returns_fresh_artifact_and_misses_every_changed_input(self):
        compiler=Mock(return_value='{"status":"compiled","parameters":[{"value":"original"}]}')
        request={'sql':'SELECT x.name FROM X x','modules':[{'pin':{'sha256':'a'},'documentJson':'original'}],
            'parameters':{'id':{'family':'integer','value':'1'}},'target':{'bindingJson':'binding-a'},'readProfile':'complete-entity'}
        original=json.dumps(request)
        first=cache.compile_response(compiler,original)
        first['parameters'][0]['value']='caller mutation'
        self.assertEqual(cache.compile_response(compiler,original)['parameters'][0]['value'],'original')
        self.assertEqual(compiler.call_count,1)
        for key in request:
            changed=dict(request);changed[key]='changed'
            cache.compile_response(compiler,json.dumps(changed))
        self.assertEqual(compiler.call_count,1+len(request))
        successor=Mock(return_value=compiler.return_value)
        cache.compile_response(successor,original)
        successor.assert_called_once_with(original)

    def test_page_position_and_size_are_part_of_identity(self):
        compiler=Mock(return_value='{"status":"compiled","artifact":{},"page":{}}')
        cache.compile_response(compiler,'request',10,['a'])
        cache.compile_response(compiler,'request',10,['a'])
        cache.compile_response(compiler,'request',10,['b'])
        cache.compile_response(compiler,'request',20,['a'])
        self.assertEqual(compiler.call_count,3)

    def test_blocked_results_and_failures_are_not_cached(self):
        compiler=Mock(return_value='{"status":"blocked","diagnostics":[]}')
        cache.compile_response(compiler,'request');cache.compile_response(compiler,'request')
        self.assertEqual(compiler.call_count,2)
        self.assertEqual(len(cache._entries),0)
        compiler.side_effect=ValueError('compiler failed')
        with self.assertRaises(ValueError):cache.compile_response(compiler,'request')
        self.assertEqual(len(cache._entries),0)

    def test_eviction_and_oversize_results_bound_retention(self):
        compiler=Mock(return_value='{"status":"compiled"}')
        with patch.object(cache,'MAX_ENTRIES',2):
            for request in ('a','b','c'):cache.compile_response(compiler,request)
            self.assertEqual(len(cache._entries),2)
            cache.compile_response(compiler,'a')
            self.assertEqual(compiler.call_count,4)
        self.set_cache_empty()
        with patch.object(cache,'MAX_BYTES',1):cache.compile_response(compiler,'huge')
        self.assertEqual(len(cache._entries),0)
        self.assertEqual(cache._bytes,0)


if __name__=='__main__':unittest.main()
