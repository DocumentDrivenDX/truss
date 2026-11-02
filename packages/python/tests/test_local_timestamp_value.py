# SPDX-License-Identifier: MIT OR Apache-2.0
"""Standalone local carrier; native and legacy transport remain unqualified."""
import unittest
from dataclasses import FrozenInstanceError, asdict

import truss
from truss.contracts import (
    LocalTimestampValue, MapEntry, PresentValue, SequenceValue, TextValue,
    validate_local_timestamp_text,
)
from truss._import_runtime import _cell
from truss._record_schema import _wire_cell


class LocalTimestampValueTests(unittest.TestCase):
    def test_exact_canonical_text_and_immutable_distinct_kind(self):
        for token in (
            '0001-01-01T00:00:00.000000',
            '9999-12-31T23:59:59.999999',
            '2000-02-29T12:30:45.123456',
            '2024-11-03T01:30:00.000001',
        ):
            with self.subTest(token=token):
                value = LocalTimestampValue(text=token)
                self.assertIs(truss.LocalTimestampValue, LocalTimestampValue)
                self.assertIs(value.text, token)
                self.assertIs(validate_local_timestamp_text(token), token)
                self.assertEqual(asdict(value), {'text': token, 'kind': 'localTimestamp'})
                with self.assertRaises(FrozenInstanceError):
                    value.text = 'changed'

    def test_calendar_clock_precision_and_shape_refusals(self):
        for token in (
            '0000-01-01T00:00:00.000000', '1900-02-29T12:00:00.000000',
            '2024-02-30T12:00:00.000000', '2024-13-01T00:00:00.000000',
            '2024-01-01T24:00:00.000000', '2024-01-01T12:60:00.000000',
            '2024-01-01T12:00:60.000000', '2024-01-01T00:00:00',
            '2024-01-01T00:00:00.1', '2024-01-01T00:00:00.1234567',
            '2024-01-01T00:00:00.123456Z', '2024-01-01T00:00:00.123456+00:00',
            '2024-01-01t00:00:00.123456', '２０２４-01-01T00:00:00.123456',
            '2024-01-01T00:00:00.123456\n', b'2024-01-01T00:00:00.123456',
            None, 0,
        ):
            with self.subTest(token=token), self.assertRaises(ValueError):
                LocalTimestampValue(text=token)
        with self.assertRaises(TypeError):
            LocalTimestampValue(text='2024-01-01T00:00:00.000000', kind='timestamp')

    def test_existing_exact_value_and_import_profiles_still_refuse_local(self):
        value = LocalTimestampValue(text='2024-03-10T01:30:00.123456')
        self.assertIsNone(_wire_cell(value))
        for construct in (
            lambda: PresentValue(value=value),
            lambda: SequenceValue(items=(value,)),
            lambda: MapEntry(key='local', value=value),
            lambda: TextValue(kind='localTimestamp', text=value.text),
            lambda: _cell(asdict(value)),
            lambda: _cell({'kind': 'sequence', 'items': [asdict(value)]}, containers=True),
        ):
            with self.subTest(construct=construct), self.assertRaises(ValueError):
                construct()

    def test_existing_timestamp_retains_original_precision_and_unknown_offset(self):
        token = '2024-01-01T00:00:00.123456789-00:00'
        value = TextValue(kind='timestamp', text=token)
        self.assertEqual(_cell(asdict(value)), value)
        self.assertEqual(value.text, token)
        with self.assertRaises(ValueError):
            LocalTimestampValue(text=token)


if __name__ == '__main__':
    unittest.main()
