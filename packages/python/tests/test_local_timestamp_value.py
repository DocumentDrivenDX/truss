# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure tests for the separate, zone-free local timestamp carrier."""
import unittest

import truss
from truss.contracts import LocalTimestampValue, TextValue, validate_local_timestamp_text
from truss._import_runtime import _cell as decode_import_cell
from truss._query_runtime import _decode_value, query_temporal_abi


class LocalTimestampValueTests(unittest.TestCase):
    def test_public_constructor_preserves_exact_canonical_civil_text(self):
        token = '2024-02-29T23:59:58.000001'
        value = LocalTimestampValue(text=token)
        self.assertIs(truss.LocalTimestampValue, LocalTimestampValue)
        self.assertEqual(value.kind, 'localTimestamp')
        self.assertEqual(value.text, token)
        self.assertIs(validate_local_timestamp_text(token), token)

    def test_gregorian_and_clock_boundaries(self):
        for token in (
            '0001-01-01T00:00:00.000000',
            '9999-12-31T23:59:59.999999',
            '2000-02-29T12:30:45.123456',
        ):
            self.assertEqual(LocalTimestampValue(text=token).text, token)
        for token in (
            '0000-01-01T00:00:00.000000',
            '1900-02-29T12:00:00.000000',
            '2024-02-30T12:00:00.000000',
            '2024-01-01T24:00:00.000000',
            '2024-01-01T12:60:00.000000',
            '2024-01-01T12:00:60.000000',
        ):
            with self.subTest(token=token), self.assertRaises(ValueError):
                LocalTimestampValue(text=token)

    def test_only_exact_26_ascii_characters_without_zone_are_admitted(self):
        for token in (
            '2024-01-01T00:00:00',
            '2024-01-01T00:00:00.1',
            '2024-01-01T00:00:00.1234567',
            '2024-01-01T00:00:00.123456Z',
            '2024-01-01T00:00:00.123456+00:00',
            '2024-01-01t00:00:00.123456',
            '２０２４-01-01T00:00:00.123456',
            '2024-01-01T00:00:00.123456\n',
            None,
        ):
            with self.subTest(token=token), self.assertRaises(ValueError):
                LocalTimestampValue(text=token)

    def test_offset_timestamp_carrier_remains_distinct_and_unchanged(self):
        token = '2024-01-01T00:00:00.123456789-00:00'
        value = TextValue(kind='timestamp', text=token)
        self.assertEqual(value.kind, 'timestamp')
        self.assertEqual(value.text, token)
        with self.assertRaises(ValueError):
            LocalTimestampValue(text=token)

    def test_import_codec_decodes_local_timestamp_as_distinct_value(self):
        value = decode_import_cell({'kind': 'localTimestamp', 'text': '2024-03-10T01:30:00.123456'})
        self.assertIs(type(value), LocalTimestampValue)
        with self.assertRaises(ValueError):
            decode_import_cell({'kind': 'localTimestamp', 'text': '2024-03-10T01:30:00-05:00'})
        with self.assertRaises(ValueError):
            decode_import_cell({'kind': 'sequence', 'items': [
                {'kind': 'localTimestamp', 'text': '2024-03-10T01:30:00.123456'}]}, containers=True)

    def test_temporal_query_abi_is_distinct_and_result_decoder_preserves_value(self):
        descriptor = query_temporal_abi()
        self.assertEqual(descriptor['version'], '1.3')
        self.assertEqual(descriptor['bindingInterfaceVersion'], 'truss-runtime-binding/0.5')
        identity = {'module': 'M', 'element': 'local'}
        value = _decode_value('2024-03-10T01:30:00.123456', identity, {
            '{"element":"local","module":"M"}': {
                'identity': identity, 'kind': 'exactScalar', 'scalarType': 'localTimestamp'
            }
        })
        self.assertIs(type(value), LocalTimestampValue)
        self.assertEqual(value.text, '2024-03-10T01:30:00.123456')


if __name__ == '__main__':
    unittest.main()
