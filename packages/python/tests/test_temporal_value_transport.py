# SPDX-License-Identifier: MIT OR Apache-2.0
import unittest
from dataclasses import asdict
from truss import LocalTimestampValue
from truss.contracts import TextValue
from truss._temporal_values import wire_temporal_cell, local_timestamp_cell
from truss._record_schema import _wire_cell
from truss._import_runtime import _cell


class TemporalValueTransportTests(unittest.TestCase):
    def test_explicit_local_round_trip_and_ordinary_refusals(self):
        value = LocalTimestampValue(text='2024-11-03T01:30:00.123456')
        cell = wire_temporal_cell(value)
        self.assertEqual(cell, asdict(value))
        self.assertEqual(local_timestamp_cell(cell), value)
        self.assertIsNone(_wire_cell(value))
        with self.assertRaises(ValueError): _cell(cell)

    def test_broad_ordinary_instant_keeps_original_bytes(self):
        value = TextValue(kind='timestamp', text='2024-01-01T00:00:00.123456789-00:00')
        self.assertEqual(wire_temporal_cell(value), asdict(value))

    def test_closed_local_native_cell_and_canonical_ingress(self):
        for cell in ({'kind': 'timestamp', 'text': '2024-01-01T00:00:00.000000'},
                     {'kind': 'localTimestamp', 'text': '2024-01-01T00:00:00.000000', 'extra': True},
                     {'kind': 'localTimestamp', 'text': '2024-01-01T00:00:00'},
                     {'kind': 'localTimestamp', 'text': '2024-01-01T00:00:00.0000000'},
                     {'kind': 'localTimestamp', 'text': '2024-01-01T00:00:00.000000Z'}):
            with self.subTest(cell=cell), self.assertRaises(ValueError): local_timestamp_cell(cell)

    def test_result_decoding_requires_explicit_provider_and_never_nested_local(self):
        from truss._temporal_values import logical_object_cell
        cell={'kind':'localTimestamp','text':'2024-11-03T01:30:00.123456'}
        with self.assertRaises(ValueError):logical_object_cell(cell)
        self.assertEqual(logical_object_cell(cell,local=True),LocalTimestampValue(text=cell['text']))
        for nested in ({'kind':'sequence','items':[cell]}, {'kind':'map','entries':[{'key':'local','value':cell}]}):
            with self.assertRaises(ValueError):logical_object_cell(nested,local=True)
        self.assertIsNone(logical_object_cell(None,local=True))
        self.assertEqual(logical_object_cell({'kind':'sequence','items':[]},local=True).items,())

    def test_explicit_storage_transport_preserves_ordinary_containers(self):
        from truss.contracts import SequenceValue,NullValue,MapValue,MapEntry
        for value in (SequenceValue(items=()),SequenceValue(items=(NullValue(),)),
                      MapValue(entries=(MapEntry(key='text',value=TextValue(kind='string',text='unchanged')),))):
            self.assertEqual(wire_temporal_cell(value),_wire_cell(value))
