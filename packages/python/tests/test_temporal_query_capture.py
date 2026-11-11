# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure capture framing/refusal controls, not native binding qualification."""
from decimal import Decimal
from threading import RLock
import unittest

from truss import LocalTimestampValue, Ok
from truss.catalog_runtime import CatalogReferenceAssembly
from truss.query import QueryRefused
from truss.temporal import TemporalValues
from truss._temporal_query_runtime import _parameters,capture_sources


class TemporalQueryCaptureTests(unittest.TestCase):
    def test_factory_binds_real_private_port_without_io(self):
        assembly=object.__new__(CatalogReferenceAssembly)
        assembly._lock=RLock();assembly._disposed=False
        selected=assembly.temporal_values()
        self.assertIsInstance(selected,TemporalValues)
        with self.assertRaises(ValueError):
            assembly._temporal_values_operation('ordinary_fallback',{})
        with self.assertRaises(ValueError):
            assembly._temporal_values_operation('group_context_in_transaction',{'transaction':object(),'extra':True})

    def test_parameters_keep_exact_tokens_and_map_membership(self):
        original={'amount':Decimal('12345678901234567890.123400'),'id':12345678901234567890,
                  'enabled':True,'text':'ordinary timestamp-looking string 2024-01-01'}
        tokens={'utc':{'kind':'instant','value':'2024-01-01T01:00:00.123456+01:00'},
                'local':{'kind':'local','value':'2024-01-01T00:00:00.0000000'}}
        ordinary,temporal=_parameters(original,tokens)
        self.assertEqual(ordinary['amount'],{'family':'decimal','value':'12345678901234567890.123400'})
        self.assertEqual(ordinary['id']['value'],'12345678901234567890')
        self.assertEqual(ordinary['text']['family'],'string')
        # Capture does not add a competing calendar parser or repair a token
        # which the owner compiler must refuse (including seven zero digits).
        self.assertEqual(temporal,tokens)
        self.assertIsNot(temporal['local'],tokens['local'])

    def test_malformed_maps_refuse_before_any_native_call(self):
        class NoIO:
            def _run_operation(self,*args,**kwargs):raise AssertionError('I/O before input refusal')
        base=dict(host=NoIO(),transaction=object(),sql='SELECT value FROM source',document_ids=('adoc',),
                  parameters={},temporal_parameters={},maximum_rows=10,maximum_scan_rows=100,maximum_bytes=1024,
                  manifest={'releaseId':'truss-catalog-runtime/0.76-candidate'},digest='not-observed',pin_cursor=None)
        for changes in (
            {'parameters':{'same':'x'},'temporal_parameters':{'same':{'kind':'local','value':'x'}}},
            {'parameters':{'x':LocalTimestampValue(text='2024-01-01T00:00:00.000000')}},
            {'parameters':{'x':Decimal('NaN')}}, {'parameters':{'x':Decimal('1e1048577')}},
            {'temporal_parameters':{'x':{'kind':'timestamp','value':'x'}}},
            {'temporal_parameters':{'x':{'kind':'local','value':'x','extra':True}}},
            {'temporal_parameters':{'x':{'kind':'local','value':'x\0'}}},
            {'temporal_parameters':{'x':{'kind':'local','value':None}}},
            {'document_ids':('adoc','adoc')}, {'sql':'\ud800'},
        ):
            with self.subTest(changes=changes):
                self.assertEqual(capture_sources(**{**base,**changes}),Ok(QueryRefused(code='invalid_query')))
        self.assertEqual(capture_sources(**{**base,'maximum_rows':True}),Ok(QueryRefused(code='limits')))
        self.assertEqual(capture_sources(**{**base,'manifest':{'releaseId':'truss-catalog-runtime/0.75-candidate'}}),
                         Ok(QueryRefused(code='unsupported_query')))
