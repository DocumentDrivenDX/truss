# SPDX-License-Identifier: MIT OR Apache-2.0
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from released_runtime_validation import (
    declared_test_inventory,
    parse_sha256sums,
    validate_verbose_unittest_result,
    verify_asset_checksum,
)


class ReleasedRuntimeValidationTests(unittest.TestCase):
    def test_two_asset_manifests_require_unique_exact_digests(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            runtime = root / "runtime.whl"
            truss = root / "truss.whl"
            runtime.write_bytes(b"runtime")
            truss.write_bytes(b"truss")
            runtime_digest = hashlib.sha256(b"runtime").hexdigest()
            truss_digest = hashlib.sha256(b"truss").hexdigest()
            runtime_manifest = parse_sha256sums(f"{runtime_digest}  runtime.whl\n")
            truss_manifest = parse_sha256sums(f"{truss_digest}  truss.whl\n")
            self.assertEqual(verify_asset_checksum(runtime, runtime_manifest, label="runtime"), runtime_digest)
            self.assertEqual(verify_asset_checksum(truss, truss_manifest, label="truss"), truss_digest)

            with self.assertRaisesRegex(ValueError, "no checksum entry"):
                verify_asset_checksum(truss, runtime_manifest, label="Truss")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                verify_asset_checksum(truss, {"truss.whl": runtime_digest}, label="Truss")
            with self.assertRaisesRegex(ValueError, "duplicate filename"):
                parse_sha256sums(f"{truss_digest}  truss.whl\n{truss_digest}  truss.whl\n")
            with self.assertRaisesRegex(ValueError, "basename-only"):
                parse_sha256sums(f"{truss_digest}  ../truss.whl\n")

    def test_ast_inventory_tracks_source_declarations_and_digest(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "driver_tests.py"
            source.write_text(
                "class PsycopgHostNativeTests:\n"
                "    def test_alpha(self): pass\n"
                "    async def test_beta(self): pass\n"
                "    def helper(self): pass\n"
            )
            inventory = declared_test_inventory(source, "PsycopgHostNativeTests")
            self.assertEqual(inventory["names"], ["test_alpha", "test_beta"])
            self.assertEqual(inventory["count"], 2)
            self.assertEqual(inventory["sourceSha256"], hashlib.sha256(source.read_bytes()).hexdigest())

    def _valid_output(self, names):
        lines = [
            f"{name} (test_psycopg_host_native.PsycopgHostNativeTests.{name}) ... ok"
            for name in names
        ]
        lines.extend([f"Ran {len(names)} tests in 0.001s", "", "OK"])
        return "\n".join(lines)

    def _validate(self, output, *, names=("test_alpha", "test_beta"), returncode=0):
        return validate_verbose_unittest_result(
            output,
            returncode=returncode,
            expected_module="test_psycopg_host_native",
            expected_class="PsycopgHostNativeTests",
            expected_names=list(names),
            source_sha256="a" * 64,
        )

    def test_exact_named_suite_passes_and_is_receipted(self):
        output = self._valid_output(["test_beta", "test_alpha"])
        evidence = self._validate(output)
        self.assertEqual(evidence["declaredCount"], 2)
        self.assertEqual(evidence["executedNames"], ["test_beta", "test_alpha"])
        self.assertEqual(evidence["skippedCount"], 0)
        self.assertEqual(evidence["sourceSha256"], "a" * 64)

    def test_missing_extra_duplicate_skipped_and_failed_tests_refuse(self):
        valid = self._valid_output(["test_alpha", "test_beta"])
        for output in (
            self._valid_output(["test_alpha"]),
            self._valid_output(["test_alpha", "test_beta", "test_extra"]),
            valid.replace("Ran 2 tests", "Ran 1 tests"),
            valid.replace("test_beta (test_psycopg_host_native.PsycopgHostNativeTests.test_beta) ... ok", "test_beta (test_psycopg_host_native.PsycopgHostNativeTests.test_beta) ... skipped 'disabled'"),
            valid.replace("test_beta (test_psycopg_host_native.PsycopgHostNativeTests.test_beta) ... ok\n", ""),
        ):
            with self.subTest(output=output), self.assertRaises(ValueError):
                self._validate(output)
        duplicate = valid.replace(
            "Ran 2 tests in 0.001s",
            "test_alpha (test_psycopg_host_native.PsycopgHostNativeTests.test_alpha) ... ok\nRan 3 tests in 0.001s",
        )
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self._validate(duplicate)
        with self.assertRaisesRegex(ValueError, "exit zero"):
            self._validate(valid, returncode=1)

    def test_wrong_module_and_missing_success_footer_refuse(self):
        wrong_module = self._valid_output(["test_alpha", "test_beta"]).replace(
            "test_psycopg_host_native", "other_module"
        )
        with self.assertRaisesRegex(ValueError, "Unexpected test module"):
            self._validate(wrong_module)
        without_footer = self._valid_output(["test_alpha", "test_beta"]).removesuffix("\nOK")
        with self.assertRaisesRegex(ValueError, "unittest OK"):
            self._validate(without_footer)


if __name__ == "__main__":
    unittest.main()
