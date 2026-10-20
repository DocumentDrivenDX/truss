# SPDX-License-Identifier: MIT OR Apache-2.0
"""Archive verification controls for the release-time Weft wheel pin."""
import csv
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "verify-weft-release-wheel.py"
SPEC = importlib.util.spec_from_file_location("verify_weft_release_wheel", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class VerifyWeftReleaseWheelTests(unittest.TestCase):
    native_name = "weft/weft.abi3.so"
    record_name = "weft_sql-0.4.48.dist-info/RECORD"

    def _zip(self, path: Path, members: dict[str, bytes]) -> None:
        payloads = dict(members)
        rows = []
        for name, data in sorted(payloads.items()):
            digest = VERIFY._record_digest("sha256", data)
            rows.append((name, f"sha256={digest}", str(len(data))))
        rows.append((self.record_name, "", ""))
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerows(rows)
        payloads[self.record_name] = output.getvalue().encode()
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(payloads.items()):
                archive.writestr(name, data)

    def _registry(self, path: Path, wheel: Path, native: bytes) -> Path:
        source = path / "_current_query_originals.py"
        source.write_text(
            "_CONSUMER_COHORTS = ({"
            f"'weftWheelSha256': '{hashlib.sha256(wheel.read_bytes()).hexdigest()}', "
            f"'weftModuleSha256': '{hashlib.sha256(native).hexdigest()}'"
            "},)\n",
            encoding="utf-8",
        )
        return source

    def _members(self, native: bytes) -> dict[str, bytes]:
        return {
            "weft/__init__.py": b"from .weft import version\n",
            self.native_name: native,
            "weft_sql-0.4.48.dist-info/METADATA": b"Metadata-Version: 2.1\nName: weft-sql\nVersion: 0.4.48\n",
            "weft_sql-0.4.48.dist-info/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: false\nTag: py3-none-any\n",
        }

    def test_exact_frozen_archive_and_record_verify(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "weft_sql-0.4.48-py3-none-any.whl"
            native = b"synthetic native module"
            self._zip(wheel, self._members(native))
            source = self._registry(root, wheel, native)
            result = VERIFY.verify_wheel(wheel, source)
            self.assertEqual(result["status"], "verified")
            self.assertEqual(result["nativeModule"], self.native_name)
            self.assertEqual(result["record"], self.record_name)

    def test_repacked_wheel_with_same_native_module_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "weft.whl"
            native = b"synthetic native module"
            members = self._members(native)
            self._zip(wheel, members)
            source = self._registry(root, wheel, native)
            # Repacking valid identical members changes ZIP bytes while keeping
            # the exact native module hash and valid RECORD contents.
            self._zip(wheel, {**members, "weft/extra.py": b"extra\n"})
            with self.assertRaisesRegex(ValueError, "archive SHA-256"):
                VERIFY.verify_wheel(wheel, source)

    def test_unknown_native_module_digest_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "weft.whl"
            native = b"different synthetic native module"
            self._zip(wheel, self._members(native))
            source = self._registry(root, wheel, b"frozen other native module")
            with self.assertRaisesRegex(ValueError, "does not select one frozen"):
                VERIFY.verify_wheel(wheel, source)

    def test_cohort_pin_cannot_be_overridden_by_later_dictionary_unpack(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "_current_query_originals.py"
            source.write_text(
                "_CONSUMER_COHORTS = ({"
                f"'weftWheelSha256': '{'0' * 64}', "
                f"'weftModuleSha256': '{'1' * 64}', **later_pins"
                "},)\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unpack cannot follow explicit"):
                VERIFY._cohorts(source)

    def test_tampered_record_payload_is_rejected_even_with_matching_archive_pin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "weft.whl"
            native = b"synthetic native module"
            members = self._members(native)
            self._zip(wheel, members)
            with zipfile.ZipFile(wheel) as archive:
                tampered = {name: archive.read(name) for name in archive.namelist()}
            tampered["weft/__init__.py"] += b"# changed\n"
            with zipfile.ZipFile(wheel, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for name, data in sorted(tampered.items()):
                    archive.writestr(name, data)
            source = self._registry(root, wheel, native)
            with self.assertRaisesRegex(ValueError, "RECORD hash mismatch"):
                VERIFY.verify_wheel(wheel, source)


if __name__ == "__main__":
    unittest.main()
