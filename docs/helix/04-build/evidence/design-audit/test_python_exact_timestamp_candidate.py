"""Independent timestamp fixtures; no source grammar/native qualification."""
import json
from pathlib import Path
import unittest

from python_exact_timestamp_candidate import timestamp_from_admitted_text


class ExactTimestampCandidateTests(unittest.TestCase):
    def test_original_timestamp_vectors(self):
        root = Path(__file__).resolve().parents[2]
        fixture = json.loads((root / "../03-test/python-exact-value-vectors.proposal.json").read_text())
        decoded = {}
        for vector in fixture["vectors"]:
            carrier = vector["wire"].get("value", {})
            if carrier.get("kind") != "timestamp":
                continue
            result = timestamp_from_admitted_text(carrier["text"], 64)
            decoded[vector["id"]] = result
            self.assertEqual(result.original_text, vector["expected"]["originalTimestampText"])
        self.assertEqual(len(decoded), 3)
        self.assertIsNone(decoded["timestamp-nanoseconds"].datetime_view)
        self.assertEqual(decoded["timestamp-offset"].datetime_view, decoded["timestamp-utc"].datetime_view)
        self.assertNotEqual(decoded["timestamp-offset"].original_text, decoded["timestamp-utc"].original_text)
        self.assertEqual(decoded["timestamp-offset"].datetime_view.microsecond, 123456)
        self.assertEqual(decoded["timestamp-offset"].datetime_view.utcoffset().total_seconds(), -14400)

    def test_offset_components_cannot_be_normalized_by_python(self):
        for offset in ('+00:60', '-01:99', '+24:00', '-24:00', '+99:99'):
            token = '2026-10-09T12:34:56' + offset
            result = timestamp_from_admitted_text(token, 64)
            self.assertEqual(result.original_text, token)
            self.assertIsNone(result.datetime_view)
        for offset, seconds in (('+23:59', 86340), ('-23:59', -86340),
                                ('+00:59', 3540), ('-01:59', -7140)):
            token = '2026-10-09T12:34:56' + offset
            result = timestamp_from_admitted_text(token, 64)
            self.assertEqual(result.original_text, token)
            self.assertEqual(result.datetime_view.utcoffset().total_seconds(), seconds)

    def test_lossless_precision_and_unavailable_views(self):
        token = "2026-10-09T12:34:56.123456000Z"
        result = timestamp_from_admitted_text(token, len(token))
        self.assertEqual(result.original_text, token)
        self.assertEqual(result.datetime_view.microsecond, 123456)
        for token in (
            "2026-10-09T12:34:56.123456001Z",
            "2026-10-09T12:34:56-00:00",
            "2016-12-31T23:59:60Z",
            "2026-10-09T12:34:56",
            "2026-02-30T12:34:56Z",
        ):
            result = timestamp_from_admitted_text(token, 64)
            self.assertEqual(result.original_text, token)
            self.assertIsNone(result.datetime_view)
        with self.assertRaises(ValueError):
            timestamp_from_admitted_text("2026-10-09T12:34:56Z", 18)


if __name__ == "__main__":
    unittest.main()
