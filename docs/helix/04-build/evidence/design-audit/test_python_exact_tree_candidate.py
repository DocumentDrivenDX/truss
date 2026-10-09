"""Independent tree/projection controls, not native or whole-parser evidence."""
import json
from hashlib import sha256
from pathlib import Path
import unittest

from python_exact_tree_candidate import TreeBounds, project_admitted_presence


BOUNDS = TreeBounds(depth=16, nodes=100, entries=10, text_bytes=256)


class ExactTreeCandidateTests(unittest.TestCase):
    def test_remaining_carriers_and_non_normalized_keys(self):
        source = 'unknown Unicode source\né'
        opaque = {"kind": "opaque", "format": "retained-original", "sourceText": source,
                  "sha256": sha256(source.encode("utf-8")).hexdigest()}
        values = [{"kind": "boolean", "value": False}, {"kind": "binary", "text": "AA=="}, opaque,
                  {"kind": "map", "entries": [
                      {"key": "é", "value": {"kind": "null"}},
                      {"key": "e\u0301", "value": {"kind": "null"}}]}]
        result = project_admitted_presence({"present": True, "value": {"kind": "sequence", "items": values}}, BOUNDS)
        self.assertIs(result.value.payload[0].payload, False)
        self.assertEqual(result.value.payload[1].payload, "AA==")
        self.assertEqual(result.value.payload[2].payload[1], source)
        self.assertEqual(tuple(key for key, _ in result.value.payload[3].payload), ("é", "e\u0301"))

    def test_all_original_vectors_and_nested_families(self):
        root = Path(__file__).resolve().parents[2]
        vectors = json.loads((root / "../03-test/python-exact-value-vectors.proposal.json").read_text())["vectors"]
        results = {v["id"]: project_admitted_presence(v["wire"], BOUNDS) for v in vectors}
        self.assertEqual(len(results), 15)
        self.assertFalse(results["absent"].present)
        self.assertTrue(results["explicit-null"].present)
        self.assertEqual(results["explicit-null"].value.kind, "null")
        self.assertEqual(results["empty-sequence"].value.payload, ())
        self.assertEqual(results["empty-string"].value.payload, "")
        token, literal = results["nested-token-and-string"].value.payload
        self.assertEqual(token[1].kind, "decimal")
        self.assertEqual(token[1].payload.original_text, "1.00")
        self.assertEqual(literal[1].kind, "string")
        self.assertEqual(literal[1].payload, "1.00")

    def test_copied_ordered_record_and_exact_identities(self):
        fields = [{"fieldId": "9007199254740993", "value": {"kind": "string", "text": "a"}},
                  {"fieldId": "9007199254740992", "value": {"kind": "null"}}]
        carrier = {"present": True, "value": {"kind": "record", "definitionPin": "original", "fields": fields}}
        result = project_admitted_presence(carrier, BOUNDS)
        fields[0]["value"]["text"] = "changed"
        self.assertEqual(result.value.payload[1][0][0], "9007199254740993")
        self.assertEqual(result.value.payload[1][0][1].payload, "a")
        fields[1]["fieldId"] = fields[0]["fieldId"]
        with self.assertRaises(ValueError):
            project_admitted_presence(carrier, BOUNDS)

    def test_refusals(self):
        invalid = [
            {"present": False, "value": {"kind": "null"}},
            {"present": 1, "value": {"kind": "null"}},
            {"present": True, "value": {"kind": "boolean", "value": 1}},
            {"present": True, "value": {"kind": "string", "text": "\x00"}},
            {"present": True, "value": {"kind": "string", "text": "\ud800"}},
            {"present": True, "value": {"kind": "map", "entries": [
                {"key": "same", "value": {"kind": "null"}},
                {"key": "same", "value": {"kind": "null"}}]}},
            {"present": True, "value": {"kind": "opaque", "format": "x", "sourceText": "original", "sha256": "0" * 64}},
        ]
        for carrier in invalid:
            with self.assertRaises(ValueError):
                project_admitted_presence(carrier, BOUNDS)
        two = {"present": True, "value": {"kind": "sequence", "items": [{"kind": "null"}, {"kind": "null"}]}}
        for bounds in (TreeBounds(1, 100, 10, 256), TreeBounds(16, 2, 10, 256), TreeBounds(16, 100, 1, 256)):
            with self.assertRaises(ValueError):
                project_admitted_presence(two, bounds)


if __name__ == "__main__":
    unittest.main()
