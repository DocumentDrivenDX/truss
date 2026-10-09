"""Original independent raw-JSON vector expectations; no native qualification."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from python_raw_json_candidate import JsonNumberToken, JsonObject, parse_retained_json


def parse(source, **limits):
    return parse_retained_json(source, **({"maximum_bytes": 1024, "maximum_depth": 16,
                                          "maximum_nodes": 100} | limits))


def collect(value, pointer=""):
    numbers, strings = {}, {}
    if type(value) is JsonNumberToken:
        numbers[pointer] = value.text
    elif type(value) is str:
        strings[pointer] = value
    elif type(value) is JsonObject:
        for key, child in value.entries:
            n, s = collect(child, pointer + "/" + key.replace("~", "~0").replace("/", "~1"))
            numbers.update(n)
            strings.update(s)
    elif type(value) is tuple:
        for index, child in enumerate(value):
            n, s = collect(child, pointer + "/" + str(index))
            numbers.update(n)
            strings.update(s)
    return numbers, strings


class RawJsonCandidateTests(unittest.TestCase):
    def test_preflight_refuses_before_decoder_allocation(self):
        for source, limits in ((b'[[null]]', {"maximum_depth": 1}),
                               (b'{"a":null,"b":null}', {"maximum_nodes": 2}),
                               (b'["string",false,1.00]', {"maximum_nodes": 3}),
                               (b'null', {"maximum_bytes": 3})):
            with patch("python_raw_json_candidate.json.loads") as decoder:
                with self.assertRaises(ValueError):
                    parse(source, **limits)
                decoder.assert_not_called()
        self.assertEqual(len(parse(b'["string",false,1.00]', maximum_nodes=4).value), 3)
        self.assertEqual(len(parse(b'{"a":null,"b":null}', maximum_nodes=3).value.entries), 2)

    def test_all_original_vector_bytes_and_token_inventories(self):
        root = Path(__file__).resolve().parents[2]
        fixture = json.loads((root / "../03-test/python-raw-json-vectors.proposal.json").read_text())
        for vector in fixture["vectors"]:
            source = vector["sourceUtf8Text"].encode("utf-8")
            result = parse(source)
            self.assertEqual(result.source_bytes, source)
            numbers, strings = collect(result.value)
            self.assertEqual(numbers, {v["pointer"]: v["token"] for v in vector["expectedNumericTokens"]})
            self.assertEqual(strings, {v["pointer"]: v["text"] for v in vector["expectedStrings"]})
            if vector["id"] == "json-null-empty-string-and-sequence":
                members = dict(result.value.entries)
                self.assertNotIn("missing", members)
                self.assertIsNone(members["null"])
                self.assertEqual(members["sequence"], ())

    def test_original_copy_and_depth_scanner_string_escapes(self):
        source = bytearray(b'{"s":"[\\\"{", "n":9007199254740993}')
        result = parse(source, maximum_depth=1)
        source[0] = 32
        self.assertEqual(result.source_bytes[0], ord("{"))
        self.assertEqual(dict(result.value.entries)["n"].text, "9007199254740993")

    def test_parser_and_selected_bound_refusals(self):
        for source in (b'{"n":NaN}', b'{"n":Infinity}', b'{"n":-Infinity}',
                       b'{"n":1,"n":2}', b'{"nested":{"n":1,"n":2}}',
                       b'"\\ud800"', b'"\\u0000"', b'"\xff"'):
            with self.assertRaises(ValueError):
                parse(source)
        for source, limits in ((b'[[null]]', {"maximum_depth": 1}),
                               (b'[null,null]', {"maximum_nodes": 2}),
                               (b'null', {"maximum_bytes": 3})):
            with self.assertRaises(ValueError):
                parse(source, **limits)
        self.assertIsNone(parse(b'null', maximum_bytes=4, maximum_nodes=1).value)


if __name__ == "__main__":
    unittest.main()
