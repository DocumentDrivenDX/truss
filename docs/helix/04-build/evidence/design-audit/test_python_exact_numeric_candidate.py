"""Independent fixture checks; no native or public-adapter qualification."""
import json
from decimal import localcontext
from pathlib import Path
import unittest

from python_exact_numeric_candidate import (
    decimal_from_admitted_text, integer_from_admitted_text, integral_host_value,
)


class ExactNumericCandidateTests(unittest.TestCase):
    def test_original_numeric_vectors(self):
        root = Path(__file__).resolve().parents[2]
        fixture = json.loads((root / "../03-test/python-exact-value-vectors.proposal.json").read_text())
        decoded = {}
        for vector in fixture["vectors"]:
            carrier = vector["wire"].get("value", {})
            if carrier.get("kind") not in ("integer", "decimal"):
                continue
            convert = integer_from_admitted_text if carrier["kind"] == "integer" else decimal_from_admitted_text
            with localcontext() as context:
                context.prec = 3
                decoded[vector["id"]] = convert(carrier["text"], 256)
            result = decoded[vector["id"]]
            expected = vector["expected"]
            self.assertEqual(result.original_text, expected.get("exactIntegerText", expected.get("originalDecimalText")))
            if "signedZero" in expected:
                self.assertEqual(result.value.is_signed(), expected["signedZero"])
            if vector["id"] == "decimal-large":
                self.assertEqual(str(result.value), expected["originalDecimalText"])
        self.assertEqual(len(decoded), 7)
        self.assertNotEqual(decoded["integer-even"].value, decoded["integer-odd"].value)
        for vector in fixture["vectors"]:
            if vector["id"] not in decoded:
                continue
            expected = vector["expected"]
            if "mathematicallyEqualTo" in expected:
                self.assertEqual(decoded[vector["id"]].value, decoded[expected["mathematicallyEqualTo"]].value)
            if "wireDistinctFrom" in expected:
                self.assertNotEqual(decoded[vector["id"]].original_text, decoded[expected["wireDistinctFrom"]].original_text)

    def test_refusals_and_explicit_bounds(self):
        for value in (True, False, 1.0, "1"):
            with self.assertRaises(ValueError):
                integral_host_value(value)
        self.assertEqual(integral_host_value(9007199254740993), 9007199254740993)
        for token in ("NaN", "sNaN", "Infinity", "-Infinity"):
            with self.assertRaises(ValueError):
                decimal_from_admitted_text(token, 32)
        for convert in (integer_from_admitted_text, decimal_from_admitted_text):
            for token, bound in (("123", 2), ("1", 0), ("1", True), (1, 32), ("\ud800", 32)):
                with self.assertRaises(ValueError):
                    convert(token, bound)
            self.assertEqual(convert("123", 3).original_text, "123")


if __name__ == "__main__":
    unittest.main()
